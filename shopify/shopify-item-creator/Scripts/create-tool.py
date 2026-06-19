import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

# Added V Code Metafield 08 16 2024
# Added Series metafield 08 21 2024
#-------------------------Functions--------------------------------#

def transform_series(series):
    if pd.isna(series):
        return ''  # Return an empty string if the value is NA
    return 'series-' + series.strip().lower().replace(' ', '-')

def get_non_zero_numbers(vendor_id):
    # Use regular expression to find all numbers in the string
    numbers = re.findall(r'\d+', vendor_id)
    
    # Filter out numbers that are non-zero and remove leading zeros
    non_zero_numbers = [str(int(num)) for num in numbers if int(num) != 0]
    
    return non_zero_numbers

# Function to create series handle
def create_series_handle(vendor_id, series_name):
    if pd.notna(series_name) and series_name:  # Check if series_name (Tags) is not NaN and not empty
        non_zero_numbers = get_non_zero_numbers(vendor_id)
        if non_zero_numbers:  # Check if there are valid non-zero numbers
            # Assuming you want the first non-zero number if there are multiple
            non_zero_number = non_zero_numbers[0]
            return f'{non_zero_number}-{series_name}'
    return ''  # Return an empty string if Tags is NaN or no valid non-zero number

folder_path_filtered_data = r'C:\Users\VVillafana\Desktop\python_scripts\elit-tile-script\shopify-item-creator\Filtered Data'
output_import_folder = r'C:\Users\VVillafana\Desktop\python_scripts\elit-tile-script\shopify-item-creator\Import Files'

Vendor_Mapping = et.get_tool_vendors()
Brand_Mapping = et.get_tool_brand_mapping()

#ftp = et.ftp_login()

Vendor_id = input('Input vendor code (not case sensistve): ').upper()

#df_unfiltered = et.get_tool_mpl_by_vendor(ftp, Vendor_id)
df_unfiltered = et.get_tool_mpl_by_vendor_2(Vendor_id)

#Filtering out all of the INACTIVE items and saving them into an Excel File to spot check if needed

df_unfiltered = df_unfiltered[df_unfiltered['PRICELIST STATUS'] == "ACTIVE"]

os.makedirs(folder_path_filtered_data, exist_ok=True)

output_excel_file = os.path.join(folder_path_filtered_data, Vendor_id + " Filtered_Data.xlsx")
df_unfiltered.to_excel(output_excel_file, index=False)

file_path = os.path.join(folder_path_filtered_data, output_excel_file )

print("Filtered Excel file has been created in the '{}' folder.".format(folder_path_filtered_data))

df = pd.read_excel(file_path)

# Begin filling out the import file columns

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

# Mapping the vendor with the vendor name

vendor_name = Vendor_Mapping.get(Vendor_id, "Vendor ID not found")
new_df['Vendor'] = vendor_name

# Creating the Tag for Smart Collection mapping

new_df['Tags'] = df['SERIES'].apply(transform_series)

# Continuing on with the simple mappings

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

# Mapping the Variant Option Names and Values

new_df['Option 1 Name'] = ''
new_df['Option 1 Value'] = ''
new_df['Option 2 Name'] = ''
new_df['Option 2 Value'] = ''
new_df['Option 3 Name'] = ''
new_df['Option 3 Value'] = ''

# Define the order of options
options = ['SIZE', 'COLOR', 'FINISH']

# Iterate over each row in the original DataFrame
for index, row in df.iterrows():
    option_names = []
    option_values = []
    
    # Collect names and values if they are not missing
    for option in options:
        if pd.notna(row[option]):
            option_names.append(option.title())
            option_values.append(row[option])
    
    # Assign names and values to Option columns
    for i in range(3):
        option_name_col = f'Option {i+1} Name'
        option_value_col = f'Option {i+1} Value'
        if i < len(option_names):
            new_df.at[index, option_name_col] = option_names[i]
            new_df.at[index, option_value_col] = option_values[i]
        else:
            new_df.at[index, option_name_col] = ''
            new_df.at[index, option_value_col] = ''

# Back to simple mapping

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

# Create the logic for if an item needs the calculator or not
new_df['Variant Metafield: calculator.show-for-variant [boolean]'] = (new_df['Variant Metafield: pricelist.uom [single_line_text_field]'] != 
                                                                      new_df['Variant Metafield: pricelist.sell_unit [single_line_text_field]']).astype(str).str.upper()
new_df['Metafield: calculator.show [boolean]'] = new_df['Variant Metafield: calculator.show-for-variant [boolean]']

# Using a formula to generate Price and cost

new_df['Variant Cost'] = new_df['Variant Metafield: pricelist.cost_by_uom [number_decimal]'].astype(float) * new_df['Metafield: calculator.ratio [number_decimal]'].astype(float)
new_df['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'] = new_df['Variant Price']
new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'] = new_df['Variant Metafield: pricelist.msrp_sell_unit [number_decimal]'].astype(float) / new_df['Metafield: calculator.ratio [number_decimal]'].astype(float)
new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'] = new_df['Variant Metafield: pricelist.msrp_uom [number_decimal]'].round(2)

new_df['Metafield: custom.custom_variant [collection_reference]'] = new_df['Tags'].apply(lambda x: create_series_handle(Vendor_id, x))

# Mapping in the Tool Filters

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

# Locations

new_df['Inventory Available: Elit Tile -  North Hollywood'] = 'Stocked'
new_df['Inventory Available: Elit Tile - Los Angeles'] = 'Stocked'

#Create Import Excel File from new_df
os.makedirs(output_import_folder, exist_ok=True)

sheet_name = 'Products'

output_import_file = os.path.join(output_import_folder, Vendor_id + ' Shopify Tool Import.xlsx')
new_df.to_excel(output_import_file, sheet_name=sheet_name, index=False)

print("Import file has been created in the '{}' folder.".format(output_import_folder))