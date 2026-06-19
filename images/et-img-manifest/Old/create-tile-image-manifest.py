import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

def pwd(ftp):
    print(f"Changing directory to {ftp.pwd()}")

def get_mpl() -> pd.DataFrame:
    MPL_FN = 'CURRENT_TILE_MPL.xlsx'

SKU_PATTERN = et.SKU_PATTERN

OUT_DIR = ".\\out\\"

## Data File info
DATA_PATH = 'data'
DATA_FILE_LIST = ['CURRENT_TILE_MPL.xlsx', 'Matrixify All Products.xlsx']
LOCAL_DATA_FILES = []
DATA_FILES = {
    'mpl': 'CURRENT_TILE_MPL.xlsx',
}

ACTIVE_VENDORS = et.get_tile_vendors()

full_out = pd.ExcelWriter('./out/full-manifest.xlsx', engine='xlsxwriter')

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

ven_codes = ACTIVE_VENDORS.keys()
for ven_code in ven_codes:
    mpl_df = et.get_tile_mpl_by_vendor(ftp, ven_code)
    vendor_dfs[ven_code] = mpl_df[['E SKU', 'VENDOR ITEM CODE', 'ID', 'SERIES', 'COLOR', 'SIZE', 'FINISH', 'PRICELIST STATUS']].copy()
    vendor_dfs[ven_code].set_index('E SKU', inplace=True)


ftp.cwd(root)

prod_df = et.get_current_prod(ftp)
prod_df = prod_df[prod_df['Top Row'].notna()].copy()
prod_df.set_index('Variant SKU', inplace=True)

ignore_folders = ['angled-corner', 'lifestyle', 'corner','top-down']  # Add folder names to ignore here

for ven in ACTIVE_VENDORS.keys():
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
            print(f"Unknown error for product {sku} setting status to 'UNKNOWN'")
            vendor_dfs[ven].at[i, 'shopify status'] = "UNKNOWN"

    column_order = ['VENDOR ITEM CODE', 'ID', 'SERIES', 'COLOR', 'SIZE', 'FINISH', 'PRICELIST STATUS', 
                    'shopify status', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'motion-clip']

    vendor_dfs[ven] = vendor_dfs[ven].reindex(columns=column_order)

    vendor_dfs[ven].to_excel(f"./out/{ven}-full-image-manifest.xlsx")
    vendor_dfs[ven].to_excel(full_out, sheet_name=ven)
    print(f'Created {ven}-full-image-manifest.xlsx successfully')   

full_out.close()

print("Program completes sucessfully")