import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

active_tile_vendors = et.tile_vendor_mapping
active_tool_vendors = et.tool_vendor_mapping

output_folder = os.path.join(SCRIPT_DIR, 'out')
os.makedirs(output_folder, exist_ok=True)

#----------------------------USER SELECTION-------------------------------------#
print("\n" + "="*60)
print("IMAGE IMPORT CREATOR")
print("="*60)

category_choice = input("\nWhat do you want to process?\n1. Tile\n2. Tool\n3. All\n\nEnter your choice (1, 2, or 3): ").strip()

selected_tile_vendors = {}
selected_tool_vendors = {}

if category_choice == "1":
    vendor_choice = input("\nProcess all tile vendors or one?\n1. All tile vendors\n2. One tile vendor\n\nEnter your choice (1 or 2): ").strip()
    if vendor_choice == "2":
        print("\nAvailable tile vendors:")
        for ven_code in active_tile_vendors.keys():
            print(f"  {ven_code}")
        pick = input("\nEnter the vendor code (e.g., E0164): ").strip().upper()
        if pick in active_tile_vendors:
            selected_tile_vendors = {pick: active_tile_vendors[pick]}
            print(f"\nProcessing tile vendor: {pick}")
        else:
            print(f"ERROR: '{pick}' not found in tile vendors. Processing all tile vendors instead.")
            selected_tile_vendors = active_tile_vendors.copy()
    else:
        selected_tile_vendors = active_tile_vendors.copy()
        print("\nProcessing all tile vendors...")

elif category_choice == "2":
    vendor_choice = input("\nProcess all tool vendors or one?\n1. All tool vendors\n2. One tool vendor\n\nEnter your choice (1 or 2): ").strip()
    if vendor_choice == "2":
        print("\nAvailable tool vendors:")
        for ven_code in active_tool_vendors.keys():
            print(f"  {ven_code}")
        pick = input("\nEnter the vendor code (e.g., E0991): ").strip().upper()
        if pick in active_tool_vendors:
            selected_tool_vendors = {pick: active_tool_vendors[pick]}
            print(f"\nProcessing tool vendor: {pick}")
        else:
            print(f"ERROR: '{pick}' not found in tool vendors. Processing all tool vendors instead.")
            selected_tool_vendors = active_tool_vendors.copy()
    else:
        selected_tool_vendors = active_tool_vendors.copy()
        print("\nProcessing all tool vendors...")

elif category_choice == "3":
    selected_tile_vendors = active_tile_vendors.copy()
    selected_tool_vendors = active_tool_vendors.copy()
    print("\nProcessing all vendors...")

else:
    print("Invalid choice. Processing all vendors instead.")
    selected_tile_vendors = active_tile_vendors.copy()
    selected_tool_vendors = active_tool_vendors.copy()

ftp = et.ftp_login()

prod_df = et.get_current_prod(ftp)
prod_df.set_index('Variant SKU', inplace=True)

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

def process_vendor(ven_code, mpl_df):
    ven_name = et.get_vendor_name(ven_code)

    mpl_df.set_index('E SKU', inplace=True)

    print(f"Reading in {ven_name} Image Manifest")
    manifest_df = et.get_image_manifest(ftp, ven_code)
    manifest_df.set_index('E SKU', inplace=True)
    print("done\n")

    ROOT_URL = f"https://tiledata.net/images/ElitTile_images/{ven_code}"

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
            except KeyError:
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
            except KeyError:
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

#-----------------------TILES----------------------------------#
if selected_tile_vendors:
    mpl_tile_df = et.get_tile_mpl_ftpserver(ftp)
    for ven_code in selected_tile_vendors.keys():
        ven_name = et.get_vendor_name(ven_code)
        print(f"Reading in {ven_name} MPL")
        mpl_df = mpl_tile_df[mpl_tile_df['VENDOR'] == ven_code].copy()
        print("done\n")
        process_vendor(ven_code, mpl_df)

#-----------------------TOOLS----------------------------------#
if selected_tool_vendors:
    mpl_tool_df = et.get_tool_mpl_ftpserver(ftp)
    for ven_code in selected_tool_vendors.keys():
        ven_name = et.get_vendor_name(ven_code)
        print(f"Reading in {ven_name} MPL")
        mpl_df = mpl_tool_df[mpl_tool_df['VENDOR'] == ven_code].copy()
        print("done\n")
        process_vendor(ven_code, mpl_df)

print("Program completes successfully")
