import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ftp = et.ftp_login()

active_tile_vendors = et.get_tile_vendors()

output_folder_cut = os.path.join(SCRIPT_DIR, 'Sample Product Add Item Files')
os.makedirs(output_folder_cut, exist_ok=True)

output_folder_cut_uom = os.path.join(SCRIPT_DIR, 'Sample Product UOM Files')
os.makedirs(output_folder_cut_uom, exist_ok=True)

output_folder_v = os.path.join(SCRIPT_DIR, 'V Code Sample Product Add Item Files')
os.makedirs(output_folder_v, exist_ok=True)

output_folder_v_uom = os.path.join(SCRIPT_DIR, 'V Code Sample Product UOM Files')
os.makedirs(output_folder_v_uom, exist_ok=True)

ven_code = input('Enter vendor code(not case sensitive): ').upper()

# Check if vendor is E0207 and display warning
if ven_code == 'E0207':
    print("\n" + "="*70)
    print("WARNING: E0207 does not have automatic samples")
    print("Samples should only be created if instructed by managers")
    print("="*70 + "\n")
    user_choice = input("Do you want to continue creating samples for E0207? (yes/no): ").lower().strip()
    if user_choice not in ['yes', 'y']:
        print("Sample creation cancelled.")
        sys.exit()
    print()

active_retail_vendor = et.get_retail_vendor_mapping()
retail_vendor = active_retail_vendor.get(ven_code)

vendor = active_tile_vendors.get(ven_code)

mpl_all = et.get_tile_mpl_itshare()
mpl = mpl_all[mpl_all["VENDOR"] == ven_code].copy()

mpl_for_sample = mpl[(mpl['HAS CUT SAMPLE'] == 'YES') & (mpl['PRICELIST STATUS'] == 'ACTIVE')]
mpl_for_sample = mpl_for_sample.reset_index(drop=True)

# Create Dictionaries with each columns as lists

sample_data = {

    "E SKU": [],
    "NetSuite V Sample": [],
    "External ID": [],
    "itemid": [],
    "Item Color": [],
    "Item Size": [],
    "costcategory": [],
    "atpmethod": [],
    "Vendor": [],
    "Subsidiary": [],
    "Tax Schedule": [],
    "Display Name/Code": [],
    "HANDLE SHOPIFY": [],
    "ID": [],
    "Item Name": [],
    "Item Name/Number (Req)": [],
    "Item Weight": [],
    "Location": [],
    "Primary Purchase Unit": [],
    "Primary Sale Unit": [],
    "Primary Stock Unit": [],
    "Purchase Price": [],
    "itemPriceLine1_itemPriceTypeRef": [],
    "itemPriceLine1_itemPrice": [],
    "itemPriceLine1_quantityPricing": [],
    "vendor1_subsidiary": [],
    "vendor1_preferred": [],
    "vendor1_purchaseprice": [],
    "isdropship":[]

}

uom_data = {
    'Item(Type Name)': [],
    'Internal ID*Update Only': [],
    'Unit Name': [],
    'Plural Name': [],
    'Abbreviation': [],
    'Plural Abbreviation': [],
    'Conversion Rate(/Base)': [],
    'Base Unit': []
}

v_sample_data = {

    "V SKU": [],
    "NetSuite E Sample": [],
    "External ID": [],
    "itemid": [],
    "Item Color": [],
    "Item Size": [],
    "Vendor Code": [],
    "Sales Description": [],
    "costcategory": [],
    "atpmethod": [],
    "Subsidiary": [],
    "Tax Schedule": [],
    "Display Name/Code": [],
    "HANDLE SHOPIFY": [],
    "ID": [],
    "Item Name": [],
    "Item Name/Number (Req)": [],
    "Item Weight": [],
    "Location": [],
    "Primary Purchase Unit": [],
    "Primary Sale Unit": [],
    "Primary Stock Unit": [],
    "Purchase Price": [],
    "itemPriceLine1_itemPriceTypeRef": [],
    "itemPriceLine1_itemPrice": [],
    "itemPriceLine1_quantityPricing": [],
    "vendor1_name": [],
    "vendor1_subsidiary": [],
    "vendor1_preferred": [],
    "vendor1_purchaseprice": [],
    "vendor1_code": [],
    "vendor2_name": [],
    "vendor2_subsidiary": [],
    "vendor2_preferred": [],
    "vendor2_purchaseprice": [],
    "vendor2_code": []

}

v_uom_data = {
    'Item(Type Name)': [],
    'Internal ID*Update Only': [],
    'Unit Name': [],
    'Plural Name': [],
    'Abbreviation': [],
    'Plural Abbreviation': [],
    'Conversion Rate(/Base)': [],
    'Base Unit': []
}

#-----------------------------Code Starts Here--------------------------------------#

# Populate Sample data using a loop

for i, r in mpl_for_sample.iterrows():
    sku = r['E SKU']

    sample_data['E SKU'].append(sku)
    sample_data['NetSuite V Sample'].append(r['V SKU'] + "-S")
    sample_data['External ID'].append(r['E SKU'] + "-S")
    sample_data['itemid'].append(r['E SKU'] + "-S")
    sample_data['Item Color'].append(r['COLOR'])
    sample_data['Item Size'].append(r['SIZE'].upper())
    sample_data['costcategory'].append('Default Cost Category')
    sample_data['atpmethod'].append('Cumulative ATP with Look Ahead')
    sample_data['Vendor'].append('E0002 ELIT TILE LA')
    sample_data['Subsidiary'].append('Elit Tile Consolidated : ElitTile.com')
    sample_data['Tax Schedule'].append('Non-Taxable')
    sample_data['Display Name/Code'].append("SAMPLE - " + r['SHOPIFY NAME'].upper())
    sample_data['HANDLE SHOPIFY'].append(r['E SKU'].lower() + "-s")
    sample_data['ID'].append('')
    sample_data['Item Name'].append("SAMPLE - " + r['SHOPIFY NAME'].upper())
    sample_data['Item Name/Number (Req)'].append(r['E SKU'] + "-S" + " SAMPLE - " + r['SHOPIFY NAME'].upper())
    sample_data['Item Weight'].append("1")
    sample_data['Location'].append('LA ElitTile.com')
    sample_data['Primary Purchase Unit'].append('')
    sample_data['Primary Sale Unit'].append('')
    sample_data['Primary Stock Unit'].append('')
    sample_data['Purchase Price'].append('0')
    sample_data['itemPriceLine1_itemPriceTypeRef'].append('BASE PRICE')
    sample_data['itemPriceLine1_itemPrice'].append('0')
    sample_data['itemPriceLine1_quantityPricing'].append('0')
    sample_data['vendor1_subsidiary'].append(10)
    sample_data['vendor1_preferred'].append('T')
    sample_data['vendor1_purchaseprice'].append(0)
    sample_data['isdropship'].append('T')

# Create DataFrame, convert to csv, add to output folder

sample_df = pd.DataFrame(sample_data)

# Define a dictionary to specify the data type for each column
dtype_dict = {col: str for col in sample_df.columns}

# Fill NaN values with empty strings using the specified data types
sample_df = sample_df.fillna('', inplace=False).astype(dtype_dict)

output_cut_sample = os.path.join(output_folder_cut, ven_code + ' SAMPLE ADD ITEM.csv')

sample_df.to_csv(output_cut_sample, index=False)

print(f'Sample Add Item file has been created in the {output_folder_cut} for {vendor}')

#---------------------------------------------------------------SAMPLE UOM------------------------------------------------------------------#

# Populate uom_data using a for loop

for i, r in sample_df.iterrows():

    uom_data['Item(Type Name)'].append(r['External ID'])
    uom_data['Internal ID*Update Only'].append('')
    uom_data['Unit Name'].append('EACH')
    uom_data['Plural Name'].append('EACH')
    uom_data['Abbreviation'].append('EA')
    uom_data['Plural Abbreviation'].append('EA')
    uom_data['Conversion Rate(/Base)'] = '1'
    uom_data['Base Unit'] = 'Yes'

# Create DataFrame, convert to csv, add to output folder

uom_df = pd.DataFrame(uom_data)

output_cut_uom = os.path.join(output_folder_cut_uom, ven_code + ' SAMPLE UOM.csv')

uom_df.to_csv(output_cut_uom, index=False)

print(f'Sample UOM file has been created in the {output_folder_cut_uom} for {vendor}')

#------------------------------V Code Sample------------------------------------------------#

for i, r in mpl_for_sample.iterrows():
    sku = r['V SKU']

    v_sample_data['V SKU'].append(sku)
    v_sample_data['NetSuite E Sample'].append(r['E SKU'] + "-S")
    v_sample_data['External ID'].append(r['V SKU'] + "-S")
    v_sample_data['itemid'].append(r['V SKU'] + "-S")
    v_sample_data['Item Color'].append(r['COLOR'])
    v_sample_data['Item Size'].append(r['SIZE'].upper())
    v_sample_data['Vendor Code'].append(r['VENDOR ITEM CODE'] if pd.notna(r['VENDOR ITEM CODE']) else '')
    parts = []

    if pd.notna(r['EA/BX']):
        parts.append(f"{r['EA/BX']} EA/BX")
    if pd.notna(r['SF/EA']):
        parts.append(f"{r['SF/EA']} SF/EA")
    if pd.notna(r['SF/BX']):
        parts.append(f"{r['SF/BX']} SF/BX")

    v_sample_data['Sales Description'].append(' '.join(parts))

    v_sample_data['costcategory'].append('Default Cost Category')
    v_sample_data['atpmethod'].append('Cumulative ATP with Look Ahead')
    v_sample_data['Subsidiary'].append('Elit Tile Consolidated : Elit Tile Corp (LA)|Elit Tile Consolidated : International Tile and Stone Inc. (noho)')
    v_sample_data['Tax Schedule'].append('Non-Taxable')
    v_sample_data['Display Name/Code'].append("SAMPLE - " + r['SHOPIFY NAME'].upper())
    v_sample_data['HANDLE SHOPIFY'].append(r['E SKU'].lower() + "-s")
    v_sample_data['ID'].append('')
    v_sample_data['Item Name'].append("SAMPLE - " + r['SHOPIFY NAME'].upper())
    v_sample_data['Item Name/Number (Req)'].append(r['V SKU'] + "-S" + " SAMPLE - " + r['SHOPIFY NAME'].upper())
    v_sample_data['Item Weight'].append("1")
    v_sample_data['Location'].append('')
    v_sample_data['Primary Purchase Unit'].append('')
    v_sample_data['Primary Sale Unit'].append('')
    v_sample_data['Primary Stock Unit'].append('')
    v_sample_data['Purchase Price'].append('0')
    v_sample_data['itemPriceLine1_itemPriceTypeRef'].append('BASE PRICE')
    v_sample_data['itemPriceLine1_itemPrice'].append('0')
    v_sample_data['itemPriceLine1_quantityPricing'].append('0')
    v_sample_data['vendor1_name'].append(retail_vendor)
    v_sample_data['vendor1_subsidiary'].append(3)
    v_sample_data['vendor1_preferred'].append('T')
    v_sample_data['vendor1_purchaseprice'].append(0)
    v_sample_data['vendor1_code'].append(r['VENDOR ITEM CODE'] if pd.notna(r['VENDOR ITEM CODE']) else '')
    v_sample_data['vendor2_name'].append(retail_vendor)
    v_sample_data['vendor2_subsidiary'].append(4)
    v_sample_data['vendor2_preferred'].append('T')
    v_sample_data['vendor2_purchaseprice'].append(0)
    v_sample_data['vendor2_code'].append(r['VENDOR ITEM CODE'] if pd.notna(r['VENDOR ITEM CODE']) else '')

# Create DataFrame, convert to csv, add to output folder

v_sample_df = pd.DataFrame(v_sample_data)

# Define a dictionary to specify the data type for each column
dtype_dict = {col: str for col in sample_df.columns}

output_v_sample = os.path.join(output_folder_v, retail_vendor + ' SAMPLE ADD ITEM.csv')

v_sample_df.to_csv(output_v_sample, index=False)

print(f'Sample Add Item file has been created in the {output_folder_v} for {retail_vendor}')

#-----------------------------------------V Code UOM-----------------------------------------------#

# Populate uom_data using a for loop

for i, r in v_sample_df.iterrows():

    v_uom_data['Item(Type Name)'].append(r['External ID'])
    v_uom_data['Internal ID*Update Only'].append('')
    v_uom_data['Unit Name'].append('EACH')
    v_uom_data['Plural Name'].append('EACH')
    v_uom_data['Abbreviation'].append('EA')
    v_uom_data['Plural Abbreviation'].append('EA')
    v_uom_data['Conversion Rate(/Base)'] = '1'
    v_uom_data['Base Unit'] = 'Yes'

# Create DataFrame, convert to csv, add to output folder

v_uom_df = pd.DataFrame(v_uom_data)

output_v_uom = os.path.join(output_folder_v_uom, retail_vendor + ' SAMPLE UOM.csv')

v_uom_df.to_csv(output_v_uom, index=False)

print(f'Sample UOM file has been created in the {output_folder_v_uom} for {retail_vendor}')
