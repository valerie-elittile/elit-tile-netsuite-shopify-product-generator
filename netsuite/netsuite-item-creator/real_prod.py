import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et

'''
This script will do two things. It will make the add item import file to import straight into NetSuite and the UOM import file that is needed before 
the add item file. It requires only the mpl file be updated and uploaded on to the FTP server.

'''
ven_code = input('Enter Vendor ID (not case sensitive):  ').upper()

print('What type of item will you be processing?')
mpl_type = input('1 for Tile \n2 for Tool\n...')

if mpl_type == '1':
    mpl_all = et.get_tile_mpl_itshare()
    mpl = mpl_all[mpl_all["VENDOR"] == ven_code].copy()
    print('Tile mpl has been chosen')
elif mpl_type == '2':
    mpl = et.get_tool_mpl_by_vendor_2(ven_code)
    print('Tool mpl has been chosen')
else:
    print('1 or 2 must be chosen')

mpl = mpl[mpl['PRICELIST STATUS'] == 'ACTIVE']

mpl = mpl[mpl['E CODE NETSUITE INTERNAL ID'].isna()]

# mpl = mpl[mpl['E CODE NETSUITE INTERNAL ID'].notna()]

# UOM and Unit Mapping

uom_mapping = et.get_uom_mapping()
plural_uom_mapping = et.get_plural_uom_mapping()
sell_unit_mapping = et.get_sell_unit_mapping()
plural_sell_unit_mapping = et.get_plural_sell_unit_mapping()

vendor_mapping = et.get_all_vendors()

vendor = vendor_mapping.get(ven_code)

# --------------------------- ADD ITEM SECTION -------------------------------------#

df = pd.DataFrame()

df['externalid'] = mpl['E SKU']
df['V SKU'] = mpl['V SKU'].str.upper()
df['itemId'] = df['externalid']
df['internalID'] = ''
df['Item Weight'] = mpl['WEIGHT/SELL UNIT']
df['ID'] = mpl['ID']
df['isdropshipitem'] = "T"
df['vendor_code'] = mpl["VENDOR ITEM CODE"].astype(str).replace('nan', '')
df['SERIES'] = mpl['SERIES'].where(mpl['SERIES'].notna(), '').astype(str).str.upper()
df['Item Size'] = mpl['SIZE'].str.upper()
df['Item Color'] = mpl['COLOR'].where(mpl['COLOR'].notna(), '').astype(str).str.upper()

if mpl_type == "2":
    df['Item Name'] = mpl['SHOPIFY NAME'].str.upper()
else:    
    df['Item Name'] = np.where(
        mpl['FINISH'].isna(),
        mpl['SERIES'].str.strip(),
        mpl['SERIES'].str.strip() + ' ' + mpl['FINISH'].str.strip().str.upper()
    )

df['Item Number and Name'] = df['externalid'] + ' ' + df['Item Name']
df['displayname'] = df[['Item Name', 'Item Size', 'Item Color', 'vendor_code', 'V SKU']].fillna('').astype(str).apply(lambda x: ' '.join(x[x != '']), axis=1)
df['Type'] = 'Inventory Item'
df['Pcs in a Box'] = mpl['EA/BX']
df['SQFT BY PCS/SHEET'] = mpl['SF/EA']
df['SQFT BY BOX'] = mpl['SF/BX']

# Creating Sales Description
df['salesdescription'] = ''

for index, row in df.iterrows():
    description = ''
    if not pd.isnull(row['Pcs in a Box']):
        description += str(row['Pcs in a Box']) + ' EA/BX'
    if not pd.isnull(row['SQFT BY PCS/SHEET']):
        description += ' ' + str(row['SQFT BY PCS/SHEET']) + ' SF/EA'
    if not pd.isnull(row['SQFT BY BOX']):
        description += ' ' + str(row['SQFT BY BOX']) + ' SF/BX'
    
    df.at[index, 'salesdescription'] = description.strip()

# Class mapping

class_mapping = et.get_class_mapping()

if mpl_type == "2":
    df['Class'] = 110
else:
    df['Class'] = mpl['PIECE TYPE (FILTER)'].str.upper().map(class_mapping)

df['Sales Packaging Unit'] = mpl['SELL UNIT'].str.upper().map(sell_unit_mapping)

df['UOM'] = mpl['UOM'].str.upper().map(uom_mapping)

df['Sales QTY Per Pack Unit'] = mpl['CONV']

df['stockunit'] = mpl['UOM'].str.upper().map(plural_uom_mapping)

df['purchaseunit'] = df['stockunit']

df['saleunits'] = mpl['SELL UNIT'].str.upper().map(plural_sell_unit_mapping)

df['cost'] = mpl['COST/UOM']

variant_cost = df['cost'].astype(float) * df['Sales QTY Per Pack Unit'].astype(float)

base_price = mpl['PRICE PER SELL UNIT']

df['Price by UOM'] = base_price / df['Sales QTY Per Pack Unit']

df['unitstype'] = df['externalid']
df['parent'] = ''
df['includechildren'] = ''
df['Department'] = ''
df['Location'] = 'LA ElitTile.com'
df['costingmethod'] = ''
df['purchasedescription'] = ''
df['matchbilltoreceipt'] = ''
df['usebins'] = ''
df['supplyreplenishmentmethod'] = ''
df['alternatedemandsourceitem'] = ''
df['autopreferredstocklevel'] = ''
df['reordermultiple'] = ''
df['isspecialorderitem'] = ''
df['autoreorderpoint'] = ''
df['autoleadtime'] = ''
df['leadtime'] = ''
df['safetystocklevel'] = ''
df['safetystockleveldays'] = ''
df['transferprice'] = ''
df['preferredlocation'] = ''
df['itembinnumber1'] = ''
df['preferredperlocation'] = ''
df['subsidiary'] = 'Elit Tile Consolidated : ElitTile.com'
df['vendor1_name'] = vendor
df['vendor1_preferred'] = ''
df['vendor1_subsidiary'] = 10
df['vendor1_purchaseprice'] = df['cost']
df['vendor1_schedule'] = ''
df['vendor1_code'] = df['vendor_code']
df['vendor2_name'] = 'E0002 ELIT TILE LA'
df['vendor2_preferred'] = 'T'
df['vendor2_subsidiary'] = 10
df['vendor2_purchaseprice'] = df['cost']
df['vendor2_schedule'] = ''
df['vendor2_code'] = df['vendor_code']
df['itemLocationLine1_location'] = ''
df['itemLocationLine1_defaultreturncost'] = ''
df['itemLocationLine1_preferredstocklevel'] = ''
df['itemLocationLine1_reorderpoint'] = ''
df['itemLocationLine1_lotnumbers'] = ''
df['itemLocationLine1_lotsizingmethod'] = ''
df['costestimatetype'] = ''
df['costestimate'] = ''
df['minimumquantity'] = ''
df['enforceminqtyinternally'] = ''
df['itemPriceLine1_itemPriceTypeRef'] = 'BASE PRICE'
df['itemPriceLine1_itemPrice'] = base_price
df['itemPriceLine1_quantityPricing'] = 0
df['cogsaccount'] = ''
df['incomeaccount'] = ''
df['assetaccount'] = ''
df['billpricevarianceacct'] = ''
df['billqtyvarianceacct'] = ''
df['billexchratevarianceacct'] = ''
df['custreturnvarianceaccount'] = ''
df['vendreturnvarianceaccount'] = ''
df['taxSchedule'] = 'Taxable'
df['Item Image'] = ''
df['Variant Inventory Item ID'] = mpl['Variant Inventory Item ID']
df['Variant ID'] = mpl['Variant ID']
df['Variant Weight'] = df['Item Weight']
df['Variant Weight Unit'] = 'lb'
df['Handle'] = mpl['Handle']
df['Shopify Flag'] = 'Add/Update Item'

# Define a dictionary to specify the data type for each column
dtype_dict = {col: str for col in df.columns}

# Fill NaN values with empty strings using the specified data types
add_item_df = df.fillna('', inplace=False).astype(dtype_dict)

output_folder = 'Real Product Add Item Files'
os.makedirs(output_folder, exist_ok=True)

output_csv_file = os.path.join(output_folder, ven_code + " ADD ITEM.csv")

add_item_df.to_csv(output_csv_file, index=False)

print("Add Item Import file has been created in the '{}' folder.".format(output_folder))

#------------------------------- UOM File Section-------------------------------#

# Dictionaries for Mapping

Plural = et.get_unit_plural_mapping()
Abb = et.get_uom_mapping_abb()
Plural_Abb = et.get_plural_abb_mapping()

# Filter rows where 'Sales Packaging Unit' is not equal to 'UOM'
mask = df['Sales Packaging Unit'] != df['UOM']

# Extract rows that satisfy the condition
filtered_rows = df[mask]

# Duplicate 'externalid' values where the condition is met
duplicated_externalids = filtered_rows['externalid']

# Append duplicated rows to the original DataFrame
uom_df = pd.concat([df, filtered_rows], ignore_index=True)

# Sort values by 'externalid'
uom_df = uom_df.sort_values(by='externalid').reset_index(drop=True)


# Select only the desired columns in the output file
output_columns = ['externalid', 'UOM', 'Sales Packaging Unit']  # Add other column names if needed
uom_df = uom_df[output_columns]

uom_df['Internal ID*Update Only'] = ''

unit_names = []

# Loop through the filtered DataFrame to populate 'Unit Name (Name)' based on conditions
for index, row in uom_df.iterrows():
    if row['UOM'] == row['Sales Packaging Unit']:
        unit_names.append(row['UOM'])
    else:
        unit_names.append(row['Sales Packaging Unit'] if index % 2 != 0 else row['UOM'])

# Check if lengths match before assigning as a new column
if len(unit_names) == len(uom_df):
    uom_df['Unit Name (Name)'] = unit_names
else:
    print("Lengths don't match! Please verify the logic.")

# Assign the list to the DataFrame as the 'Unit Name (Name)' column
uom_df['Unit Name (Name)'] = unit_names

uom_df = uom_df.drop(columns=['UOM','Sales Packaging Unit'])


# Plura names, abbreviations, and plural abbreviations columns

uom_df['Plural Name'] = uom_df['Unit Name (Name)'].map(Plural)
uom_df['Abbreviation'] = uom_df['Unit Name (Name)'].map(Abb)
uom_df['Plural Abbreviation'] = uom_df['Unit Name (Name)'].map(Plural_Abb)

# Conversion Rate and Base Unit

# Initialize lists to store values for new columns
conversion_rate = []
base_unit = []

# Loop through the filtered DataFrame to populate 'Conversion Rate(/Base)' and 'Base Unit' columns
for index, row in uom_df.iterrows():
    if index % 2 == 0:  # For the first instance of externalid
        conversion_rate.append(1)
        base_unit.append('Yes')
    else:  # For the second instance of externalid
        # Retrieve 'Sales QTY Per Pack Unit' value from the original df based on 'externalid'
        sales_qty = df.loc[df['externalid'] == row['externalid'], 'Sales QTY Per Pack Unit'].values
        if len(sales_qty) > 0:  # Ensure a value is found
            conversion_rate.append(sales_qty[0])  # Use the 'Sales QTY Per Pack Unit' value
        else:
            conversion_rate.append(None)  # If not found, append None

        # Set 'Base Unit' based on 'Conversion Rate(/Base)' value
        base_unit.append('Yes' if conversion_rate[-1] == 1 else 'No')

# Check if lengths match before assigning as new columns
if len(conversion_rate) == len(uom_df) and len(base_unit) == len(uom_df):
    uom_df['Conversion Rate(/Base)'] = conversion_rate
    uom_df['Base Unit'] = base_unit
else:
    print("Lengths don't match! Please verify the logic.")

# Rename Columns
uom_df = uom_df.rename(columns={'externalid': 'Item(Type Name)'})

# Fill NaN values with appropriate values for each column type
uom_df = uom_df.fillna({
    'Conversion Rate(/Base)': 0,  # Numeric columns use 0
    'Item(Type Name)': '',
    'Unit Name (Name)': '',
    'Internal ID*Update Only': '',
    'Plural Name': '',
    'Abbreviation': '',
    'Plural Abbreviation': '',
    'Base Unit': ''
})

uom_df = uom_df.sort_values(by=['Item(Type Name)', 'Base Unit'], ascending=[True, False])

# print(uom_df.head())

# Create a folder named 'Add Item Output'
output_folder_2 = 'Real Product UOM Files'
os.makedirs(output_folder_2, exist_ok=True)

# Define the output file path within the folder
output_csv_file_2 = os.path.join(output_folder_2, ven_code + " UOM.csv")

# Save the DataFrame to the output file
uom_df.to_csv(output_csv_file_2, encoding="utf-8", index=False)

# create a csv file that has 'Netsuite E code' column name with mpl['E SKU'] data and 'External Id' column name with mpl['V SKU'] data
sync_mpl = pd.DataFrame({
    'Netsuite E code': mpl['E SKU'],
    'External Id': mpl['V SKU']
})

output_folder_3 = 'V Code and E code Link'
os.makedirs(output_folder_3, exist_ok=True)
output_csv_file_mpl = os.path.join(output_folder_3, "{} V code sync to E code.csv".format(ven_code))
sync_mpl.to_csv(output_csv_file_mpl, encoding="utf-8", index=False)

print("UOM Import file has been created in the '{}' folder.".format(output_folder_2))
