import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

ftp = et.ftp_login()

active_tile_vendors = et.tile_vendor_mapping
active_tool_vendors = et.tool_vendor_mapping

output_folder = 'out'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

#-----------------------TILES----------------------------------#
mpl_tile_df = et.get_tile_mpl_ftpserver(ftp)

for ven_code in active_tile_vendors.keys():
    ven_name = et.get_vendor_name(ven_code)
    print(f"Reading in {ven_name} MPL")
    mpl_df = et.get_tile_mpl_ftpserver(ftp)
    mpl_df = mpl_tile_df[mpl_tile_df['VENDOR'] == ven_code].copy()
    mpl_df.set_index('E SKU', inplace=True)
    print("done\n")
    
    print(f"Reading in {ven_name} Image Manifest")
    manifest_df = et.get_image_manifest(ftp, ven_code)
    manifest_df.set_index('E SKU', inplace=True)
    print("done\n")

    print(f"Reading in {ven_name} Shopify Product data")
    prod_df = et.get_current_prod(ftp)
    prod_df.set_index('Variant SKU', inplace=True)
    print("done\n")

    ROOT_URL = f"https://tiledata.net/images/ElitTile_images/{ven_code}"

    m_folders = {
        1: 'm1',
        2: 'm2',
        3: 'm3',
        4: 'm4',
        5: 'm5',
        6: 'm6',
        7: 'm7'
    }

    v_folders = {
        8: 'motion-clip'
    }

    out_data = {
        'ID': [],
        'Command': [],
        'Variant ID': [],
        'Variant Command': [],
        'Image Command': [],
        'Image Src': [],
        'Image Position': [],
        'E SKU': []
    }



    for i, r in mpl_df.iterrows():
        sku = i
        for position, m_folder in m_folders.items():
            try:
                dir_exists = bool(pd.notna(manifest_df.at[i, m_folder]))
            except KeyError as e:
                #print(e)
                continue
            if pd.isna(manifest_df.at[i, m_folder]):
                continue
            img_fn = str(manifest_df.at[i, m_folder])
            img_src = f"{ROOT_URL}/products/{m_folder}/{img_fn}" 

            out_data['ID'].append(r['ID'])
            out_data['Command'].append("MERGE")
            out_data['Variant ID'].append(r['Variant ID'])
            out_data['Variant Command'].append("MERGE")
            out_data['Image Command'].append("REPLACE")
            out_data['Image Src'].append(img_src)
            out_data['Image Position'].append(position)
            out_data['E SKU'].append(sku)

        for position, v_folder in v_folders.items():
            try:
                dir_exists = bool(pd.notna(manifest_df.at[i, v_folder]))
            except KeyError as e:
                #print(e)
                continue
            if pd.isna(manifest_df.at[i, v_folder]):
                continue

            vid_fn = str(manifest_df.at[i, v_folder])
            vid_src = f"{ROOT_URL}/videos/{vid_fn}"

            out_data['ID'].append(r['ID'])
            out_data['Command'].append("MERGE")
            out_data['Variant ID'].append(r['Variant ID'])
            out_data['Variant Command'].append("MERGE")
            out_data['Image Command'].append("REPLACE")
            out_data['Image Src'].append(vid_src)
            out_data['Image Position'].append(position)
            out_data['E SKU'].append(sku)

    out_df = pd.DataFrame(out_data)
    out_file = os.path.join(output_folder, f'{ven_code}-image_import.xlsx')
    out_df.to_excel(out_file, sheet_name="Products", index=None)
    print(f"Created {out_file}")


#-----------------------TOOLS----------------------------------#

for ven_code in active_tool_vendors.keys():
    ven_name = et.get_vendor_name(ven_code)
    print(f"Reading in {ven_name} MPL")
    mpl_df = et.get_tool_mpl_by_vendor(ftp, ven_code)
    mpl_df.set_index('E SKU', inplace=True)
    print("done\n")
    
    print(f"Reading in {ven_name} Image Manifest")
    manifest_df = et.get_image_manifest(ftp, ven_code)
    manifest_df.set_index('E SKU', inplace=True)
    print("done\n")

    print(f"Reading in {ven_name} Shopify Product data")
    prod_df = et.get_current_prod(ftp)
    prod_df.set_index('Variant SKU', inplace=True)
    print("done\n")

    ROOT_URL = f"https://tiledata.net/images/ElitTile_images/{ven_code}"

    m_folders = {
        1: 'm1',
        2: 'm2',
        3: 'm3',
        4: 'm4',
        5: 'm5',
        6: 'm6',
        7: 'm7'
    }

    v_folders = {
        8: 'motion-clip'
    }

    out_data = {
        'ID': [],
        'Command': [],
        'Variant ID': [],
        'Variant Command': [],
        'Image Command': [],
        'Image Src': [],
        'Image Position': [],
        'E SKU': []
    }



    for i, r in mpl_df.iterrows():
        sku = i
        for position, m_folder in m_folders.items():
            try:
                dir_exists = bool(pd.notna(manifest_df.at[i, m_folder]))
            except KeyError as e:
                #print(e)
                continue
            if pd.isna(manifest_df.at[i, m_folder]):
                continue
            img_fn = str(manifest_df.at[i, m_folder])
            img_src = f"{ROOT_URL}/products/{m_folder}/{img_fn}" 

            out_data['ID'].append(r['ID'])
            out_data['Command'].append("MERGE")
            out_data['Variant ID'].append(r['Variant ID'])
            out_data['Variant Command'].append("MERGE")
            out_data['Image Command'].append("REPLACE")
            out_data['Image Src'].append(img_src)
            out_data['Image Position'].append(position)
            out_data['E SKU'].append(sku)

        for position, v_folder in v_folders.items():
            try:
                dir_exists = bool(pd.notna(manifest_df.at[i, v_folder]))
            except KeyError as e:
                #print(e)
                continue
            if pd.isna(manifest_df.at[i, v_folder]):
                continue

            vid_fn = str(manifest_df.at[i, v_folder])
            vid_src = f"{ROOT_URL}/videos/{vid_fn}"

            out_data['ID'].append(r['ID'])
            out_data['Command'].append("MERGE")
            out_data['Variant ID'].append(r['Variant ID'])
            out_data['Variant Command'].append("MERGE")
            out_data['Image Command'].append("REPLACE")
            out_data['Image Src'].append(vid_src)
            out_data['Image Position'].append(position)
            out_data['E SKU'].append(sku)

    out_df = pd.DataFrame(out_data)
    out_file = os.path.join(output_folder, f'{ven_code}-image_import.xlsx')
    out_df.to_excel(out_file, sheet_name="Products", index=None)
    print(f"Created {out_file}")

print("Program completes successfully")
