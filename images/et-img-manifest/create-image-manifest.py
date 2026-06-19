import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

def pwd(ftp):
    print(f"Changing directory to {ftp.pwd()}")

SKU_PATTERN = et.SKU_PATTERN

OUT_DIR = ".\\out\\"

ACTIVE_TILE_VENDORS = et.get_tile_vendors()
ACTIVE_TOOL_VENDORS = et.get_tool_vendors()

## Create sub-directories if non-existent
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)
    print(f"Created {OUT_DIR}")
else:
    print(f"{OUT_DIR} already exists")

   ## Connect to FTP server
ftp = et.ftp_login()
print(f"Sucessfully logged into to ftp server")
root = ftp.pwd()
pwd(ftp)

## Load current data files from FTP server
print("Loading datafiles..")

vendor_dfs = {}

mpl_tile_df = et.get_tile_mpl_ftpserver(ftp)

ven_codes = ACTIVE_TILE_VENDORS.keys()
for ven_code in ven_codes:
    #mpl_df = et.get_tile_mpl_by_vendor(ftp, ven_code)
    mpl_df = mpl_tile_df[mpl_tile_df['VENDOR'] == ven_code].copy()
    vendor_dfs[ven_code] = mpl_df[['E SKU', 'VENDOR ITEM CODE', 'ID', 'SERIES', 'COLOR', 'SIZE', 'FINISH', 'PRICELIST STATUS']].copy()
    vendor_dfs[ven_code].set_index('E SKU', inplace=True)

ven_codes = ACTIVE_TOOL_VENDORS.keys()
for ven_code in ven_codes:
    mpl_df = et.get_tool_mpl_by_vendor(ftp, ven_code)
    vendor_dfs[ven_code] = mpl_df[['E SKU', 'VENDOR ITEM CODE', 'ID', 'SERIES', 'COLOR', 'SIZE', 'FINISH', 'PRICELIST STATUS']].copy()
    vendor_dfs[ven_code].set_index('E SKU', inplace=True)

ftp.cwd(root)

prod_df = et.get_current_prod(ftp)
prod_df = prod_df[prod_df['Top Row'].notna()].copy()
prod_df.set_index('Variant SKU', inplace=True)

ignore_folders = ['angled-corner', 'lifestyle', 'corner','top-down']  # Add folder names to ignore here

#----------------------------USER SELECTION-------------------------------------#
print("\n" + "="*60)
print("IMAGE MANIFEST CREATION")
print("="*60)

# Get user choice
choice = input("\nDo you want to process:\n1. All vendors\n2. One vendor\n\nEnter your choice (1 or 2): ").strip()

selected_tile_vendors = ACTIVE_TILE_VENDORS.copy()
selected_tool_vendors = ACTIVE_TOOL_VENDORS.copy()

if choice == "2":
    # Show all available vendors
    all_vendors = list(ACTIVE_TILE_VENDORS.keys()) + list(ACTIVE_TOOL_VENDORS.keys())
    print("\nAvailable vendors:")
    for idx, ven_code in enumerate(all_vendors, 1):
        vendor_type = "Tile" if ven_code in ACTIVE_TILE_VENDORS else "Tool"
        print(f"  {idx}. {ven_code} ({vendor_type})")
    
    vendor_choice = input("\nEnter the vendor code (e.g., ven_code): ").strip().upper()
    
    # Validate and filter vendors
    if vendor_choice in ACTIVE_TILE_VENDORS:
        selected_tile_vendors = {vendor_choice: ACTIVE_TILE_VENDORS[vendor_choice]}
        selected_tool_vendors = {}
        print(f"\nProcessing tile vendor: {vendor_choice}")
    elif vendor_choice in ACTIVE_TOOL_VENDORS:
        selected_tool_vendors = {vendor_choice: ACTIVE_TOOL_VENDORS[vendor_choice]}
        selected_tile_vendors = {}
        print(f"\nProcessing tool vendor: {vendor_choice}")
    else:
        print(f"ERROR: Vendor '{vendor_choice}' not found. Processing all vendors instead.")
elif choice == "1":
    print("\nProcessing all vendors...")
else:
    print("Invalid choice. Processing all vendors instead.")

# Create an ExcelWriter object
full_out = pd.ExcelWriter('./out/full-manifest.xlsx', engine='xlsxwriter')

try:
    #----------------------------TILES-------------------------------------#
    for ven in selected_tile_vendors.keys():
        ftp.cwd(f"ElitTile_images/{ven}/products")
        folder_list = ftp.nlst()
        ftp.cwd(root)

        for folder in folder_list:
            if folder in ignore_folders:
                continue  # Skip this folder if it's in the ignore list
            if not "." in folder:
                ftp.cwd(f"ElitTile_images/{ven}/products/{folder}")
                pwd(ftp)
                file_list = ftp.nlst()
                for file in file_list:
                    matches = re.findall(SKU_PATTERN, file, flags=re.IGNORECASE)
                    if matches:
                        sku = matches[0]
                        vendor_dfs[ven].at[sku, folder] = file
                ftp.cwd(root)
                pwd(ftp)

        ## Scrape all files in folder 'videos'
        ftp.cwd(f"ElitTile_images/{ven}/videos")
        pwd(ftp)
        video_file_list = ftp.nlst()
        ftp.cwd(root)
        pwd(ftp)

        for file in video_file_list:
            if file.endswith(".mp4"):
                matches = re.findall(SKU_PATTERN, file, flags=re.IGNORECASE)
                if matches:
                    sku = matches[0]
                    vendor_dfs[ven].at[sku, 'motion-clip'] = file

        for i, r in vendor_dfs[ven].iterrows():
            try:
                vendor_dfs[ven].at[i, 'shopify status'] = prod_df.at[i, 'Status']
            except KeyError:
                vendor_dfs[ven].at[i, 'shopify status'] = "Not Listed"
            except Exception as e:
                print(f"Unknown error for product {i} setting status to 'UNKNOWN'")
                vendor_dfs[ven].at[i, 'shopify status'] = "UNKNOWN"

        column_order = ['VENDOR ITEM CODE', 'ID', 'SERIES', 'COLOR', 'SIZE', 'FINISH', 'PRICELIST STATUS', 
                        'shopify status', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'motion-clip']

        vendor_dfs[ven] = vendor_dfs[ven].reindex(columns=column_order)

        vendor_dfs[ven].to_excel(f"./out/{ven}-full-image-manifest.xlsx")

        # Write to the combined Excel file
        vendor_dfs[ven].to_excel(full_out, sheet_name=ven)

        print(f'Created {ven}-full-image-manifest.xlsx successfully')   

    #----------------------------TOOLS-------------------------------------#
    for ven in selected_tool_vendors.keys():
        ftp.cwd(f"ElitTile_images/{ven}/products")
        folder_list = ftp.nlst()
        ftp.cwd(root)

        for folder in folder_list:
            if folder in ignore_folders:
                continue  # Skip this folder if it's in the ignore list
            if not "." in folder:
                ftp.cwd(f"ElitTile_images/{ven}/products/{folder}")
                pwd(ftp)
                file_list = ftp.nlst()
                for file in file_list:
                    matches = re.findall(SKU_PATTERN, file, flags=re.IGNORECASE)
                    if matches:
                        sku = matches[0]
                        vendor_dfs[ven].at[sku, folder] = file
                ftp.cwd(root)
                pwd(ftp)

        ## Scrape all files in folder 'videos'
        ftp.cwd(f"ElitTile_images/{ven}/videos")
        pwd(ftp)
        video_file_list = ftp.nlst()
        ftp.cwd(root)
        pwd(ftp)

        for file in video_file_list:
            if file.endswith(".mp4"):
                matches = re.findall(SKU_PATTERN, file, flags=re.IGNORECASE)
                if matches:
                    sku = matches[0]
                    vendor_dfs[ven].at[sku, 'motion-clip'] = file

        for i, r in vendor_dfs[ven].iterrows():
            try:
                vendor_dfs[ven].at[i, 'shopify status'] = prod_df.at[i, 'Status']
            except KeyError:
                vendor_dfs[ven].at[i, 'shopify status'] = "Not Listed"
            except Exception as e:
                print(f"Unknown error for product {i} setting status to 'UNKNOWN'")
                vendor_dfs[ven].at[i, 'shopify status'] = "UNKNOWN"

        column_order = ['VENDOR ITEM CODE', 'ID', 'SERIES', 'COLOR', 'SIZE', 'FINISH', 'PRICELIST STATUS', 
                        'shopify status', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'motion-clip']

        vendor_dfs[ven] = vendor_dfs[ven].reindex(columns=column_order)

        vendor_dfs[ven].to_excel(f"./out/{ven}-full-image-manifest.xlsx")

        # Write to the combined Excel file
        vendor_dfs[ven].to_excel(full_out, sheet_name=ven)

        print(f'Created {ven}-full-image-manifest.xlsx successfully') 

finally:
    # Save and close the ExcelWriter object
    full_out.close()

print("Program completes sucessfully")
