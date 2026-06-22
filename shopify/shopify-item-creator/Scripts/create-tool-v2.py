import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

#-------------------------Functions--------------------------------#

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)

def transform_series(series):
    if pd.isna(series):
        return ''
    return 'series-' + series.strip().lower().replace(' ', '-')

def get_non_zero_numbers(vendor_id):
    numbers = re.findall(r'\d+', vendor_id)
    non_zero_numbers = [str(int(num)) for num in numbers if int(num) != 0]
    return non_zero_numbers

def create_series_handle(vendor_id, series_name):
    if pd.notna(series_name) and series_name:
        non_zero_numbers = get_non_zero_numbers(vendor_id)
        if non_zero_numbers:
            non_zero_number = non_zero_numbers[0]
            return f'{non_zero_number}-{series_name}'
    return ''

def get_vendors_to_process(mpl_df):
    unique_vendors = sorted(mpl_df['VENDOR'].unique())
    print("\nUnique Vendor IDs in the MPL:")
    for vendor in unique_vendors:
        print(f"  {vendor}")

    vendors_to_process = []
    while True:
        vendor_id = input("\nEnter a Vendor ID to process (or type 'done' to finish): ").upper()
        if vendor_id == 'DONE':
            break
        elif vendor_id in unique_vendors:
            vendors_to_process.append(vendor_id)
            print(f"  Added {vendor_id}")
        else:
            print("Invalid Vendor ID. Please enter a valid one from the list above.")

    return vendors_to_process

def build_import_df(df, Vendor_id, Vendor_Mapping, Brand_Mapping):
    new_df = pd.DataFrame()

    new_df['ID'] = df['ID']
    new_df['Variant SKU'] = df['E SKU']
    new_df['Variant Metafield: custom.retail_v_code [single_line_text_field]'] = df['V SKU']
    new_df['Handle'] = df['HANDLE']
    new_df['Command'] = 'MERGE'
    new_df['SERIES'] = df['SERIES']
    new_df['Metafield: custom.series [single_line_text_field]'] = df['SERIES'].where(df['SERIES'].notna(), '').astype(str).str.title()
    new_df['Title'] = df['SHOPIFY NAME']
    new_df['BODY HTML'] = ''

    vendor_name = Vendor_Mapping.get(Vendor_id, "Vendor ID not found")
    new_df['Vendor'] = vendor_name

    new_df['Tags'] = df['SERIES'].apply(transform_series)

    new_df['Type'] = 'Tools'
    new_df['Status'] = 'Draft'
    new_df['Published'] = 'FALSE'
    new_df['Published Scope'] = 'web'
    new_df['Variant ID'] = df['Variant ID']
    new_df['Variant Inventory Item ID'] = df['Variant Inventory Item ID']
    new_df['Variant Command'] = 'MERGE'
    new_df['Variant Weight'] = df['WEIGHT']
    new_df['Variant Weight Unit'] = 'lb'
    new_df['Variant Metafield: pricelist.vendor_code [single_line_text_field]'] = df['VENDOR ITEM CODE']
    new_df['Variant Metafield: pricelist.class [single_line_text_field]'] = df['pricelist.class']

    new_df['Option 1 Name'] = ''
    new_df['Option 1 Value'] = ''
    new_df['Option 2 Name'] = ''
    new_df['Option 2 Value'] = ''
    new_df['Option 3 Name'] = ''
    new_df['Option 3 Value'] = ''

    options = ['SIZE', 'COLOR', 'FINISH']

    for index, row in df.iterrows():
        option_names = []
        option_values = []

        for option in options:
            if pd.notna(row[option]):
                option_names.append(option.title())
                option_values.append(row[option])

        for i in range(3):
            option_name_col = f'Option {i+1} Name'
            option_value_col = f'Option {i+1} Value'
            if i < len(option_names):
                new_df.at[index, option_name_col] = option_names[i]
                new_df.at[index, option_value_col] = option_values[i]
            else:
                new_df.at[index, option_name_col] = ''
                new_df.at[index, option_value_col] = ''

    new_df['Variant Metafield: pricelist.ea_bx [number_integer]'] = df['EA/BX']
    new_df['Variant Metafield: pricelist.sf_ea [number_decimal]'] = df['SF/EA']
    new_df['Variant Metafield: pricelist.sf_box [number_decimal]'] = df['SF/BX']
    new_df['Variant Metafield: pricelist.uom [single_line_text_field]'] = df['UOM']
    new_df['Variant Metafield: pricelist.sell_unit [single_line_text_field]'] = df['SELL UNIT']
    new_df['Variant Metafield: pricelist.cost_by_uom [number_decimal]'] = df['COST']
    new_df['Variant Price'] = df['PRICE PER SELL UNIT']
    new_df['Variant Metafield: calculator.ratio [number_decimal]'] = df['CONV']
    new_df['Metafield: calculator.ratio [number_decimal]'] = df['CONV']
    new_df['Variant Taxable'] = 'TRUE'
    new_df['Variant Inventory Policy'] = 'deny'
    new_df['Variant Fulfillment Service'] = 'manual'
    new_df['Variant Requires Shipping'] = 'TRUE'

    new_df['Variant Metafield: calculator.show-for-variant [boolean]'] = (new_df['Variant Metafield: pricelist.uom [single_line_text_field]'] !=
                                                                          new_df['Variant Metafield: pricelist.sell_unit [single_line_text_field]']).astype(str).str.upper()
    new_df['Metafield: calculator.show [boolean]'] = new_df['Variant Metafield: calculator.show-for-variant [boolean]']

    new_df['Variant Cost'] = new_df['Variant Metafield: pricelist.cost_by_uom [number_decimal]'].astype(float) * new_df['Metafield: calculator.ratio [number_decimal]'].astype(float)
    new_df['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'] = new_df['Variant Price']
    new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'] = new_df['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'].astype(float) / new_df['Metafield: calculator.ratio [number_decimal]'].astype(float)
    new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'] = new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'].round(2)

    new_df['Metafield: custom.custom_variant [collection_reference]'] = new_df['Tags'].apply(lambda x: create_series_handle(Vendor_id, x))

    vendor_brand = Brand_Mapping.get(Vendor_id, "Vendor ID not found")
    new_df['Metafield: my_fields.brand [single_line_text_field]'] = vendor_brand

    new_df['Metafield: tool.tools_categories [single_line_text_field]'] = df['CATEGORY']
    new_df['Metafield: tool_filter.type [single_line_text_field]'] = df['TOOL TYPE']
    new_df['Metafield: tool_filter.metal_trim_thickness [single_line_text_field]'] = df['METAL TRIM THICKNESS']
    new_df['Metafield: tool_filter.metal_trim_finish [single_line_text_field]'] = df['METAL TRIM FINISH']
    new_df['Metafield: tool_filter.metal_trim_length [single_line_text_field]'] = df['METAL TRIM LENGTH']
    new_df['Metafield: tool_filter.tile_spacer_shape [single_line_text_field]'] = df['TILE SPACER SHAPE/TYPE']
    new_df['Metafield: tool_filter.tile_spacer_size [single_line_text_field]'] = df['TILE SPACER SIZE']
    new_df['Metafield: tool_filter.blade_cut_material [list.single_line_text_field]'] = df['BLADE CUT MATERIAL']
    new_df['Metafield: tool_filter.blade_material [single_line_text_field]'] = df['BLADE MATERIAL']
    new_df['Metafield: tool_filter.grout_base_color [list.single_line_text_field]'] = df['GROUT/CAULK BASE COLOR']
    new_df['Metafield: tool_filter.grout_type [list.single_line_text_field]'] = df['GROUT/CAULK TYPE']
    new_df['Metafield: custom.trowel_notch_type [single_line_text_field]'] = df['TROWEL NOTCH TYPE']
    new_df['Metafield: tool_filter.trowel_size [single_line_text_field]'] = df['TROWL SIZE']

    new_df['Inventory Available: Elit Tile -  North Hollywood'] = 'Stocked'
    new_df['Inventory Available: Elit Tile - Los Angeles'] = 'Stocked'

    new_df = new_df.fillna('').astype(str)

    return new_df

#------------- Begin Script -----------------------------------------------#

output_import_folder = os.path.join(parent_dir, 'Import Files')
os.makedirs(output_import_folder, exist_ok=True)

output_filtered_folder = os.path.join(parent_dir, 'Filtered Data')
os.makedirs(output_filtered_folder, exist_ok=True)

Vendor_Mapping = et.get_tool_vendors()
Brand_Mapping = et.get_tool_brand_mapping()

mpl_df = et.get_tool_mpl_itshare()

vendors_to_process = get_vendors_to_process(mpl_df)

if not vendors_to_process:
    print("No vendors selected. Exiting.")
    sys.exit()

active_mpl = mpl_df[mpl_df['PRICELIST STATUS'] == "ACTIVE"]

for Vendor_id in vendors_to_process:
    df = active_mpl[active_mpl['VENDOR'] == Vendor_id].copy()
    df = df.reset_index(drop=True)

    if df.empty:
        print(f"No active items found for {Vendor_id}. Skipping.")
        continue

    filtered_file = os.path.join(output_filtered_folder, Vendor_id + " Filtered_Data.xlsx")
    df.to_excel(filtered_file, index=False)
    print(f"Filtered data saved: {filtered_file}")

    new_df = build_import_df(df, Vendor_id, Vendor_Mapping, Brand_Mapping)

    output_import_file = os.path.join(output_import_folder, Vendor_id + ' Shopify Tool Import.xlsx')
    new_df.to_excel(output_import_file, sheet_name='Products', index=False)
    print(f"Import file created: {output_import_file}")

print("\nDone.")
