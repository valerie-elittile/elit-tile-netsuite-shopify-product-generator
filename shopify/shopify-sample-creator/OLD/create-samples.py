import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

ftp = et.ftp_login()

active_tile_vendors = et.get_tile_vendors()


output_folder_cut = 'cut samples out'
os.makedirs(output_folder_cut, exist_ok=True)

output_folder_fs = 'fs samples out'
os.makedirs(output_folder_fs, exist_ok=True)

ven_code = input('Enter vendor code(not case sensitive): ').upper()

vendor = active_tile_vendors.get(ven_code)

mpl = et.get_tile_mpl_by_vendor(ftp,ven_code)

mpl_for_sample = mpl[(mpl['HAS CUT SAMPLE'] == 'YES') & (mpl['PRICELIST STATUS'] == 'ACTIVE')]
mpl_for_sample = mpl_for_sample.reset_index(drop=True)


mpl_for_fs = mpl[(mpl['HAS FULL SIZE SAMPLE'] == 'YES') & (mpl['PRICELIST STATUS'] == 'ACTIVE')]
mpl_for_fs = mpl_for_fs.reset_index(drop=True)

sample_data = {
    'Parent SKU':[],
    'Image Command':[],
    'Image Src':[],
    'Image Position':[],

}

fs_data = {
    'Parent SKU':[],
    'Image Command':[],
    'Image Src':[],
    'Image Position':[],

}

column_order = [
    'ID',
    'Handle',
    'Title',
    'Status',
    'Variant SKU',
    'Variant Inventory Item ID',
    'Variant ID',
    'Variant Weight',
    'Variant Price',
    'Variant Cost',
    'Variant Metafield: pricelist.class [single_line_text_field]',
    'Template Suffix',
    'Command',
    'Vendor',
    'Type',
    'Published',
    'Published Scope',
    'Variant Command',
    'Variant Weight Unit',
    'Variant Taxable',
    'Variant Inventory Policy',
    'Variant Fulfillment Service',
    'Variant Requires Shipping',
    'Metafield: custom.parent_product [product_reference]',
    'Metafield: seo.hidden [number_integer]',
    'Image Command',
    'Image Src',
    'Image Position',
    'Parent SKU'
]

manifest_df = et.get_image_manifest(ftp,ven_code)

manifest_df.set_index('E SKU', inplace=True)

ROOT_URL = f"https://tiledata.net/images/ElitTile_images/{ven_code}"

m_folders = {1: 'm1'}

sheet_name = "Products"


#--------------------------------Cut Samples----------------------------------------#

# Populate sample_data using the loop
for i, r in mpl_for_sample.iterrows():
    sku = r['E SKU']
    if sku not in manifest_df.index:
        print(f"SKU {sku} not found in manifest_df")
        continue
    for position, m_folder in m_folders.items():
        try:
            dir_exists = bool(pd.notna(manifest_df.at[sku, m_folder]))
        except KeyError as e:
            print(f"KeyError for SKU {sku}: {e}")
            continue
        
        if pd.isna(manifest_df.at[sku, m_folder]):
            print(f"No data for SKU {sku} in folder {m_folder}")
            continue

        img_fn = str(manifest_df.at[sku, m_folder])
        img_src = f"{ROOT_URL}/products/{m_folder}/{img_fn}"

        sample_data['Image Command'].append("REPLACE")
        sample_data['Image Src'].append(img_src)
        sample_data['Image Position'].append(position)
        sample_data['Parent SKU'].append(sku)



sample_df = pd.DataFrame(sample_data)

sample_df['ID'] = ''
sample_df['Handle'] = mpl_for_sample['E SKU'].str.lower() + "-s"
sample_df['Title'] = 'SAMPLE - ' + mpl_for_sample['SHOPIFY NAME']
sample_df['Status'] = "Draft"
sample_df['Variant SKU'] = mpl_for_sample['E SKU'] + '-S'
sample_df['Variant Inventory Item ID'] = ''
sample_df['Variant ID'] = ''
sample_df['Variant Weight'] = '1'
sample_df['Variant Price'] = 0
sample_df['Variant Cost'] = 0
sample_df['Variant Metafield: pricelist.class [single_line_text_field]'] = 'SAMPLE'
sample_df['Template Suffix'] = 'sample-noform'
sample_df['Command'] = 'MERGE'
sample_df['Vendor'] = vendor
sample_df['Type'] = 'Building Materials'
sample_df['Published'] = 'FALSE'
sample_df['Published Scope'] = 'web'
sample_df['Variant Command'] = 'MERGE'
sample_df['Variant Weight Unit'] = 'lb'
sample_df['Variant Taxable'] = 'TRUE'
sample_df['Variant Inventory Policy'] = 'deny'
sample_df['Variant Fulfillment Service'] = 'manual'
sample_df['Variant Requires Shipping'] = 'TRUE'
sample_df['Metafield: custom.parent_product [product_reference]'] = mpl_for_sample['HANDLE']
sample_df['Metafield: seo.hidden [number_integer]'] = 1

sample_df = sample_df.reindex(columns=column_order)

# Define a dictionary to specify the data type for each column
dtype_dict = {col: str for col in sample_df.columns}

# Fill NaN values with empty strings using the specified data types
sample_df = sample_df.fillna('', inplace=False).astype(dtype_dict)

output_cut_sample = os.path.join(output_folder_cut, ven_code + ' Shopify Cut Sample Import.xlsx')

sample_df.to_excel(output_cut_sample, index=False, sheet_name=sheet_name)

print(f'Import Sample Excel File has been created in the {output_folder_cut} folder for {vendor}')

#--------------------------------------Full Size---------------------------------------------#

# Populate fs_data using the loop
for i, r in mpl_for_fs.iterrows():
    sku = r['E SKU']
    if sku not in manifest_df.index:
        print(f"SKU {sku} not found in manifest_df")
        continue
    for position, m_folder in m_folders.items():
        try:
            dir_exists = bool(pd.notna(manifest_df.at[sku, m_folder]))
        except KeyError as e:
            print(f"KeyError for SKU {sku}: {e}")
            continue
        
        if pd.isna(manifest_df.at[sku, m_folder]):
            print(f"No data for SKU {sku} in folder {m_folder}")
            continue

        img_fn = str(manifest_df.at[sku, m_folder])
        img_src = f"{ROOT_URL}/products/{m_folder}/{img_fn}"

        fs_data['Image Command'].append("REPLACE")
        fs_data['Image Src'].append(img_src)
        fs_data['Image Position'].append(position)
        fs_data['Parent SKU'].append(sku)

# Create fs_sample_df with the same index as mpl_for_fs
fs_sample_df = pd.DataFrame(fs_data, index=mpl_for_fs.index)

# Add additional columns
fs_sample_df['ID'] = ''
fs_sample_df['Handle'] = mpl_for_fs['E SKU'].str.lower() + "-fs"
fs_sample_df['Title'] = 'FULL SIZE SAMPLE - ' + mpl_for_fs['SHOPIFY NAME']
fs_sample_df['Status'] = "Draft"
fs_sample_df['Variant SKU'] = mpl_for_fs['E SKU'] + '-FS'
fs_sample_df['Variant Inventory Item ID'] = ''
fs_sample_df['Variant ID'] = ''
fs_sample_df['Variant Weight'] = 'PLACEHOLDER' # CHANGE THIS WHEN WE GET THE DATA---------------------------------------------XXXX
fs_sample_df['Variant Price'] = 'PLACEHOLDER' # CHANGE THIS WHEN WE GET THE DATA---------------------------------------------XXXX
fs_sample_df['Variant Cost'] = 'PLACEHOLDER' # CHANGE THIS WHEN WE GET THE DATA---------------------------------------------XXXX
fs_sample_df['Variant Metafield: pricelist.class [single_line_text_field]'] = 'SAMPLE'
fs_sample_df['Template Suffix'] = 'sample-noform'
fs_sample_df['Command'] = 'MERGE'
fs_sample_df['Vendor'] = vendor
fs_sample_df['Type'] = 'Building Materials'
fs_sample_df['Published'] = 'FALSE'
fs_sample_df['Published Scope'] = 'web'
fs_sample_df['Variant Command'] = 'MERGE'
fs_sample_df['Variant Weight Unit'] = 'lb'
fs_sample_df['Variant Taxable'] = 'TRUE'
fs_sample_df['Variant Inventory Policy'] = 'deny'
fs_sample_df['Variant Fulfillment Service'] = 'manual'
fs_sample_df['Variant Requires Shipping'] = 'TRUE'
fs_sample_df['Metafield: custom.parent_product [product_reference]'] = mpl_for_fs['HANDLE']
fs_sample_df['Metafield: seo.hidden [number_integer]'] = 1

fs_sample_df = fs_sample_df.reindex(columns=column_order)

# Define a dictionary to specify the data type for each column
dtype_dict = {col: str for col in fs_sample_df.columns}

# Fill NaN values with empty strings using the specified data types
fs_sample_df = fs_sample_df.fillna('', inplace=False).astype(dtype_dict)

output_cut_sample = os.path.join(output_folder_fs, ven_code + ' Shopify Fullsize Sample Import.xlsx')

fs_sample_df.to_excel(output_cut_sample, index=False, sheet_name=sheet_name)

print(f'Import Sample Excel File has been created in the {output_folder_fs} folder for {vendor}')