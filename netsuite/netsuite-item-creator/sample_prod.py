import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_sales_description(row):
    parts = []
    if pd.notna(row.get('EA/BX')):
        parts.append(f"{row['EA/BX']} EA/BX")
    if pd.notna(row.get('SF/EA')):
        parts.append(f"{row['SF/EA']} SF/EA")
    if pd.notna(row.get('SF/BX')):
        parts.append(f"{row['SF/BX']} SF/BX")
    return ' '.join(parts)


def build_e_sample_row(row):
    sku = row['E SKU']
    sample_sku = sku + "-S"
    display_name = "SAMPLE - " + row['SHOPIFY NAME'].upper()

    return {
        "E SKU": sku,
        "NetSuite V Sample": row['V SKU'] + "-S",
        "External ID": sample_sku,
        "itemid": sample_sku,
        "Item Color": row['COLOR'],
        "Item Size": row['SIZE'].upper(),
        "costcategory": "Default Cost Category",
        "atpmethod": "Cumulative ATP with Look Ahead",
        "Vendor": "E0002 ELIT TILE LA",
        "Subsidiary": "Elit Tile Consolidated : ElitTile.com",
        "Tax Schedule": "Non-Taxable",
        "Display Name/Code": display_name,
        "HANDLE SHOPIFY": sku.lower() + "-s",
        "ID": "",
        "Item Name": display_name,
        "Item Name/Number (Req)": sample_sku + " " + display_name,
        "Item Weight": "1",
        "Location": "LA ElitTile.com",
        "Primary Purchase Unit": "",
        "Primary Sale Unit": "",
        "Primary Stock Unit": "",
        "Purchase Price": "0",
        "itemPriceLine1_itemPriceTypeRef": "BASE PRICE",
        "itemPriceLine1_itemPrice": "0",
        "itemPriceLine1_quantityPricing": "0",
        "vendor1_subsidiary": 10,
        "vendor1_preferred": "T",
        "vendor1_purchaseprice": 0,
        "isdropship": "T",
    }


def build_v_sample_row(row, retail_vendor):
    sku = row['V SKU']
    sample_sku = sku + "-S"
    display_name = "SAMPLE - " + row['SHOPIFY NAME'].upper()
    vendor_code = row['VENDOR ITEM CODE'] if pd.notna(row['VENDOR ITEM CODE']) else ''

    return {
        "V SKU": sku,
        "NetSuite E Sample": row['E SKU'] + "-S",
        "External ID": sample_sku,
        "itemid": sample_sku,
        "Item Color": row['COLOR'],
        "Item Size": row['SIZE'].upper(),
        "Vendor Code": vendor_code,
        "Sales Description": build_sales_description(row),
        "costcategory": "Default Cost Category",
        "atpmethod": "Cumulative ATP with Look Ahead",
        "Subsidiary": "Elit Tile Consolidated : Elit Tile Corp (LA)|Elit Tile Consolidated : International Tile and Stone Inc. (noho)",
        "Tax Schedule": "Non-Taxable",
        "Display Name/Code": display_name,
        "HANDLE SHOPIFY": row['E SKU'].lower() + "-s",
        "ID": "",
        "Item Name": display_name,
        "Item Name/Number (Req)": sample_sku + " " + display_name,
        "Item Weight": "1",
        "Location": "",
        "Primary Purchase Unit": "",
        "Primary Sale Unit": "",
        "Primary Stock Unit": "",
        "Purchase Price": "0",
        "itemPriceLine1_itemPriceTypeRef": "BASE PRICE",
        "itemPriceLine1_itemPrice": "0",
        "itemPriceLine1_quantityPricing": "0",
        "vendor1_name": retail_vendor,
        "vendor1_subsidiary": 3,
        "vendor1_preferred": "T",
        "vendor1_purchaseprice": 0,
        "vendor1_code": vendor_code,
        "vendor2_name": retail_vendor,
        "vendor2_subsidiary": 4,
        "vendor2_preferred": "T",
        "vendor2_purchaseprice": 0,
        "vendor2_code": vendor_code,
    }


def build_sample_uom_row(external_id):
    return {
        'Item(Type Name)': external_id,
        'Internal ID*Update Only': '',
        'Unit Name': 'EACH',
        'Plural Name': 'EACH',
        'Abbreviation': 'EA',
        'Plural Abbreviation': 'EA',
        'Conversion Rate(/Base)': '1',
        'Base Unit': 'Yes',
    }


def build_e_sample_df(mpl_for_sample):
    rows = [build_e_sample_row(r) for _, r in mpl_for_sample.iterrows()]
    df = pd.DataFrame(rows)
    dtype_dict = {col: str for col in df.columns}
    return df.fillna('').astype(dtype_dict)


def build_v_sample_df(mpl_for_sample, retail_vendor):
    rows = [build_v_sample_row(r, retail_vendor) for _, r in mpl_for_sample.iterrows()]
    df = pd.DataFrame(rows)
    dtype_dict = {col: str for col in df.columns}
    return df.fillna('').astype(dtype_dict)


def build_sample_uom_df(sample_df):
    rows = [build_sample_uom_row(r['External ID']) for _, r in sample_df.iterrows()]
    return pd.DataFrame(rows)


if __name__ == "__main__":
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

    #-----------------------------E Code Sample--------------------------------------#

    sample_df = build_e_sample_df(mpl_for_sample)

    output_cut_sample = os.path.join(output_folder_cut, ven_code + ' SAMPLE ADD ITEM.csv')
    sample_df.to_csv(output_cut_sample, index=False)
    print(f'Sample Add Item file has been created in the {output_folder_cut} for {vendor}')

    #-----------------------------E Code Sample UOM----------------------------------#

    uom_df = build_sample_uom_df(sample_df)

    output_cut_uom = os.path.join(output_folder_cut_uom, ven_code + ' SAMPLE UOM.csv')
    uom_df.to_csv(output_cut_uom, index=False)
    print(f'Sample UOM file has been created in the {output_folder_cut_uom} for {vendor}')

    #-----------------------------V Code Sample--------------------------------------#

    v_sample_df = build_v_sample_df(mpl_for_sample, retail_vendor)

    output_v_sample = os.path.join(output_folder_v, retail_vendor + ' SAMPLE ADD ITEM.csv')
    v_sample_df.to_csv(output_v_sample, index=False)
    print(f'Sample Add Item file has been created in the {output_folder_v} for {retail_vendor}')

    #-----------------------------V Code Sample UOM----------------------------------#

    v_uom_df = build_sample_uom_df(v_sample_df)

    output_v_uom = os.path.join(output_folder_v_uom, retail_vendor + ' SAMPLE UOM.csv')
    v_uom_df.to_csv(output_v_uom, index=False)
    print(f'Sample UOM file has been created in the {output_folder_v_uom} for {retail_vendor}')
