import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

'''
This script will do two things. It will make the add item import file to import straight into NetSuite and the UOM import file that is needed before
the add item file. It requires only the mpl file be updated and uploaded on to the FTP server.

'''


def build_sales_description(row):
    parts = []
    if not pd.isnull(row.get('Pcs in a Box')):
        parts.append(str(row['Pcs in a Box']) + ' EA/BX')
    if not pd.isnull(row.get('SQFT BY PCS/SHEET')):
        parts.append(str(row['SQFT BY PCS/SHEET']) + ' SF/EA')
    if not pd.isnull(row.get('SQFT BY BOX')):
        parts.append(str(row['SQFT BY BOX']) + ' SF/BX')
    return ' '.join(parts)


def build_item_name(row, mpl_type):
    if mpl_type == "2":
        return row['SHOPIFY NAME'].upper()
    if pd.isna(row['FINISH']):
        return row['SERIES'].strip()
    return row['SERIES'].strip() + ' ' + row['FINISH'].strip().upper()


def build_add_item_df(mpl, mpl_type, vendor, class_mapping,
                       uom_mapping, plural_uom_mapping,
                       sell_unit_mapping, plural_sell_unit_mapping):
    df = pd.DataFrame()

    df['externalid'] = mpl['E SKU']
    df['V SKU'] = mpl['V SKU'].str.upper()
    df['itemId'] = df['externalid']
    df['internalID'] = ''
    df['Item Weight'] = mpl['WEIGHT/SELL UNIT']
    df['ID'] = mpl['ID']
    df['isdropshipitem'] = "T"
    df['vendor_code'] = mpl["VENDOR ITEM CODE"].astype(str).replace('nan', '')
    df['SERIES'] = mpl['SERIES'].where(mpl['SERIES'].notna(), '').astype(str).str.upper()
    df['Item Size'] = mpl['SIZE'].str.upper()
    df['Item Color'] = mpl['COLOR'].where(mpl['COLOR'].notna(), '').astype(str).str.upper()

    if mpl_type == "2":
        df['Item Name'] = mpl['SHOPIFY NAME'].str.upper()
    else:
        df['Item Name'] = np.where(
            mpl['FINISH'].isna(),
            mpl['SERIES'].str.strip(),
            mpl['SERIES'].str.strip() + ' ' + mpl['FINISH'].str.strip().str.upper()
        )

    df['Item Number and Name'] = df['externalid'] + ' ' + df['Item Name']
    df['displayname'] = df[['Item Name', 'Item Size', 'Item Color', 'vendor_code', 'V SKU']].fillna('').astype(str).apply(lambda x: ' '.join(x[x != '']), axis=1)
    df['Type'] = 'Inventory Item'
    df['Pcs in a Box'] = mpl['EA/BX']
    df['SQFT BY PCS/SHEET'] = mpl['SF/EA']
    df['SQFT BY BOX'] = mpl['SF/BX']

    # Creating Sales Description
    df['salesdescription'] = ''
    for index, row in df.iterrows():
        df.at[index, 'salesdescription'] = build_sales_description(row)

    # Class mapping
    if mpl_type == "2":
        df['Class'] = 110
    else:
        df['Class'] = mpl['PIECE TYPE (FILTER)'].str.upper().map(class_mapping)

    df['Sales Packaging Unit'] = mpl['SELL UNIT'].str.upper().map(sell_unit_mapping)
    df['UOM'] = mpl['UOM'].str.upper().map(uom_mapping)
    df['Sales QTY Per Pack Unit'] = mpl['CONV']
    df['stockunit'] = mpl['UOM'].str.upper().map(plural_uom_mapping)
    df['purchaseunit'] = df['stockunit']
    df['saleunits'] = mpl['SELL UNIT'].str.upper().map(plural_sell_unit_mapping)
    df['cost'] = mpl['COST/UOM']

    base_price = mpl['PRICE PER SELL UNIT']
    df['Price by UOM'] = base_price / df['Sales QTY Per Pack Unit']

    df['unitstype'] = df['externalid']
    df['parent'] = ''
    df['includechildren'] = ''
    df['Department'] = ''
    df['Location'] = 'LA ElitTile.com'
    df['costingmethod'] = ''
    df['purchasedescription'] = ''
    df['matchbilltoreceipt'] = ''
    df['usebins'] = ''
    df['supplyreplenishmentmethod'] = ''
    df['alternatedemandsourceitem'] = ''
    df['autopreferredstocklevel'] = ''
    df['reordermultiple'] = ''
    df['isspecialorderitem'] = ''
    df['autoreorderpoint'] = ''
    df['autoleadtime'] = ''
    df['leadtime'] = ''
    df['safetystocklevel'] = ''
    df['safetystockleveldays'] = ''
    df['transferprice'] = ''
    df['preferredlocation'] = ''
    df['itembinnumber1'] = ''
    df['preferredperlocation'] = ''
    df['subsidiary'] = 'Elit Tile Consolidated : ElitTile.com'
    df['vendor1_name'] = vendor
    df['vendor1_preferred'] = ''
    df['vendor1_subsidiary'] = 10
    df['vendor1_purchaseprice'] = df['cost']
    df['vendor1_schedule'] = ''
    df['vendor1_code'] = df['vendor_code']
    df['vendor2_name'] = 'E0002 ELIT TILE LA'
    df['vendor2_preferred'] = 'T'
    df['vendor2_subsidiary'] = 10
    df['vendor2_purchaseprice'] = df['cost']
    df['vendor2_schedule'] = ''
    df['vendor2_code'] = df['vendor_code']
    df['itemLocationLine1_location'] = ''
    df['itemLocationLine1_defaultreturncost'] = ''
    df['itemLocationLine1_preferredstocklevel'] = ''
    df['itemLocationLine1_reorderpoint'] = ''
    df['itemLocationLine1_lotnumbers'] = ''
    df['itemLocationLine1_lotsizingmethod'] = ''
    df['costestimatetype'] = ''
    df['costestimate'] = ''
    df['minimumquantity'] = ''
    df['enforceminqtyinternally'] = ''
    df['itemPriceLine1_itemPriceTypeRef'] = 'BASE PRICE'
    df['itemPriceLine1_itemPrice'] = base_price
    df['itemPriceLine1_quantityPricing'] = 0
    df['cogsaccount'] = ''
    df['incomeaccount'] = ''
    df['assetaccount'] = ''
    df['billpricevarianceacct'] = ''
    df['billqtyvarianceacct'] = ''
    df['billexchratevarianceacct'] = ''
    df['custreturnvarianceaccount'] = ''
    df['vendreturnvarianceaccount'] = ''
    df['taxSchedule'] = 'Taxable'
    df['Item Image'] = ''
    df['Variant Inventory Item ID'] = mpl['Variant Inventory Item ID']
    df['Variant ID'] = mpl['Variant ID']
    df['Variant Weight'] = df['Item Weight']
    df['Variant Weight Unit'] = 'lb'
    df['Handle'] = mpl['Handle']
    df['Shopify Flag'] = 'Add/Update Item'

    dtype_dict = {col: str for col in df.columns}
    return df.fillna('', inplace=False).astype(dtype_dict)


def build_uom_df(add_item_df, plural_mapping, abb_mapping, plural_abb_mapping):
    df = add_item_df.copy()

    # Filter rows where Sales Packaging Unit differs from UOM
    mask = df['Sales Packaging Unit'] != df['UOM']
    filtered_rows = df[mask]

    # Append duplicated rows for items that need a second UOM row
    uom_df = pd.concat([df, filtered_rows], ignore_index=True)
    uom_df = uom_df.sort_values(by='externalid').reset_index(drop=True)

    # Select only the desired columns
    uom_df = uom_df[['externalid', 'UOM', 'Sales Packaging Unit']]
    uom_df['Internal ID*Update Only'] = ''

    # Determine unit name: base UOM for even rows, Sales Packaging Unit for odd rows
    unit_names = []
    for index, row in uom_df.iterrows():
        if row['UOM'] == row['Sales Packaging Unit']:
            unit_names.append(row['UOM'])
        else:
            unit_names.append(row['Sales Packaging Unit'] if index % 2 != 0 else row['UOM'])

    uom_df['Unit Name (Name)'] = unit_names
    uom_df = uom_df.drop(columns=['UOM', 'Sales Packaging Unit'])

    # Plural names, abbreviations
    uom_df['Plural Name'] = uom_df['Unit Name (Name)'].map(plural_mapping)
    uom_df['Abbreviation'] = uom_df['Unit Name (Name)'].map(abb_mapping)
    uom_df['Plural Abbreviation'] = uom_df['Unit Name (Name)'].map(plural_abb_mapping)

    # Conversion Rate and Base Unit
    conversion_rate = []
    base_unit = []

    for index, row in uom_df.iterrows():
        if index % 2 == 0:
            conversion_rate.append(1)
            base_unit.append('Yes')
        else:
            sales_qty = add_item_df.loc[add_item_df['externalid'] == row['externalid'], 'Sales QTY Per Pack Unit'].values
            if len(sales_qty) > 0:
                conversion_rate.append(sales_qty[0])
            else:
                conversion_rate.append(None)
            base_unit.append('Yes' if conversion_rate[-1] == 1 else 'No')

    uom_df['Conversion Rate(/Base)'] = conversion_rate
    uom_df['Base Unit'] = base_unit

    uom_df = uom_df.rename(columns={'externalid': 'Item(Type Name)'})

    uom_df = uom_df.fillna({
        'Conversion Rate(/Base)': 0,
        'Item(Type Name)': '',
        'Unit Name (Name)': '',
        'Internal ID*Update Only': '',
        'Plural Name': '',
        'Abbreviation': '',
        'Plural Abbreviation': '',
        'Base Unit': ''
    })

    uom_df = uom_df.sort_values(by=['Item(Type Name)', 'Base Unit'], ascending=[True, False])

    return uom_df


def validate_uom_df(uom_df):
    error_codes = {
        'uom-001': 'Missing Unit Name (Name)',
        'uom-002': 'Missing Plural Name, Abbreviation, or Plural Abbreviation',
        'uom-003': 'Conversion Rate is 0 on non-base unit row',
        'uom-004': 'Item has no base unit row (Base Unit = Yes)',
        'uom-005': 'Item has duplicate base unit rows'
    }

    item_errors = {}

    for item_name, group in uom_df.groupby('Item(Type Name)'):
        errors = []

        # Check for blank unit names
        if (group['Unit Name (Name)'] == '').any():
            errors.append('uom-001')

        # Check for blank plural/abbreviation fields
        if (group['Plural Name'] == '').any() or \
           (group['Abbreviation'] == '').any() or \
           (group['Plural Abbreviation'] == '').any():
            errors.append('uom-002')

        # Check for 0 conversion rate on non-base rows
        non_base = group[group['Base Unit'] == 'No']
        if not non_base.empty:
            if (non_base['Conversion Rate(/Base)'].astype(float) == 0).any():
                errors.append('uom-003')

        # Check for missing base unit row
        base_rows = group[group['Base Unit'] == 'Yes']
        if base_rows.empty:
            errors.append('uom-004')

        # Check for duplicate base unit rows
        if len(base_rows) > 1:
            errors.append('uom-005')

        if errors:
            item_errors[item_name] = errors

    rejected_items = set(item_errors.keys())
    valid_df = uom_df[~uom_df['Item(Type Name)'].isin(rejected_items)].copy()

    rejected_df = uom_df[uom_df['Item(Type Name)'].isin(rejected_items)].copy()
    if not rejected_df.empty:
        rejected_df['REJECTION NOTES'] = rejected_df['Item(Type Name)'].map(
            lambda x: '; '.join(error_codes[e] for e in item_errors.get(x, []))
        )

    return valid_df, rejected_df


if __name__ == "__main__":
    ven_code = input('Enter Vendor ID (not case sensitive):  ').upper()

    print('What type of item will you be processing?')
    mpl_type = input('1 for Tile \n2 for Tool\n...')

    if mpl_type == '1':
        mpl_all = et.get_tile_mpl_itshare()
        mpl = mpl_all[mpl_all["VENDOR"] == ven_code].copy()
        print('Tile mpl has been chosen')
    elif mpl_type == '2':
        mpl = et.get_tool_mpl_by_vendor_2(ven_code)
        print('Tool mpl has been chosen')
    else:
        print('1 or 2 must be chosen')
        sys.exit()

    mpl = mpl[mpl['PRICELIST STATUS'] == 'ACTIVE']
    mpl = mpl[mpl['E CODE NETSUITE INTERNAL ID'].isna()]

    # UOM and Unit Mapping
    uom_mapping = et.get_uom_mapping()
    plural_uom_mapping = et.get_plural_uom_mapping()
    sell_unit_mapping = et.get_sell_unit_mapping()
    plural_sell_unit_mapping = et.get_plural_sell_unit_mapping()

    vendor_mapping = et.get_all_vendors()
    vendor = vendor_mapping.get(ven_code)

    class_mapping = et.get_class_mapping()

    # --------------------------- ADD ITEM SECTION -------------------------------------#

    add_item_df = build_add_item_df(
        mpl, mpl_type, vendor, class_mapping,
        uom_mapping, plural_uom_mapping,
        sell_unit_mapping, plural_sell_unit_mapping
    )

    output_folder = os.path.join(SCRIPT_DIR, 'Real Product Add Item Files')
    os.makedirs(output_folder, exist_ok=True)

    output_csv_file = os.path.join(output_folder, ven_code + " ADD ITEM.csv")
    add_item_df.to_csv(output_csv_file, index=False)
    print("Add Item Import file has been created in the '{}' folder.".format(output_folder))

    # ------------------------------- UOM File Section-------------------------------#

    Plural = et.get_unit_plural_mapping()
    Abb = et.get_uom_mapping_abb()
    Plural_Abb = et.get_plural_abb_mapping()

    uom_df = build_uom_df(add_item_df, Plural, Abb, Plural_Abb)
    valid_uom_df, rejected_uom_df = validate_uom_df(uom_df)

    output_folder_2 = os.path.join(SCRIPT_DIR, 'Real Product UOM Files')
    os.makedirs(output_folder_2, exist_ok=True)

    output_csv_file_2 = os.path.join(output_folder_2, ven_code + " UOM.csv")
    valid_uom_df.to_csv(output_csv_file_2, encoding="utf-8", index=False)

    if not rejected_uom_df.empty:
        rejected_folder = os.path.join(SCRIPT_DIR, 'Rejected UOM Files')
        os.makedirs(rejected_folder, exist_ok=True)
        rejected_csv = os.path.join(rejected_folder, ven_code + " REJECTED UOM.csv")
        rejected_uom_df.to_csv(rejected_csv, encoding="utf-8", index=False)
        print("{} product(s) rejected from UOM file. See '{}'".format(
            rejected_uom_df['Item(Type Name)'].nunique(), rejected_csv))
    else:
        print("All products passed UOM validation.")

    # V Code sync file
    sync_mpl = pd.DataFrame({
        'Netsuite E code': mpl['E SKU'],
        'External Id': mpl['V SKU']
    })

    output_folder_3 = os.path.join(SCRIPT_DIR, 'V Code and E code Link')
    os.makedirs(output_folder_3, exist_ok=True)
    output_csv_file_mpl = os.path.join(output_folder_3, "{} V code sync to E code.csv".format(ven_code))
    sync_mpl.to_csv(output_csv_file_mpl, encoding="utf-8", index=False)

    print("UOM Import file has been created in the '{}' folder.".format(output_folder_2))
