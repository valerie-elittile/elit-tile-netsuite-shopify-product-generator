import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et
import json
import unicodedata
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)

NATURAL_STONE = {
    'MARBLE', 'QUARTZITE', 'LIMESTONE', 'SLATE', 'TRAVERTINE', 'GRANITE', 'SANDSTONE', 'BASALT'
}

SESSION_SKIPS = {
    'colors': [],
    'finishes': [],
    'materials': [],
    'residential_applications': [],
    #'styles': [],
    'mosaic_shapes': [],
    'piece_type': [],
    'looks': []
}

Pack_Info_Mapping = et.get_pack_info_mapping()
TAXONOMY_BY_ID = {}

# Define the order of options
options = ['SIZE', 'COLOR', 'FINISH']


# ============================================================================
# UTILITY FUNCTIONS - Basic text and data manipulation
# ============================================================================

def remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def drop_special_chars(input_str: str) -> str:
    out_str = re.sub(r'[^\-\w\s]', '', input_str)
    return out_str

def replace_dashes(s: str) -> str:
    while "  " in s:
        s = s.replace("  ", " ")
    s = s.strip()
    return s.replace(" ", "-")

def clean_handle(handle: str) -> str:
    handle = remove_accents(handle)
    handle = drop_special_chars(handle)
    handle = handle.replace(".", "-")
    handle = handle.replace("/", "-")
    while "  " in handle:
        handle = handle.replace("  ", " ")
    return handle

def get_decimal(term):
    # Remove any whitespace
    term = re.sub(r'\s', '', term)

    # Extract and separate the fractional parts from the base
    if '/' in term and '-' in term:
        fractions = re.findall(r'(\d+-\d+/\d+)', term)
        base, frac = fractions[0].split('-')
    elif '/' in term:
            fractions = re.findall(r'(\d+/\d+)', term)
            frac = fractions[0]
            base = 0
    else:
        try:
            base = float(term)
        except ValueError as e:
            base = 0
        frac = '0'
    
    # Convert the fractional part to decimal before adding it back to the base
    if '/' in frac:
        numerator, denominator = frac.split('/')
        decimal_component = float(numerator) / float(denominator)
        full_dec_term = float(base) + decimal_component
    else:
        try:
            full_dec_term = float(base)
        except ValueError as e:
            full_dec_term = 0

    return full_dec_term

def stringify_dict(d_in):
    out_list = list()
    if d_in['width']:
        out_list.append(str(d_in['width']))
    if d_in['length']:
        out_list.append(str(d_in['length']))
    if d_in['height']:
        out_list.append(str(d_in['height']))

    out_str = ("X").join(out_list)
    return out_str

def round_to_full(n):
    r = round(n)
    return r


# ============================================================================
# SIZE/DIMENSION HELPER FUNCTIONS
# ============================================================================

def dimensionate(size: str) -> dict:
    out = {
        'width': '',
        'length': '',
        'height': ''
    }
    try:
        if not 'x' in size.lower():
            return out
    except AttributeError as e:
        print(e)
        print(f"Size value: {size}")
        return out
    
    temp_terms = re.split(r'x|X', size)
    if len(temp_terms) < 1 or len(temp_terms) > 3:
        return out
    elif len(temp_terms) == 1:
        out['width'] = temp_terms[0]
    elif len(temp_terms) == 2:
        out['width'] = temp_terms[0]
        out['length'] = temp_terms[1]
    elif len(temp_terms) == 3:
        out['width'] = temp_terms[0]
        out['length'] = temp_terms[1]
        out['height'] = temp_terms[2]
    
    return out

def decimalize(dims: dict) -> dict:
    out = {
        'width': None,
        'length': None,
        'height': None
    }

    if dims['width']:
        out['width'] = get_decimal(dims['width'])
    if dims['length']:
        out['length'] = get_decimal(dims['length'])
    if dims['height']:
        out['height'] = get_decimal(dims['height'])
    
    return out

def sort_dims(d_in) -> dict:
    l = list(d_in.values())

    out = {
        'width': None,
        'length': None,
        'height': None
    }

    while None in l:
        l.remove(None)

    if len(l) == 1:
        out['width'] = l[0]
    elif len(l) == 2:
        out['length'] = max(l)
        l.remove(out['length'])
        out['width'] = l[0]
    elif len(l) == 3:
        out['length'] = max(l)
        l.remove(out['length'])
        out['width'] = max(l)
        l.remove(out['width'])
        out['height'] = l[0]
    else:
        print(f"The length of list to be sorted is unsupported: {len(l)}")
    
    return out

def get_full_round(s_d: dict) -> dict:
    if pd.notna(s_d['width']) :
        out_w = round_to_full(s_d['width'])
    else:
        out_w = ''
    if pd.notna(s_d['length']) :
        out_l = round_to_full(s_d['length'])
    else:
        out_l = ''
    if pd.notna(s_d['height']) :
        out_h = round_to_full(s_d['height'])
    else:
        out_h = ''
    
    return {
        'width': out_w,
        'length': out_l,
        'height': out_h
    }


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_term_dict(file_path='term_dict.json'):
    if not os.path.dirname(file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, file_path)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Term dictionary file not found at: {file_path}")


def add_synonym_to_filter_dictionary(category: str, term_key: str, new_synonym: list, file_path='term_dict.json'):
    """
    Adds a new term or synonyms to the desired category in the filter dictionary in the JSON file.

    Parameters:
        category (str): The category of the term to be added
        term_key (str): The main term in the category(e.g., 'BLUE')
        new_synonym (list): A list of synonyms to be added for the given term.
        file_path (str): Path to the JSON file storing the term dictionary.
    """

    # Load the term dictionary from JSON
    term_dict = load_term_dict()

    # Ensure 'colors' category exists
    if category not in term_dict:
        raise ValueError(f"Unable to locate {category} in JSON dictionary")
    
    # Add or update the color term
    if term_key in term_dict[category]:
        # Update the existing key with new synonyms (avoid duplicates)
        existing_synonyms = term_dict[category][term_key]
        updated_synonyms = list(set(existing_synonyms + [str(new_synonym).upper()]))
        term_dict[category][term_key] = updated_synonyms
    else:
        # Add a new key with synonyms
        term_dict[category][term_key] = updated_synonyms

    # Save the updated term dictionary back to the JSON file   
    if not os.path.dirname(file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, file_path)
  
    with open(file_path, 'w') as file:
        json.dump(term_dict, file, indent=4)

    print(f"Successfully updated '{term_key}' in the '{category}' dictionary.")
    return load_term_dict()


# ============================================================================
# USER INPUT/INTERACTION FUNCTIONS
# ============================================================================

def get_warning_choice() -> int:
    # Asks the user if they want to handle warnings or suppress them
    print("\nDo you want to handle warnings or suppress them?")
    print("(1) - I will handle warnings")
    print("(2) - Please suppress all warnings")
    warning_choice = input("... ")
    # Validate user input
    try:
        warning_choice = int(warning_choice)
        if warning_choice not in [1,2]:
            raise Exception("Invalid warning choice")
    except Exception as e:
        print("You did not enter a valid choice")
        print(f"{e}")
        print("Program exiting...")
        exit()

    if warning_choice == 2:
        warning_choice = 0
    return warning_choice

def get_vendors_to_process(df: pd.DataFrame, vendor_mapping: dict) -> list:
    active_vendors = vendor_mapping
    found_vendors = sorted(df["VENDOR"].dropna().unique())
    valid_vendors = [vc for vc in found_vendors if vc in active_vendors]

    print("\nDo you want to process:")
    print("(1) - All Vendors")
    print("(2) - One Vendor")
    user_choice = input("... ")

    try:
        user_choice = int(user_choice)
        if user_choice not in [1, 2]:
            raise ValueError("Invalid choice")
    except Exception as e:
        print("Invalid input. Must be 1 or 2.")
        print(f"{e}")
        print("Program exiting...")
        exit()

    if user_choice == 1:
        print("Processing all vendors:")
        for vc in valid_vendors:
            print(f"{vc} – {active_vendors.get(vc, 'Unknown')}")
        return valid_vendors

    elif user_choice == 2:
        print("Choose a vendor to process:")
        for vc in valid_vendors:
            print(f"{vc} – {active_vendors.get(vc, 'Unknown')}")
        vc_chosen = input("Enter vendor code: ").strip().upper()
        if vc_chosen not in valid_vendors:
            print(f"Vendor '{vc_chosen}' not found in merged file or not active.")
            print("Program exiting...")
            exit()
        return [vc_chosen]


# ============================================================================
# CLASSIFICATION AND FILTER FUNCTIONS
# ============================================================================

def get_classification(r: pd.Series, column: str) -> str:
    if "CLASSIFICATION ID" not in r or pd.isna(r["CLASSIFICATION ID"]):
        return ''
    try:
        _id = int(r["CLASSIFICATION ID"])
    except:
        return ''
    return str(TAXONOMY_BY_ID.get(_id, {}).get(column, '')).strip().title()

def get_type_filter(r: pd.Series) -> str:
    cls = get_classification(r, "CLASS").upper()
    typ = get_classification(r, "TYPE").upper()

    if not cls:
        return ''

    if cls == "TILE" and typ and typ != cls:
        result = f"{cls},{typ}".title()
    else:
        result = cls.title()
    
    # Only return if it's 'Slab' or 'Prefab'
    if result in ['Slab', 'Prefab']:
        return result
    return ''

def get_type_filter_v2(r: pd.Series) -> str:
    cls = get_classification(r, "CLASS").upper()
    typ = get_classification(r, "TYPE").upper()

    if not cls:
        return ''

    if cls == "TILE" and typ and typ != cls:
        return f"{cls},{typ}".title()

    return cls.title()

def resolve_filter(r: pd.Series, column: str, dict_key: str, skip_lists: dict, warning_choice: int, active_only: bool = False):
    if dict_key != 'mosaic_shapes':
        if pd.isna(r[column]):
            return None

    filter_dict = load_term_dict()
    if dict_key not in filter_dict:
        print(f"WARNING: '{dict_key}' not found in term_dict.json")
        return None
    if dict_key == 'mosaic_shapes':
        terms = [t.strip() for t in str(column).split(",")]
    else:
        terms = [t.strip() for t in str(r[column]).split(",")]

    results = []

    for term in terms:
        found = False

        for key, synonym_list in filter_dict[dict_key].items():
            if term.lower() in [s.lower() for s in synonym_list]:
                results.append(key.title())
                found = True
                break

        if (
            not found
            and warning_choice
            and term.lower() not in [s.lower() for s in skip_lists[dict_key]]
            and (
                str(r["PRICELIST STATUS"]).upper() == "ACTIVE"
                if active_only else
                str(r["PRICELIST STATUS"]).upper() != "INACTIVE"
            )
        ):

            print(f"Unrecognized {dict_key.upper()} FILTER term: {term}")
            print(f"Do you want to add '{term}' as a synonym?")
            add_term_choice = input("(y/n)... ").lower()

            if add_term_choice == "y":
                print(f"Which {dict_key} is a synonym for {term}?")
                keys = list(filter_dict[dict_key].keys())

                for i, k in enumerate(keys, 1):
                    print(f"{i}. {k}")

                while True:
                    try:
                        user_input = input(
                            f"Enter the number corresponding to '{term}' (comma separated allowed): "
                        )

                        choices = [int(x.strip()) for x in user_input.split(",")]

                        if all(1 <= c <= len(keys) for c in choices):
                            break
                        else:
                            print("Invalid choice. Please enter numbers from the list.")

                    except ValueError:
                        print("Invalid input. Please enter a number or numbers separated by commas.")

                selected = [keys[c-1] for c in choices]

                for s in selected:
                    add_synonym_to_filter_dictionary(dict_key, s, term)
                    results.append(s.title())
                    print(f"Added the synonym {term} to the {dict_key} category {s}")

            else:
                skip_lists.setdefault(dict_key, [])
                skip_lists[dict_key].append(term)
                print("Correct the value on the MPL or add to term_dict.json")
                print(f"Product: {r.get('E SKU', '')} {r.get('SHOPIFY NAME', '')}")
                if dict_key != 'mosaic_shapes':
                    print(f"{column} field value: {r.get(column, '')}")
                else:
                    print(f"TYPE: {column}")
                print(f"PRICELIST STATUS: {r.get('PRICELIST STATUS', '')}")
                input("Press enter to continue...")

    results = list(set(results))
    return ",".join(results) if results else None

def get_material_filter(r: pd.Series, warning_choice: int, skip_lists: dict) -> str:
    """
    Returns valid terms to be used in the 'Material' filter in Shopify. Sources
    its data only from the 'MATERIAL' field in the MPL. Allows user to handle
    unrecognized terms by adding the term as a synonym of a material category or 
    skipping the term for the session.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
        warning_choice (bool): Whether to display warnings for unrecognized terms
        skip_lists (dict): JSON file loaded as dictionary containing synonyms and categories

    Returns:
        str:                A string containing valid terms separated by commas
    """
    return resolve_filter(r, 'MATERIAL', 'materials', skip_lists, warning_choice, active_only=True)

def get_finish_filter(r: pd.Series, warning_choice: int, skip_lists: dict) -> str:
    """
    Returns valid terms to be used in the 'Finish' filter in Shopify. Sources
    its data only from the 'FINISH' field in the MPL. Allows user to handle
    unrecognized terms by adding the term as a synonym of a finish category or 
    skipping the term for the session.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
        skip_lists (dict): JSON file loaded as dictionary containing synonyms and categories
    """
    return resolve_filter(r, 'FINISH', 'finishes', skip_lists, warning_choice, active_only=True)

def get_mosaic_shape_filter(warning_choice: int, r: pd.Series, skip_lists: dict) -> str:
    """
    Returns valid terms to be used in the 'Mosaic Shape' filter in Shopify.
    SOURCE: taxonomy output from get_classification() - specifically CLASS and TYPE.
    Only runs when CLASS is MOSAIC. TYPE is treated as the raw mosaic-shape term(s).
    """

    cls = get_classification(r, "CLASS")
    typ = get_classification(r, "TYPE")

    if not cls or cls.upper() != "MOSAIC":
        return None

    if not typ:
        return None
    
    manual_val = r.get('MOSAIC SHAPE (FILTER)', '')
    if pd.notna(manual_val) and str(manual_val).strip():
        raw = str(manual_val).strip()
        # Split by comma and normalize format for Shopify
        parts = [p.strip().title() for p in raw.split(",") if p.strip()]
        return ",".join(parts)
    
    return resolve_filter(r, typ, 'mosaic_shapes', skip_lists, warning_choice)

def get_size_filter(r: pd.Series) -> str:
    """
    Returns valid terms to be used in the 'Size' filter in Shopify. Sources
    its data only from the 'SIZE' field in the MPL. Allows user to handle
    unrecognized terms by adding the term as a synonym of a size category or
    skipping the term for the session.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
        skip_lists (dict): JSON file loaded as dictionary containing synonyms and categories
    """
    original_size = r['SIZE']
    matches = re.findall(r'\d+\.?\d*X\d+\.?\d*', str(original_size))

    if not matches:
        return original_size if pd.notna(original_size) else None
    else:
        dims = [tuple(map(float, m.split('X'))) for m in matches]
        max_size = max(dims, key=lambda x: x[0] * x[1])
        raw_size = f"{max_size[0]}X{max_size[1]}"

    price_list_class = r['pricelist.class']

    raw_dimensions = dimensionate(raw_size)

    decimalized_dimensions = decimalize(raw_dimensions)
    sorted_dimensions = sort_dims(decimalized_dimensions)   
    full_round = get_full_round(sorted_dimensions)

    if price_list_class != 'SAMPLE':
        if price_list_class == 'TRIM':
            full_round_str = 'Trim'
        else:
            full_round_str = stringify_dict(full_round)

    if full_round_str:
        return full_round_str
    
    return None


def get_size_display_filter(r: pd.Series) -> str:
    """
    Returns formatted size string for the 'filter.size' metafield in Shopify.
    Returns size as "width\" X length\"" format with only two dimensions.
    Examples: "6\" X 10\"", "2\" X 6\"", "4.3\" X 4.3\""

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
    
    Returns:
        str: Formatted size string with inch marks, or empty string if no valid size
    """
    original_size = r['SIZE']
    matches = re.findall(r'\d+\.?\d*X\d+\.?\d*', str(original_size))

    if not matches:
        return ''
    else:
        dims = [tuple(map(float, m.split('X'))) for m in matches]
        max_size = max(dims, key=lambda x: x[0] * x[1])
        raw_size = f"{max_size[0]}X{max_size[1]}"

    price_list_class = r['pricelist.class']

    # Handle SAMPLE and TRIM classes
    if price_list_class == 'SAMPLE':
        return ''
    elif price_list_class == 'TRIM':
        return 'Trim'

    raw_dimensions = dimensionate(raw_size)
    decimalized_dimensions = decimalize(raw_dimensions)
    sorted_dimensions = sort_dims(decimalized_dimensions)   
    full_round = get_full_round(sorted_dimensions)

    # Extract only width and length (no height)
    width = full_round['width']
    length = full_round['length']

    # Build the display string with inch marks
    size_parts = []
    if width:
        size_parts.append(f"{width}\"")
    if length:
        size_parts.append(f"{length}\"")

    if size_parts:
        return " X ".join(size_parts)
    
    return ''


def get_color_filter(r: pd.Series, warning_choice: int, skip_lists: dict) -> str:
    """
    Returns valid terms to be used in the 'Color' filter in Shopify. Sources
    its data only from the 'BASE COLOR' field in the MPL. Allows user to handle
    unrecognized terms by adding the term as a synonym of a color category or 
    skipping the term for the session.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
    """
    return resolve_filter(r, 'BASE COLOR', 'colors', skip_lists, warning_choice, active_only=True)

def get_application_filter(r: pd.Series, warning_choice: int, skip_lists: dict) -> str:
    """
    Returns valid terms to be used in the 'Primary Application' filter in Shopify. Sources
    its data only from the 'RESIDENTIAL APPLICATION' field in the MPL. Allows user to handle
    unrecognized terms by adding the term as a synonym of an application category or 
    skipping the term for the session.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
    """
    return resolve_filter(r, 'RESIDENTIAL APPLICATION', 'residential_applications', skip_lists, warning_choice, active_only=True)

def get_look_filter(r: pd.Series, warning_choice: int, skip_lists: dict) -> str:
    """
    Returns valid terms to be used in the 'Look' filter in Shopify. Sources
    its data only from the 'LOOK' field in the MPL. Allows user to handle
    unrecognized terms by adding the term as a synonym of a look category or 
    skipping the term for the session.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
    """
    return resolve_filter(r, 'LOOK', 'looks', skip_lists, warning_choice, active_only=True)

# ============================================================================
# NAMING AND HANDLE FUNCTIONS
# ============================================================================

def build_handle(r: pd.Series) -> str:
    handle = ""
    handle_terms = ['SERIES', 'COLOR', 'FINISH', 'pricelist.class', 'SIZE', 'E SKU']
    for t in handle_terms:
        if t in r and pd.notna(r[t]):
            handle = handle + " " + str(r[t])

    handle = handle.strip().lower()
    handle = clean_handle(handle)
    handle = replace_dashes(handle)

    return handle

def build_title_from_formula(r: pd.Series, formula: list) -> str:
    """
    Builds a product title from a formula (list of column names).
    If 'Title' is already populated in the row, returns that value.
    Otherwise, concatenates values from specified columns according to the formula.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data
        formula (list): A list of column names to use for building the title

    Returns:
        str: The generated title or existing title value
    """
    # If 'Title' is already populated, return this value
    if ('Title' in r) and (pd.notna(r['Title'])):
        return r['Title']

    title = ''
    for t in formula:
        if t in r and pd.notna(r[t]):
            term = str(r[t])

            if t == 'SWATCH CARD SIZE':
                while '"' in term:
                    term = term.replace('"', '')
                while ' ' in term:
                    term = term.replace(' ', '')

            # Attempt to handle up to 2 finishes
            if (t == 'FINISH') and (',' in term):
                while ' ' in term:
                    term = term.replace(' ', '')
                if len(term.split(',')) == 2:
                    term = term.replace(',', ' and ')
                else:
                    continue

            if term.lower() in title.lower():
                continue

            title = title + " " + str(term).title()
    
    return title.strip()

def get_proposed_new_title(r: pd.Series) -> str:
    """
    Generates a product title based on the pricelist class and title type.
    Uses predefined formulas for TILE, MOSAIC, and TRIM products.
    Supports two title type formats: 'A' and 'B'.

    Parameters:
        r (pandas.Series): A single row of the MPL containing product data

    Returns:
        str: The generated product title
    """
    if pd.isna(r.get('pricelist.class')):
        print(f"Cannot generate Product Title for {r.get('E SKU', 'Unknown')}")
        return ''

    # variables which determines which govern logic
    p_class = str(r['pricelist.class']).upper()

    
    if p_class == 'TILE':
        formula = ['SERIES', 'COLOR', 'SIZE', 'SPECIAL ATTRIBUTE', 'FINISH', 'MATERIAL']
    elif p_class == 'MOSAIC':
        formula = ['SERIES', 'COLOR', 'MOSAIC CHIP SIZE', 'MOSAIC CHIP SHAPE', 'SPECIAL ATTRIBUTE',
                    'FINISH', 'MATERIAL', 'pricelist.class']
    elif p_class == 'TRIM':
        formula = ['SERIES', 'COLOR', 'SIZE', 'SPECIAL ATTRIBUTE', 'FINISH', 'MATERIAL', 'PIECE TYPE']
    else:
        print(f"Error generating Product Title. TITLE TYPE 'A' but pricelist.class is unrecognized: {r['pricelist.class']}.")
        return ''
    
    title = build_title_from_formula(r, formula)

    if title:
        return title
    return ''


# ============================================================================
# STATUS AND METADATA FUNCTIONS
# ============================================================================

def get_status(row: pd.Series) -> str:
    status = 'Draft'

    ## If not active from vendor pricelist, reject; return error 001
    if (str(row['PRICELIST STATUS']).upper().strip()) == 'INACTIVE':
        return 'inactive-001'

    # If no cost data, reject; return error 002
    if ('COST/UOM' not in row) or pd.isna(row['COST/UOM']):
        return 'inactive-002' 

    ## If no sell unit data, reject; return error 003
    if ('SELL UNIT' not in row) or (pd.isna(row['SELL UNIT'])):
        return 'inactive-003'
    
    # If no weight data, reject; return error 004
    weight = get_weight(row)
    if weight is None or pd.isna(weight):
        return 'inactive-004'
    
    # If weight is 0, only allow if product is slab/prefab
    if weight == 0:
        type_filter = get_type_filter(row)
        if type_filter not in ['Slab', 'Prefab']:
            return 'inactive-005'
    
    return status

def get_weight(r: pd.Series) -> float:
    sell_unit = str(r.get('SELL UNIT', '')).strip().upper()
    if sell_unit == 'SF':
        return r.get('LBS/SF')
    if sell_unit in ['EA', 'SHT']:
        return r.get('LBS/EA')
    elif sell_unit in ['BX','SET']:
        return r.get('LBS/BX')
    elif sell_unit == 'PLT':
         return r.get('LBS/PLT')
    else:
        return None

def get_is_trim(r:pd.Series) -> str:
    if r['pricelist.class'] == "TRIM":
        return 'TRUE'
    return 'FALSE'

def get_inventory_tracked(vendor: str) -> str:
    """
    Returns whether a vendor's products should be inventory tracked.
    Checks the et.inventory_tracked_vendors dictionary.

    Parameters:
        vendor (str): The vendor code to check
    
    Returns:
        str: 'TRUE' if vendor is in inventory_tracked_vendors and set to TRUE, 'FALSE' otherwise
    """
    try:
        inventory_vendors = et.inventory_tracked_vendors
        if vendor in inventory_vendors and inventory_vendors[vendor]:
            return 'TRUE'
    except (AttributeError, KeyError, TypeError):
        pass
    
    return 'FALSE'

def get_options(r: pd.Series) -> dict:
    option_name_hierarchy = {'SIZE': 'Size', 'COLOR': 'Color', 'FINISH': 'Finish'}

    present = [
        (label, r[col])
        for col, label in option_name_hierarchy.items()
        if pd.notna(r[col])
    ]

    result = {}
    for i in range(1, 4):
        if i <= len(present):
            label, value = present[i - 1]
            result[f'Option {i} Name'] = label
            result[f'Option {i} Value'] = str(value).strip().title()
        else:
            result[f'Option {i} Name'] = ''
            result[f'Option {i} Value'] = ''

    return result

def get_product_description(r: pd.Series) -> str:
    if 'PRODUCT DESCRIPTION' not in r or pd.isna(r['PRODUCT DESCRIPTION']):
        return ''

    return f"<p>{str(r['PRODUCT DESCRIPTION']).strip()}</p>"

def get_launch_date(r: pd.Series) -> str:
    if not 'LAUNCH DATE' in r:
        return ''
    elif pd.isna(r['LAUNCH DATE']):
        return ''
    try:
        date_obj = datetime.datetime.strptime(str(r['LAUNCH DATE']), "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error to convert launch date for product {r.get('E SKU', '')} {r.get('SHOPIFY NAME', '')}): {r['LAUNCH DATE']}")
        print(e)
        return ''
    
    return date_obj.strftime("%Y-%m-%d")

def notate_rejections(df: pd.DataFrame) -> pd.DataFrame:
    ## Error code definitions
    error_codes = {
        "inactive-001": "Not active on current vendor pricelist",
        "inactive-002": "No COST/UOM data",
        "inactive-003": "No SELL UNIT data",
        "inactive-004": "No weight data",
        "inactive-005": "0 weight data"
    }
    ## Column to hold rejection note
    rejection_note_list = list()
    
    ## Iterate through the rejected products
    for index, row in df.iterrows():
        # If error code recognized, output the note text
        if row['Status'] in error_codes:
            rejection_note_list.append(error_codes[row['Status']])
        # If error code unrecognized, output generic message
        else:
            rejection_note_list.append("Unknown error code: " + str(row['Status']))
            
    df['REJECTION NOTES'] = rejection_note_list
    
    return df


# ============================================================================
# TAG AND SERIES FUNCTIONS
# ============================================================================

def custom_transform_series(series):
    if pd.isna(series) or series == '':
        return ''  # Return empty if SERIES is missing
    
    # Clean up extra spaces, remove unwanted characters, and convert to lowercase
    cleaned_series = re.sub(r'[^a-zA-Z0-9\s]', '', series.strip())  # Remove non-alphanumeric characters except spaces
    cleaned_series = re.sub(r'\s+', ' ', cleaned_series)  # Replace multiple spaces with a single space
    cleaned_series = cleaned_series.lower()  # Convert to lowercase
    return 'series-' + cleaned_series.replace(' ', '-')  # Replace spaces with single hyphen

def get_non_zero_numbers(vendor_id):
    # Use regular expression to find all numbers in the string
    numbers = re.findall(r'\d+', vendor_id)
    
    # Filter out numbers that are non-zero and remove leading zeros
    non_zero_numbers = [str(int(num)) for num in numbers if int(num) != 0]
    
    return non_zero_numbers

def create_series_handle(vendor_id, series_name):
    if pd.notna(series_name) and series_name:  # Check if series_name (Tags) is not NaN and not empty
        non_zero_numbers = get_non_zero_numbers(vendor_id)
        if non_zero_numbers:  # Check if there are valid non-zero numbers
            # Assuming you want the first non-zero number if there are multiple
            non_zero_number = non_zero_numbers[0]
            return f'{non_zero_number}-{series_name}'
    return ''  # Return an empty string if Tags is NaN or no valid non-zero number

def generate_additional_tags(row):
    tags = []

    # Add tags based on other columns
    columns_to_check = ['LOOK', 'MAIN APPLICATION', 'MATERIAL (FILTER)', 
                        'BASE COLOR (FILTER)', 'TYPE FILTERS', 'FINISH (FILTER)', 
                        'TILE SHAPE (FILTER)', 'MOSAIC SHAPE (FILTER)', 'TRIM TYPE (FILTER)',
                        'FORMAT (FILTER)', 'THICKNESS (FILTER)', 'OTHER (FILTER)']
    
    for col in columns_to_check:
        if col in row and pd.notna(row[col]):  # Check if the column exists and is not null
            value = str(row[col]).strip().lower()  # Convert value to lowercase and strip extra spaces
            if value != 'other':  # Ignore 'other' values
                tags.append(value)

    # Combine all tags into a single string, separated by commas
    raw_tags = ', '.join(tags)

    # Clean up multiple consecutive hyphens to a single hyphen
    cleaned_tags = re.sub(r'-{2,}', '-', raw_tags)  # Replace 2+ hyphens with 1
    return cleaned_tags

def generate_tags(row):
    tags_list = []

    # Transform SERIES column
    series_tag = custom_transform_series(row.get('SERIES', ''))
    if series_tag:
        tags_list.append(series_tag)

    # Create series handle
    series_handle = create_series_handle(row.get('Vendor_id', ''), series_tag)
    if series_handle:
        tags_list.append(series_handle)

    # Add additional tags (excluding SERIES to prevent duplication)
    additional_tags = generate_additional_tags(row)
    if additional_tags:
        tags_list.append(additional_tags)

    return ', '.join(tags_list) if tags_list else ''

def concatenate_with_html(row):
    def _pack_float(val):
        if val is None or pd.isna(val):
            return None
        if isinstance(val, str) and val.strip() == '':
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    values = []
    ea_bx = _pack_float(row['EA/BX'])
    if ea_bx is not None:
        values.append(f"{round(ea_bx, 0)} {Pack_Info_Mapping['EA/BX']}")
    sf_ea = _pack_float(row['SF/EA'])
    if sf_ea is not None:
        values.append(f"{round(sf_ea, 3)} {Pack_Info_Mapping['SF/EA']}")
    sf_bx = _pack_float(row['SF/BX'])
    if sf_bx is not None:
        values.append(f"{round(sf_bx, 3)} {Pack_Info_Mapping['SF/BX']}")

    if not values:
        return ''
    
    # Join values with HTML space entities
    concatenated = ' '.join(f'{v}&#160;&#160;&#160;&#160;' for v in values[:-1])
    if values:
        concatenated += values[-1]  # Add the last value without extra spaces
    
    return f'<p>{concatenated.strip()}</p>'


# ============================================================================
# CORE PROCESSING FUNCTIONS
# ============================================================================

def get_metafields2(ven_code: str, df: pd.DataFrame) -> pd.DataFrame:
    sku_list = list()
    v_sku_list = list()
    vend_code_list = list()
    uom_list = list()
    sell_unit_list = list()
    cost_uom_list = list()
    msrp_uom_list = list()
    sf_ea_list = list()
    sf_bx_list = list()
    ea_bx_list = list()
    cost_sell_unit_list = list()
    msrp_sell_unit_list = list()
    calc_show_list = list()
    conv_ratio_list = list()
    pricelist_class_list = list()
    ea_sf_list = list()
    
    for index, row in df.iterrows():
        status = row['PRICELIST STATUS']
        sku = str(row['E SKU']).strip().upper()
        v_sku = str(row['V SKU']).strip().upper()

        vend_code = row['VENDOR ITEM CODE']
        uom = row['UOM']
        sell_unit = row['SELL UNIT']
        cost_uom = row['COST/UOM']

        if np.isnan(row['PRICE/UOM']) or row['PRICE/UOM'] == "":
            msrp_uom = float(cost_uom) * 2
        else:
            msrp_uom = float(row['PRICE/UOM'])

        sf_ea = row['SF/EA']
        sf_bx = row['SF/BX']
        ea_bx = row['EA/BX']
        ea_sf = row['EA/SF']
        pricelist_class = row['pricelist.class']
        cost_sell_unit = float
        msrp_sell_unit = float
        calc_show = bool
        conv_ratio = float
        price_per_sf = float

        # Calculate cost_sell_unit and msrp_sell_unit
        if uom == "SF":
            if sell_unit == "SF":
                cost_sell_unit = cost_uom
                msrp_sell_unit = msrp_uom
            elif sell_unit == "EA" or sell_unit == "SHT":
                if np.isnan(sf_ea) or sf_ea <= 0:
                    cost_sell_unit = -1.0
                    msrp_sell_unit = -1.0
                else:
                    cost_sell_unit = cost_uom * sf_ea
                    msrp_sell_unit = msrp_uom * sf_ea
            elif sell_unit == "BX" or sell_unit == "SET":
                if np.isnan(sf_bx) or sf_bx <= 0:
                    cost_sell_unit = -1.0
                    msrp_sell_unit = -1.0
                else:
                    cost_sell_unit = cost_uom * sf_bx
                    msrp_sell_unit = msrp_uom * sf_bx
            else:
                print("Unrecognized SELL UNIT for item " + str(sku) + " UOM = " + str(uom) + "; SELL_UNIT = " + str(sell_unit))
                cost_sell_unit = ""
                msrp_sell_unit = ""
        elif uom == "EA" or uom == "SHT":
            if sell_unit == "EA" or sell_unit == "SHT":
                cost_sell_unit = cost_uom
                msrp_sell_unit = msrp_uom
            elif sell_unit == "BX":
                if np.isnan(ea_bx) or ea_bx <= 0:
                    cost_sell_unit = -1.0
                    msrp_sell_unit = -1.0
                else:
                    cost_sell_unit = cost_uom * ea_bx
                    msrp_sell_unit = msrp_uom * ea_bx
            else:
                print("Unrecognized SELL UNIT for item " + str(sku) + " UOM = " + str(uom) + "; SELL_UNIT = " + str(sell_unit))
                cost_sell_unit = ""
                msrp_sell_unit = ""
        elif uom == "BX":
            if sell_unit == "BX":
                cost_sell_unit = cost_uom
                msrp_sell_unit = msrp_uom
        elif uom == "BG":
            if sell_unit == "BG":
                cost_sell_unit = cost_uom
                msrp_sell_unit = msrp_uom
            else:
                print("Unrecognized SELL UNIT for item " + str(sku) + " UOM = " + str(uom) + "; SELL_UNIT = " + str(sell_unit))
                cost_sell_unit = ""
                msrp_sell_unit = ""
        else:
            print("Unrecognized UOM for item " + str(sku) + " UOM = " + str(uom))
            cost_sell_unit = ""
            msrp_sell_unit = ""
            
        # Generate calculator.show-for-variant
        if sell_unit == "BX" or sell_unit == "SHT" or sell_unit == "EA" or sell_unit == 'SET':
            if pricelist_class == "TRIM":
                calc_show = False
            else:
                calc_show = True
        else:
            calc_show = False
            
        # Generate conversion ratio
        if sell_unit == "BX":
            if uom == "EA" or uom == "SHT":
                conv_ratio = ea_bx
            else:
                conv_ratio = sf_bx
        elif sell_unit == "SF":
            conv_ratio = 1.0
        elif sell_unit == "SHT" or sell_unit == "EA":
            if pricelist_class == "TRIM":
                conv_ratio = ""
            else:
                conv_ratio = sf_ea
        elif sell_unit == "BG":
            conv_ratio = ""
        elif sell_unit == "SET":
            conv_ratio = sf_bx
        elif sell_unit == "PLT":
            conv_ratio = ""
        else:
            print("Unrecognized SELL UNIT for item " + str(sku) + " UOM = " + str(uom) + "; SELL_UNIT = " + str(sell_unit))
            conv_ratio = ""
            
        sku_list.append(sku)
        v_sku_list.append(v_sku)
        vend_code_list.append(vend_code)
        uom_list.append(uom)
        sell_unit_list.append(sell_unit)
        cost_uom_list.append(cost_uom)
        msrp_uom_list.append(msrp_uom)
        sf_ea_list.append(sf_ea)
        sf_bx_list.append(sf_bx)
        ea_bx_list.append(ea_bx)
        cost_sell_unit_list.append(cost_sell_unit)
        msrp_sell_unit_list.append(msrp_sell_unit)
        calc_show_list.append(calc_show)
        conv_ratio_list.append(conv_ratio)
        pricelist_class_list.append(pricelist_class)
        ea_sf_list.append(ea_sf)

    out_df = pd.DataFrame()
    out_df['Variant SKU'] = sku_list
    out_df['Variant Metafield: custom.retail_v_code [single_line_text_field]'] = v_sku_list
    out_df['Variant Price'] = msrp_sell_unit_list
    out_df['Variant Cost'] = cost_sell_unit_list
    out_df['Variant Metafield: calculator.show-for-variant [boolean]'] = calc_show_list
    out_df['Metafield: calculator.show [boolean]'] = calc_show_list
    out_df['Variant Metafield: calculator.ratio [number_decimal]'] = conv_ratio_list
    out_df['Metafield: calculator.ratio [number_decimal]'] = conv_ratio_list
    out_df['Variant Metafield: pricelist.class [single_line_text_field]'] = pricelist_class_list
    out_df['Variant Metafield: pricelist.uom [single_line_text_field]'] = uom_list
    out_df['Variant Metafield: pricelist.sf_box [number_decimal]'] = sf_bx_list
    out_df['Variant Metafield: pricelist.ea_bx [number_integer]'] = ea_bx_list
    out_df['Variant Metafield: pricelist.sf_ea [number_decimal]'] = sf_ea_list
    out_df['Variant Metafield: pricelist.sell_unit [single_line_text_field]'] = sell_unit_list
    out_df['Variant Metafield: pricelist.cost_by_uom [number_decimal]'] = cost_uom_list
    out_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'] = msrp_uom_list
    out_df['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'] = msrp_sell_unit_list
    out_df['Variant Metafield: pricelist.vendor_code [single_line_text_field]'] = vend_code_list

    return out_df


def process_vendor(vendor: str, df: pd.DataFrame, rejected_product_list: list, warning_choice: int) -> pd.DataFrame:
    active_vendors = et.get_tile_vendors()
    try:
        df = pd.DataFrame(df)
        vendor = str(vendor).strip().upper()
        if not vendor in active_vendors.keys():
            raise Exception(f"Vendor '{vendor}' not found in vendor mapping.")
    except Exception as e:
        print(f"Error processing vendor '{vendor}")
        print(f"{e}")
        print("Program exiting...")
        exit()

    df_secondary = get_metafields2(vendor, df)
    df_secondary.set_index('Variant SKU', inplace=True)
        
    out_data = {
        # Product level
        'ID': [],
        'Variant SKU': [],
        'Handle': [],
        'SERIES': [],
        'Status': [],
        'Title': [],
        'BODY HTML': [],
        # Variant level
        'Variant ID': [],
        'Variant Inventory Item ID': [],
        'Variant Weight': [],
        'Variant Metafield: pricelist.vendor_code [single_line_text_field]': [],
        'Variant Metafield: custom.retail_v_code [single_line_text_field]': [],
        'Variant Metafield: pricelist.class [single_line_text_field]': [],
        'Option 1 Name': [],
        'Option 1 Value': [],
        'Option 2 Name': [],
        'Option 2 Value': [],
        'Option 3 Name': [],
        'Option 3 Value': [],
        'Variant Metafield: pricelist.ea_bx [number_integer]': [],
        'Variant Metafield: pricelist.sf_ea [number_decimal]': [],
        'Variant Metafield: pricelist.sf_box [number_decimal]': [],
        'Variant Metafield: pricelist.uom [single_line_text_field]': [],
        'Variant Metafield: pricelist.sell_unit [single_line_text_field]': [],
        'Variant Metafield: pricelist.cost_by_uom [number_decimal]': [],
        'Variant Metafield: pricelist.msrp_sell_unit [number_decimal]':[],
        'Variant Metafield: pricelist.msrp_uom [number_decimal]': [],
        'Variant Cost': [],
        'Variant Price': [],
        'Variant Metafield: calculator.ratio [number_decimal]': [],
        'Variant Metafield: calculator.show-for-variant [boolean]':[],
        #  Product Metafields
        'Metafield: calculator.show [boolean]':[],
        'Metafield: calculator.ratio [number_decimal]': [],
        'Metafield: filter.material [list.single_line_text_field]': [],
        'Metafield: filter.type [single_line_text_field]': [],
        'Metafield: filter.type_v2 [list.single_line_text_field]': [],
        'Metafield: pricelist.filter [single_line_text_field]': [],
        'Metafield: pricelist.classification_id [number_integer]': [],
        'Metafield: pricelist.product_category [single_line_text_field]': [],
        'Metafield: pricelist.product_class [single_line_text_field]': [],
        'Metafield: pricelist.product_type [single_line_text_field]': [],
        'Metafield: custom.series [single_line_text_field]' : [],

        'Metafield: custom.multi_line_pack_info [multi_line_text_field]': [],
        'Metafield: custom.custom_variant [collection_reference]': [],
        'Metafield: tile_filter.primary_application [single_line_text_field]': [],
        'Metafield: filter.application [list.single_line_text_field]': [],
        'Metafield: filter.color [list.single_line_text_field]': [],
        'Metafield: filter.size [single_line_text_field]': [],
        'Metafield: filter.size_standardized [single_line_text_field]': [],
        'Metafield: filter.finish [list.single_line_text_field]':[],
        'Metafield: filter.look [list.single_line_text_field]': [],
        'Metafield: tile_filter.tile_shape [single_line_text_field]': [],
        'Metafield: tile_filter.commercial_application [list.single_line_text_field]': [],
        'Metafield: tile_filter.trim_type [single_line_text_field]': [],
        'Metafield: tile_filter.mosaic_shape [single_line_text_field]': [],
        'Metafield: tile_filter.format [single_line_text_field]': [],
        'Metafield: tile_filter.other [single_line_text_field]': [],
        'Metafield: tile_filter.thickness [single_line_text_field]': [],
        'Metafield: custom.launch_date [date]': [],
        'Metafield: custom.is_trim [boolean]': [],
        'Metafield: custom.inventory_tracked [boolean]': [],
        'Tags': []

    }

    # Iterate throught the MPL
    for i, r in df.iterrows():
        # helper variables
        e_sku = str(r['E SKU']).strip().upper()
        uom = r['UOM']
        sell_unit = r['SELL UNIT']
    
        for _id_col in ('ID', 'Variant ID', 'Variant Inventory Item ID'):
            value = r.get(_id_col)
            out_data[_id_col].append('' if pd.isna(value) else int(value))
        
        
        out_data['BODY HTML'].append(get_product_description(r))
        out_data['Variant Weight'].append(get_weight(r))
        out_data['Variant SKU'].append(r['E SKU'].strip().upper())
        out_data['Handle'].append(build_handle(r))
        out_data['SERIES'].append(r.get('SERIES', ''))
        out_data['Status'].append(get_status(r))
        #out_data['Title'].append(r.get('SHOPIFY NAME', ''))
        out_data['Title'].append(get_proposed_new_title(r))
        out_data['Metafield: pricelist.classification_id [number_integer]'].append(r.get('CLASSIFICATION ID',''))
        
        # Handle options
        options_dict = get_options(r)

        for key,value in options_dict.items():
            out_data[key].append(value)


        out_data['Variant Metafield: custom.retail_v_code [single_line_text_field]'].append(df_secondary.at[e_sku, 'Variant Metafield: custom.retail_v_code [single_line_text_field]'])
        out_data['Variant Metafield: pricelist.class [single_line_text_field]'].append(df_secondary.at[e_sku,'Variant Metafield: pricelist.class [single_line_text_field]'])
        out_data['Variant Metafield: pricelist.sf_box [number_decimal]'].append(df_secondary.at[e_sku,'Variant Metafield: pricelist.sf_box [number_decimal]'])
        out_data['Variant Metafield: pricelist.ea_bx [number_integer]'].append(df_secondary.at[e_sku,'Variant Metafield: pricelist.ea_bx [number_integer]'])
        out_data['Variant Metafield: pricelist.sf_ea [number_decimal]'].append(df_secondary.at[e_sku,'Variant Metafield: pricelist.sf_ea [number_decimal]'])
        out_data['Variant Metafield: pricelist.vendor_code [single_line_text_field]'].append(df_secondary.at[e_sku,'Variant Metafield: pricelist.vendor_code [single_line_text_field]'])
        
        
        out_data['Variant Metafield: pricelist.uom [single_line_text_field]'].append(df_secondary.at[e_sku, 'Variant Metafield: pricelist.uom [single_line_text_field]'])
        out_data['Variant Metafield: pricelist.sell_unit [single_line_text_field]'].append(df_secondary.at[e_sku, 'Variant Metafield: pricelist.sell_unit [single_line_text_field]'])
        out_data['Variant Metafield: pricelist.cost_by_uom [number_decimal]'].append(df_secondary.at[e_sku, 'Variant Metafield: pricelist.cost_by_uom [number_decimal]'])
        out_data['Variant Price'].append(df_secondary.at[e_sku, 'Variant Price'])
        out_data['Variant Metafield: calculator.ratio [number_decimal]'].append(df_secondary.at[e_sku, 'Variant Metafield: calculator.ratio [number_decimal]'])
        out_data['Metafield: calculator.ratio [number_decimal]'].append(df_secondary.at[e_sku, 'Metafield: calculator.ratio [number_decimal]'])
        out_data['Metafield: filter.material [list.single_line_text_field]'].append(get_material_filter(r, warning_choice, SESSION_SKIPS))
        out_data['Metafield: filter.type [single_line_text_field]'].append(get_type_filter(r))
        out_data['Metafield: filter.type_v2 [list.single_line_text_field]'].append(get_type_filter_v2(r))
        out_data['Metafield: pricelist.filter [single_line_text_field]'].append(str(r.get('FINISH') or '').title())
        out_data['Metafield: filter.finish [list.single_line_text_field]'].append(get_finish_filter(r, warning_choice, SESSION_SKIPS))
        out_data['Metafield: filter.size_standardized [single_line_text_field]'].append(get_size_filter(r))
        
        out_data['Metafield: pricelist.product_category [single_line_text_field]'].append(get_classification(r, 'CATEGORY'))
        out_data['Metafield: pricelist.product_class [single_line_text_field]'].append(get_classification(r, 'CLASS'))
        out_data['Metafield: pricelist.product_type [single_line_text_field]'].append(get_classification(r, 'TYPE'))
        out_data['Metafield: custom.multi_line_pack_info [multi_line_text_field]'].append(concatenate_with_html(r))
        _series = r.get('SERIES', '')
        out_data['Metafield: custom.series [single_line_text_field]'].append('' if pd.isna(_series) else str(_series).strip().title())
        series_transformed = custom_transform_series('' if pd.isna(_series) else _series)
        out_data['Metafield: custom.custom_variant [collection_reference]'].append(create_series_handle(vendor, series_transformed))

        out_data['Metafield: tile_filter.primary_application [single_line_text_field]'].append(r.get('MAIN APPLICATION', ''))
        out_data['Metafield: filter.application [list.single_line_text_field]'].append(get_application_filter(r, warning_choice, SESSION_SKIPS))
        out_data['Metafield: filter.color [list.single_line_text_field]'].append(get_color_filter(r, warning_choice, SESSION_SKIPS))
        out_data['Metafield: filter.size [single_line_text_field]'].append(get_size_display_filter(r))
        out_data['Metafield: filter.look [list.single_line_text_field]'].append(get_look_filter(r, warning_choice, SESSION_SKIPS))
        out_data['Metafield: tile_filter.tile_shape [single_line_text_field]'].append(r.get('TILE SHAPE (FILTER)', ''))
        out_data['Metafield: tile_filter.commercial_application [list.single_line_text_field]'].append(r.get('COMMERCIAL APPLICATION', ''))
        out_data['Metafield: tile_filter.trim_type [single_line_text_field]'].append(r.get('TRIM TYPE (FILTER)', ''))
        out_data['Metafield: tile_filter.mosaic_shape [single_line_text_field]'].append(get_mosaic_shape_filter(warning_choice,r,SESSION_SKIPS))
        out_data['Metafield: tile_filter.format [single_line_text_field]'].append(r.get('FORMAT (FILTER)', ''))
        out_data['Metafield: tile_filter.other [single_line_text_field]'].append(r.get('OTHER (FILTER)', ''))
        out_data['Metafield: tile_filter.thickness [single_line_text_field]'].append(r.get('THICKNESS (FILTER)', ''))
        out_data['Metafield: custom.launch_date [date]'].append(get_launch_date(r))
        out_data['Metafield: custom.is_trim [boolean]'].append(get_is_trim(r))
        out_data['Metafield: custom.inventory_tracked [boolean]'].append(get_inventory_tracked(vendor))

        out_data['Tags'].append(generate_tags(r))
        out_data['Variant Metafield: calculator.show-for-variant [boolean]'].append(df_secondary.at[e_sku, 'Variant Metafield: calculator.show-for-variant [boolean]'])
        out_data['Metafield: calculator.show [boolean]'].append(df_secondary.at[e_sku,'Metafield: calculator.show [boolean]'])
        out_data['Variant Cost'].append(df_secondary.at[e_sku, 'Variant Cost'])
        out_data['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'].append(df_secondary.at[e_sku,'Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'])
        out_data['Variant Metafield: pricelist.msrp_uom [number_decimal]'].append(df_secondary.at[e_sku, 'Variant Metafield: pricelist.msrp_uom [number_decimal]'])
  
    
    ## Debug array length issues
    # for key, array in out_data.items():
    #     print(f"{key}: Length = {len(array)}")
    
    out_df = pd.DataFrame(out_data)

    # Assign Default values
    out_df['Command'] = 'MERGE'
    out_df['Vendor'] = f"{active_vendors[vendor]}"
    out_df['Type'] = 'Building Materials'
    out_df['Published'] = 'FALSE'
    out_df['Published Scope'] = 'web'
    out_df['Variant Command'] = 'MERGE'
    out_df['Variant Weight Unit'] = 'lb'
    out_df['Variant Taxable'] = 'TRUE'
    out_df['Variant Inventory Policy'] = 'deny'
    out_df['Variant Fulfillment Service'] = 'manual'
    out_df['Variant Requires Shipping'] = 'TRUE'

    # Locations
    out_df['Inventory Available: Elit Tile -  North Hollywood'] = 'Stocked'
    out_df['Inventory Available: Elit Tile - Los Angeles'] = 'Stocked'

    for index, row in out_df.iterrows():
        if row['Status'] != "Draft":
            rejected_product_list.append(row)
            out_df = out_df.drop(index, axis=0)
    
    return out_df


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    output_import_folder = os.path.join(parent_dir, 'Import Files')
    os.makedirs(output_import_folder, exist_ok=True)

    Vendor_Mapping = et.get_tile_vendors()

    warning_choice = get_warning_choice()

    # Test merged MPL
    mpl_df = et.get_tile_mpl_itshare()

    vendors_to_process = get_vendors_to_process(mpl_df, Vendor_Mapping)

    mpl_dict = {}
    for vendor in vendors_to_process:
        vendor_df = mpl_df[mpl_df['VENDOR'].str.upper() == vendor]
        mpl_dict[vendor] = vendor_df
    
    classification_df = et.get_classification_table_itshare()

    global TAXONOMY_BY_ID
    TAXONOMY_BY_ID = (
        classification_df
        .set_index("CLASSIFICATION ID")[["CATEGORY", "CLASS", "TYPE"]]
        .fillna('')
        .to_dict(orient='index')
    )

    # Variables
    rejected_product_list = []
    combined_vendors = []

    for vendor, vendor_df in mpl_dict.items():
        processed_df = process_vendor(vendor, vendor_df, rejected_product_list, warning_choice)
        
        # Remove NAN values and replace with empty string
        processed_df = processed_df.fillna('').copy()
        
        output_import_file = os.path.join(output_import_folder, vendor + ' Shopify Tile Import.xlsx')
        processed_df.to_excel(output_import_file, index=False, sheet_name='Products')
        print(f'Import Excel file has been created in the "{output_import_folder}" folder.')

        combined_vendors.append(processed_df)

    if len(combined_vendors) > 1:
        combined_all = pd.concat(combined_vendors, ignore_index=True)
        combined_fn = os.path.join(output_import_folder, "ALL-VENDORS-IMPORT.xlsx")
        combined_all.to_excel(combined_fn, index=False, sheet_name="Products")
        print(f"Created {combined_fn}")


    # Write the rejected products to a file
    rejected_fn = os.path.join(output_import_folder, "REJECTED_PRODUCTS_v3.xlsx")
    rejected_df = pd.DataFrame(rejected_product_list)
    rejected_df = notate_rejections(rejected_df)
    rejected_df.to_excel(rejected_fn, index=None, sheet_name='Rejected Products')
    print(f"Created {rejected_fn}")


    print('\nProgram completes\n')

if __name__ == "__main__":
    main()
