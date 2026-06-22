# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## Overview

This directory contains scripts that generate NetSuite CSV import files from the Master Price List (MPL). There are two scripts: one for real (full-size) products and one for sample products. Both run from `netsuite-item-creator/`.

## Scripts

### `real_prod.py` — Real Product Import

Generates two CSV files per vendor:

1. **ADD ITEM file** (`{vendor_code} ADD ITEM.csv`) — the main product import with all item fields
2. **UOM file** (`{vendor_code} UOM.csv`) — unit of measure conversion table required before importing items

Also generates a **V-to-E code sync file** (`{vendor_code} V code sync to E code.csv`) mapping V SKUs to E SKUs.

**Processing flow:**
1. Prompts for vendor code and product type (Tile or Tool)
2. Loads MPL via `et.get_tile_mpl_itshare()` or `et.get_tool_mpl_by_vendor_2()`
3. Filters to ACTIVE items that do NOT yet have a NetSuite internal ID (`E CODE NETSUITE INTERNAL ID` is NaN)
4. Builds ADD ITEM DataFrame with vendor info, pricing, Shopify integration fields
5. Builds UOM DataFrame by duplicating rows where Sales Packaging Unit differs from base UOM

**ADD ITEM key fields:**
- `externalid` / `itemId`: E SKU
- `displayname`: concatenation of Item Name + Size + Color + vendor code + V SKU
- `Item Name`: SERIES + FINISH (tile) or SHOPIFY NAME (tool)
- `vendor1_name`: the vendor from ETlib mapping; `vendor2_name`: always `E0002 ELIT TILE LA` (preferred)
- `cost`: COST/UOM from MPL
- `itemPriceLine1_itemPrice`: PRICE PER SELL UNIT from MPL
- `unitstype`: set to the E SKU (used as the UOM group name in NetSuite)
- `subsidiary`: `Elit Tile Consolidated : ElitTile.com`
- `Location`: `LA ElitTile.com`
- `taxSchedule`: `Taxable`
- Shopify fields: `Variant Inventory Item ID`, `Variant ID`, `Handle`, `Shopify Flag` (set to `Add/Update Item`)

**UOM file logic:**
- Every item gets a base unit row (conversion rate = 1)
- If the Sales Packaging Unit differs from the base UOM, a second row is added with the conversion rate from `Sales QTY Per Pack Unit` (the CONV column)
- Unit names, plurals, and abbreviations come from ETlib mappings (`get_unit_plural_mapping()`, `get_uom_mapping_abb()`, `get_plural_abb_mapping()`)
- Rows are sorted by item name then base unit descending (base unit first)

### `sample_prod.py` — Sample Product Import

Generates four CSV output sets per vendor:

1. **E-code sample ADD ITEM** (`{vendor_code} SAMPLE ADD ITEM.csv`)
2. **E-code sample UOM** (`{vendor_code} SAMPLE UOM.csv`)
3. **V-code sample ADD ITEM** (`{retail_vendor} SAMPLE ADD ITEM.csv`)
4. **V-code sample UOM** (`{retail_vendor} SAMPLE UOM.csv`)

**Processing flow:**
1. Filters MPL to `HAS CUT SAMPLE == 'YES'` and `PRICELIST STATUS == 'ACTIVE'`
2. For each qualifying row, appends `-S` to the SKU to create the sample SKU
3. Sample items always use `EACH` as the unit, cost/price = 0, weight = 1 lb, non-taxable

**E-code vs V-code samples:**
- E-code samples: vendor is `E0002 ELIT TILE LA`, subsidiary is `ElitTile.com`, single vendor line
- V-code samples: vendor is the retail vendor (from `et.get_retail_vendor_mapping()`), subsidiary is `Elit Tile Corp (LA)|International Tile and Stone Inc. (noho)`, two vendor lines (subsidiary 3 and 4)

**Special case:** Vendor E0207 triggers a warning — this vendor does not have automatic samples and should only be processed if instructed by managers.

## Output Directories

All output folders are gitignored:
- `Real Product Add Item Files/` — ADD ITEM CSVs for real products
- `Real Product UOM Files/` — UOM CSVs for real products
- `V Code and E code Link/` — V-to-E code mapping CSVs
- `Sample Product Add Item Files/` — E-code sample ADD ITEM CSVs
- `Sample Product UOM Files/` — E-code sample UOM CSVs
- `V Code Sample Product Add Item Files/` — V-code sample ADD ITEM CSVs
- `V Code Sample Product UOM Files/` — V-code sample UOM CSVs

## UOM/Unit Mapping Reference

ETlib provides several related but distinct mappings:
- `get_uom_mapping()`: base unit names (e.g., `SF` → `Square Foot`)
- `get_plural_uom_mapping()`: plural unit names (e.g., `SF` → `Square Feet`)
- `get_sell_unit_mapping()`: sell unit names (same structure as UOM but for packaging units)
- `get_plural_sell_unit_mapping()`: plural sell unit names
- `get_unit_plural_mapping()`: singular → plural (e.g., `Square Foot` → `Square Feet`)
- `get_uom_mapping_abb()`: unit → abbreviation (e.g., `Square Foot` → `SF`)
- `get_plural_abb_mapping()`: plural → abbreviation

## Import Order in NetSuite

UOM files must be imported before ADD ITEM files — NetSuite needs the unit of measure definitions to exist before items can reference them.
