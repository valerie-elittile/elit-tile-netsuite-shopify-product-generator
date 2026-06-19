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

output_folder_real_mapping = 'real product mapping'
os.makedirs(output_folder_real_mapping, exist_ok=True)

ven_code = input('Enter vendor code(not case sensitive): ').upper()

vendor = active_tile_vendors.get(ven_code)

mpl_all = et.get_tile_mpl_ftpserver(ftp)
mpl = mpl_all[mpl_all["VENDOR"] == ven_code].copy()

mpl_for_sample = mpl[(mpl['HAS CUT SAMPLE'] == 'YES') & (mpl['PRICELIST STATUS'] == 'ACTIVE')]
mpl_for_sample = mpl_for_sample.reset_index(drop=True)

sample_data = {
    'Image Command': [],
    'Image Src': [],
    'Image Position': [],
    'Parent SKU': [],
    'ID': [],
    'Handle': [],
    'Title': [],
    'Status': [],
    'Variant SKU': [],
    'Variant Inventory Item ID': [],
    'Variant ID': [],
    'Variant Weight': [],
    'Variant Price': [],
    'Variant Cost': [],
    'Variant Metafield: pricelist.class [single_line_text_field]': [],
    'Template Suffix': [],
    'Command': [],
    'Vendor': [],
    'Type': [],
    'Published': [],
    'Published Scope': [],
    'Variant Command': [],
    'Variant Weight Unit': [],
    'Variant Taxable': [],
    'Variant Inventory Policy': [],
    'Variant Fulfillment Service': [],
    'Variant Requires Shipping': [],
    'Variant Shipping Profile': [],
    'Metafield: custom.parent_product [product_reference]': [],
    'Metafield: seo.hidden [number_integer]': [],
    'Inventory Available: Elit Tile - North Hollywood': [],
    'Inventory Available: Elit Tile - Los Angeles': []
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
    'Variant Shipping Profile',
    'Metafield: custom.parent_product [product_reference]',
    'Metafield: seo.hidden [number_integer]',
    'Image Command',
    'Image Src',
    'Image Position',
    'Parent SKU',
    'Inventory Available: Elit Tile - North Hollywood',
    'Inventory Available: Elit Tile - Los Angeles'
]

real_data = {
    'ID': [],
    'Command': [],
    'Metafield: sample.sku [single_line_text_field]': [],
    'Metafield: custom.sample_product [product_reference]': []
}

manifest_df = et.get_image_manifest(ftp,ven_code)

manifest_df.set_index('E SKU', inplace=True)

ROOT_URL = f"https://tiledata.net/images/ElitTile_images/{ven_code}"

m_folders = {1: 'm1', 3: 'm3'}
sheet_name = "Products"


#--------------------------------Cut Samples----------------------------------------#

# Populate sample_data using the loop
for i, r in mpl_for_sample.iterrows():
    sku = r['E SKU']
    if sku not in manifest_df.index:
        print(f"SKU {sku} not found in manifest_df")
        continue
    found_image = False
    for position, m_folder in m_folders.items():
        try:
            if pd.isna(manifest_df.at[sku, m_folder]):
                print(f"No data for SKU {sku} in folder {m_folder}")
                continue
            else:
                img_fn = str(manifest_df.at[sku, m_folder])
                img_src = f"{ROOT_URL}/products/{m_folder}/{img_fn}"

                sample_data['Image Command'].append("REPLACE")
                sample_data['Image Src'].append(img_src)
                sample_data['Image Position'].append(position)
                sample_data['Parent SKU'].append(sku)
                sample_data['ID'].append('')
                sample_data['Handle'].append(r['E SKU'].lower() + "-s")
                sample_data['Title'].append('SAMPLE - ' + r['SHOPIFY NAME'])
                sample_data['Status'].append("Draft")
                sample_data['Variant SKU'].append(r['E SKU'] + '-S')
                sample_data['Variant Inventory Item ID'].append('')
                sample_data['Variant ID'].append('')
                sample_data['Variant Weight'].append('1')
                sample_data['Variant Price'].append(0)
                sample_data['Variant Cost'].append(0)
                sample_data['Variant Metafield: pricelist.class [single_line_text_field]'].append('SAMPLE')
                sample_data['Template Suffix'].append('sample-noform')
                sample_data['Command'].append('MERGE')
                sample_data['Vendor'].append(vendor)
                sample_data['Type'].append('Building Materials')
                sample_data['Published'].append('FALSE')
                sample_data['Published Scope'].append('web')
                sample_data['Variant Command'].append('MERGE')
                sample_data['Variant Weight Unit'].append('lb')
                sample_data['Variant Taxable'].append('TRUE')
                sample_data['Variant Inventory Policy'].append('deny')
                sample_data['Variant Fulfillment Service'].append('manual')
                sample_data['Variant Requires Shipping'].append('TRUE')
                sample_data['Variant Shipping Profile'].append('Sample Products')
                sample_data['Metafield: custom.parent_product [product_reference]'].append(r['Handle'])
                sample_data['Metafield: seo.hidden [number_integer]'].append(1)
                sample_data['Inventory Available: Elit Tile - North Hollywood'].append('Stocked')
                sample_data['Inventory Available: Elit Tile - Los Angeles'].append('Stocked')
                found_image = True
                break  
        except Exception as e:
            print(f"Error for SKU {sku}: {e}")
            continue
    if not found_image:
        print(f"No data for SKU {sku} in folders {list(m_folders.values())}")

# for key, value in sample_data.items():
#     print(key, len(value))

sample_df = pd.DataFrame(sample_data)

sample_df = sample_df.reindex(columns=column_order)

# Define a dictionary to specify the data type for each column
dtype_dict = {col: str for col in sample_df.columns}

# Fill NaN values with empty strings using the specified data types
sample_df = sample_df.fillna('', inplace=False).astype(dtype_dict)

output_cut_sample = os.path.join(output_folder_cut, ven_code + ' Shopify Cut Sample Import.xlsx')

sample_df.to_excel(output_cut_sample, index=False, sheet_name=sheet_name)

print(f'Import Sample Excel File has been created in the {output_folder_cut} folder for {vendor}')


#------------------------------------Create import file to map real product to sample--------------------------------------#

for i,r in mpl_for_sample.iterrows():
    sku = r['E SKU']
    handle = r['E SKU'].lower() + "-s"

    sample_row = sample_df[sample_df['Parent SKU'] == sku]

    if not sample_row.empty:
        real_data['ID'].append(r['ID'])
        real_data['Command'].append('MERGE')
        real_data['Metafield: sample.sku [single_line_text_field]'].append(sample_row['Variant SKU'].values[0])
        real_data['Metafield: custom.sample_product [product_reference]'].append(sample_row['Handle'].values[0])
    else:
        print(f"No sample data found for SKU: {sku}")

# Convert real_data into a dataframe

real_df = pd.DataFrame(real_data)

real_df = real_df.fillna('', inplace=False)

output_real_mapping = os.path.join(output_folder_real_mapping, ven_code + ' Shopify Real Product Mapping.xlsx')

real_df.to_excel(output_real_mapping, index=False, sheet_name=sheet_name)

print(f'Import Real Product Mapping to Sample has been created in the {output_real_mapping} folder for {vendor}')
