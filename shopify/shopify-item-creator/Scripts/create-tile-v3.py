import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

# Version 3 to implement new tags

# Add locations

# Version 2 to handle decimal places in the ID columns.
# Added Retail V Code Metafield 08 16 2024
# Added Series metafield 08 21 2024
#------------- Functions -------------------------------------------#

def custom_transform_series(series):
    if pd.isna(series) or series == '':
        return ''  # Return empty if SERIES is missing
    
    # Clean up extra spaces, remove unwanted characters, and convert to lowercase
    cleaned_series = re.sub(r'[^a-zA-Z0-9\s]', '', series.strip())  # Remove non-alphanumeric characters except spaces
    cleaned_series = re.sub(r'\s+', ' ', cleaned_series)  # Replace multiple spaces with a single space
    cleaned_series = cleaned_series.lower()  # Convert to lowercase
    return 'series-' + cleaned_series.replace(' ', '-')  # Replace spaces with single hyphen

Pack_Info_Mapping = et.get_pack_info_mapping()

# Define the order of options
options = ['SIZE', 'COLOR', 'FINISH']

def concatenate_with_html(row):
    values = []
    if pd.notna(row['EA/BX']):
        rounded_value = round(float(row['EA/BX']), 0)
        values.append(f"{rounded_value} {Pack_Info_Mapping['EA/BX']}")
    if pd.notna(row['SF/EA']):
        rounded_value = round(float(row['SF/EA']), 3)
        values.append(f"{rounded_value} {Pack_Info_Mapping['SF/EA']}")
    if pd.notna(row['SF/BX']):
        rounded_value = round(float(row['SF/BX']), 3)
        values.append(f"{rounded_value} {Pack_Info_Mapping['SF/BX']}")

    if not values:
        return ''
    
    # Join values with HTML space entities
    concatenated = ' '.join(f'{v}&#160;&#160;&#160;&#160;' for v in values[:-1])
    if values:
        concatenated += values[-1]  # Add the last value without extra spaces
    
    return f'<p>{concatenated.strip()}</p>'


# Map the custom variant field with the handle of the series colleciton

def get_non_zero_numbers(vendor_id):
    # Use regular expression to find all numbers in the string
    numbers = re.findall(r'\d+', vendor_id)
    
    # Filter out numbers that are non-zero and remove leading zeros
    non_zero_numbers = [str(int(num)) for num in numbers if int(num) != 0]
    
    return non_zero_numbers

# Function to create series handle
def create_series_handle(vendor_id, series_name):
    if pd.notna(series_name) and series_name:  # Check if series_name (Tags) is not NaN and not empty
        non_zero_numbers = get_non_zero_numbers(vendor_id)
        if non_zero_numbers:  # Check if there are valid non-zero numbers
            # Assuming you want the first non-zero number if there are multiple
            non_zero_number = non_zero_numbers[0]
            return f'{non_zero_number}-{series_name}'
    return ''  # Return an empty string if Tags is NaN or no valid non-zero number

# Function to generate additional tags from other columns (excluding SERIES)
def generate_additional_tags(row):
    tags = []

    # Add tags based on other columns
    columns_to_check = ['LOOK', 'MAIN APPLICATION', 'MATERIAL (FILTER)', 
                        'BASE COLOR (FILTER)', 'PIECE TYPE (FILTER)', 'FINISH (FILTER)', 
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

# Function to generate final tags string
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

#---------------- Begin Script -------------------------------------------------------------

folder_path_filtered_data = r'C:\Users\VVillafana\Desktop\python_scripts\elit-tile-script\shopify-item-creator\Filtered Data'
output_import_folder = r'C:\Users\VVillafana\Desktop\python_scripts\elit-tile-script\shopify-item-creator\Import Files'

Vendor_Mapping = et.get_tile_vendors()

ftp = et.ftp_login()

Vendor_id = input('Input vendor code (not case sensistve): ').upper()

df_unfiltered = et.get_tile_mpl_by_vendor(ftp, Vendor_id)

#Filtering out all of the INACTIVE items and saving them into an Excel File to spot check if needed

df_unfiltered = df_unfiltered[df_unfiltered['PRICELIST STATUS'] == "ACTIVE"]

os.makedirs(folder_path_filtered_data, exist_ok=True)

output_excel_file = os.path.join(folder_path_filtered_data, Vendor_id + " Filtered_Data.xlsx")
df_unfiltered.to_excel(output_excel_file, index=False)

file_path = os.path.join(folder_path_filtered_data, output_excel_file )

print("Filtered Excel file has been created in the '{}' folder.".format(folder_path_filtered_data))

df = pd.read_excel(file_path)

# Begin filling out the import file columns

new_data = {
    'ID': [],
    'Variant SKU': [],
    'Handle': [],
    'SERIES': [],
    'Title': [],
    'BODY HTML': [],
    'Variant ID': [],
    'Variant Inventory Item ID': [],
    'Variant Weight': [],
    'Variant Metafield: pricelist.vendor_code [single_line_text_field]': [],
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
    'Variant Price': [],
    'Variant Metafield: calculator.ratio [number_decimal]': [],
    'Metafield: calculator.ratio [number_decimal]': [],
    'Metafield: filter.material [list.single_line_text_field]': [],
    'Metafield: filter.piece_type [single_line_text_field]': [],
    'Metafield: pricelist.filter [single_line_text_field]': [],
    'Metafield: custom.multi_line_pack_info [multi_line_text_field]': [],
    'Metafield: custom.custom_variant [collection_reference]': [],
    'Metafield: tile_filter.primary_application [single_line_text_field]': [],
    'Metafield: filter.application [list.single_line_text_field]': [],
    'Metafield: filter.color [list.single_line_text_field]': [],
    'Metafield: filter.size [single_line_text_field]': [],
    'Metafield: filter.look [list.single_line_text_field]': [],
    'Metafield: tile_filter.tile_shape [single_line_text_field]': [],
    'Metafield: tile_filter.commercial_application [list.single_line_text_field]': [],
    'Metafield: tile_filter.trim_type [single_line_text_field]': [],
    'Metafield: tile_filter.mosaic_shape [single_line_text_field]': [],
    'Metafield: tile_filter.format [single_line_text_field]': [],
    'Metafield: tile_filter.other [single_line_text_field]': [],
    'Metafield: tile_filter.thickness [single_line_text_field]': [],
    'Metafield: custom.is_trim [boolean]': [],
    'Tags': []

}

# Process each row in the DataFrame
for i, r in df.iterrows():
    # Handle ID column separately to avoid ValueError
    new_data['ID'].append('' if pd.isna(r.get('ID')) else int(r.get('ID', 0)))
    new_data['Variant ID'].append('' if pd.isna(r.get('Variant ID')) else int(r.get('Variant ID', 0)))
    new_data['Variant Inventory Item ID'].append('' if pd.isna(r.get('Variant Inventory Item ID')) else int(r.get('Variant Inventory Item ID', 0)))

    # Fill other columns with default values or from the DataFrame
    new_data['Variant SKU'].append(r.get('E SKU', ''))
    new_data['Variant Weight'].append(r.get('WEIGHT', ''))
    new_data['Variant Metafield: pricelist.vendor_code [single_line_text_field]'].append(r.get('VENDOR ITEM CODE',''))
    new_data['Variant Metafield: pricelist.class [single_line_text_field]'].append(r.get('pricelist.class',''))
    new_data['Handle'].append(r.get('HANDLE', ''))
    new_data['SERIES'].append(r.get('SERIES', ''))
    new_data['Title'].append(r.get('SHOPIFY NAME', ''))
    new_data['BODY HTML'].append('')

    # Handle options
    option_names = []
    option_values = []

    for option in options:
        if pd.notna(r.get(option, '')):
            option_names.append(option.title())
            option_values.append(r.get(option, ''))

    for j in range(3):
        new_data[f'Option {j+1} Name'].append(option_names[j] if j < len(option_names) else '')
        new_data[f'Option {j+1} Value'].append(option_values[j] if j < len(option_values) else '')

    # Continue with the simple mappings
    new_data['Variant Metafield: pricelist.ea_bx [number_integer]'].append(
        round(float(r.get('EA/BX', 0)), 0) if r.get('EA/BX', '') else ''
    )
    new_data['Variant Metafield: pricelist.sf_ea [number_decimal]'].append(
        round(float(r.get('SF/EA', 0)), 3) if r.get('SF/EA', '') else ''
    )
    new_data['Variant Metafield: pricelist.sf_box [number_decimal]'].append(
        round(float(r.get('SF/BX', 0)), 3) if r.get('SF/BX', '') else ''
    )
    new_data['Variant Metafield: pricelist.uom [single_line_text_field]'].append(r.get('UOM', ''))
    new_data['Variant Metafield: pricelist.sell_unit [single_line_text_field]'].append(r.get('SELL UNIT', ''))
    new_data['Variant Metafield: pricelist.cost_by_uom [number_decimal]'].append(r.get('COST', ''))
    new_data['Variant Price'].append(r.get('PRICE PER SELL UNIT', ''))
    new_data['Variant Metafield: calculator.ratio [number_decimal]'].append(r.get('CONV', ''))
    new_data['Metafield: calculator.ratio [number_decimal]'].append(r.get('CONV', ''))
    new_data['Metafield: filter.material [list.single_line_text_field]'].append(r.get('MATERIAL (FILTER)', ''))
    new_data['Metafield: filter.piece_type [single_line_text_field]'].append(r.get('PIECE TYPE (FILTER)', ''))
    new_data['Metafield: pricelist.filter [single_line_text_field]'].append(r.get('FINISH (FILTER)', ''))

    # Generate tags
    transform_series = custom_transform_series(r['SERIES'])

    # Add other fields
    new_data['Metafield: custom.multi_line_pack_info [multi_line_text_field]'].append(concatenate_with_html(r))

    series_transformed = custom_transform_series(r.get('SERIES', ''))
    new_data['Metafield: custom.custom_variant [collection_reference]'].append(create_series_handle(Vendor_id, series_transformed))

    new_data['Metafield: tile_filter.primary_application [single_line_text_field]'].append(r.get('MAIN APPLICATION', ''))
    new_data['Metafield: filter.application [list.single_line_text_field]'].append(r.get('RESIDENTIAL APPLICATION', ''))
    new_data['Metafield: filter.color [list.single_line_text_field]'].append(r.get('BASE COLOR (FILTER)', ''))
    new_data['Metafield: filter.size [single_line_text_field]'].append(r.get('SIZE (FILTER)', ''))
    new_data['Metafield: filter.look [list.single_line_text_field]'].append(r.get('LOOK', ''))
    new_data['Metafield: tile_filter.tile_shape [single_line_text_field]'].append(r.get('TILE SHAPE (FILTER)', ''))
    new_data['Metafield: tile_filter.commercial_application [list.single_line_text_field]'].append(r.get('COMMERCIAL APPLICATION', ''))
    new_data['Metafield: tile_filter.trim_type [single_line_text_field]'].append(r.get('TRIM TYPE (FILTER)', ''))
    new_data['Metafield: tile_filter.mosaic_shape [single_line_text_field]'].append(r.get('MOSAIC SHAPE (FILTER)', ''))
    new_data['Metafield: tile_filter.format [single_line_text_field]'].append(r.get('FORMAT (FILTER)', ''))
    new_data['Metafield: tile_filter.other [single_line_text_field]'].append(r.get('OTHER (FILTER)', ''))
    new_data['Metafield: tile_filter.thickness [single_line_text_field]'].append(r.get('THICKNESS (FILTER)', ''))

    # Determine if item is a trim. Check pricelist.class and PIECE TYPE (FILTER)
    pricelist_class = str(r.get('pricelist.class', '')).strip().upper() if r.get('pricelist.class', '') is not None else ''
    piece_type = str(r.get('PIECE TYPE (FILTER)', '')).strip().upper() if r.get('PIECE TYPE (FILTER)', '') is not None else ''
    is_trim = 'TRUE' if (pricelist_class == 'TRIM' or piece_type == 'TRIM') else 'FALSE'
    new_data['Metafield: custom.is_trim [boolean]'].append(is_trim)

    # Tags Column - Apply transformation logic
    new_data['Tags'].append(generate_tags(r))

# Check lengths to debug
# for key, value in new_data.items():
    # print(f"{key}: {len(value)}")

# Create DataFrame from new_data
new_df = pd.DataFrame(new_data)

# Assign static columns

new_df['Metafield: custom.series [single_line_text_field]'] = df['SERIES'].str.title()

# Create the logic for if an item needs the calculator or not

new_df['Variant Metafield: calculator.show-for-variant [boolean]'] = (new_df['Variant Metafield: pricelist.uom [single_line_text_field]'] != 
                                                                      new_df['Variant Metafield: pricelist.sell_unit [single_line_text_field]']).astype(str).str.upper()
new_df['Metafield: calculator.show [boolean]'] = new_df['Variant Metafield: calculator.show-for-variant [boolean]']

# Using a formula to generate Price and cost

new_df['Variant Cost'] = new_df['Variant Metafield: pricelist.cost_by_uom [number_decimal]'].astype(float) * new_df['Metafield: calculator.ratio [number_decimal]'].astype(float)
new_df['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'] = new_df['Variant Price']
new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'] = new_df['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'].astype(float) / new_df['Metafield: calculator.ratio [number_decimal]'].astype(float)
new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'] = new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'].round(2)
new_df['Command'] = 'MERGE'
new_df['Status'] = 'Draft'

# Apply the function to generate tags for each row
# new_df['Tags'] = df.apply(generate_additional_tags, axis=1)

vendor_name = Vendor_Mapping.get(Vendor_id, "Vendor ID not found")
new_df['Vendor'] = vendor_name
new_df['Type'] = 'Building Materials'
new_df['Published'] = 'FALSE'
new_df['Published Scope'] = 'web'
new_df['Variant Command'] = 'MERGE'
new_df['Variant Weight Unit'] = 'lb'
new_df['Variant Taxable'] = 'TRUE'
new_df['Variant Inventory Policy'] = 'deny'
new_df['Variant Fulfillment Service'] = 'manual'
new_df['Variant Requires Shipping'] = 'TRUE'
new_df['Variant Metafield: custom.retail_v_code [single_line_text_field]'] = df['V SKU']

# Locations

new_df['Inventory Available: Elittile.com -  North Hollywood'] = 'Stocked'
new_df['Inventory Available: Elittile.com - Los Angeles'] = 'Stocked'


# Define a dictionary to specify the data type for each column
dtype_dict = {col: str for col in new_df.columns}

# Fill NaN values with empty strings using the specified data types
new_df = new_df.fillna('', inplace=False).astype(dtype_dict)

# Create Import Excel File from new_df
os.makedirs(output_import_folder, exist_ok=True)

sheet_name = 'Products'

output_import_file = os.path.join(output_import_folder, Vendor_id + ' Shopify Tile Import.xlsx')
new_df.to_excel(output_import_file, index=False, sheet_name=sheet_name)
print(f'Import Excel file has been created in the "{output_import_folder}" folder.')