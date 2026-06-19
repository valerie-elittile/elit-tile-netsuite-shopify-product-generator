# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this directory.

## Overview

This directory contains scripts that generate Shopify product import files (`.xlsx`) from the Master Price List (MPL). There are three pipelines: tile products, tool products, and sample products.

## Entry Points

- `shopify-item-creator/create-item.py` — interactive menu that delegates to tile (v4) or tool (v1) scripts via `subprocess`. Run from `shopify-item-creator/`.
- `shopify-item-creator/Scripts/create-tile-v4.py` — current tile pipeline. Run from `Scripts/`.
- `shopify-item-creator/Scripts/create-tool-v2.py` — current tool pipeline (multi-vendor). Run from `Scripts/`.
- `shopify-item-creator/Scripts/create-tool.py` — older single-vendor tool pipeline. Has hardcoded paths.
- `shopify-sample-creator/create-samples v2.py` — generates sample product imports + real-to-sample mapping files. Run from `shopify-sample-creator/`.

## Tile Pipeline (`create-tile-v4.py`)

The main processing function is `process_vendor()`, which iterates through every MPL row for a vendor and builds a dict of lists that becomes the output DataFrame.

### Processing Flow

1. `main()` loads MPL via `et.get_tile_mpl_itshare()` and classification taxonomy via `et.get_classification_table_itshare()`
2. User selects warning handling (resolve unrecognized filter terms interactively vs. suppress)
3. User selects all vendors or one vendor to process
4. For each vendor, `process_vendor()` is called which:
   - Calls `get_metafields2()` to compute pricing/calculator metafields into a secondary DataFrame indexed by SKU
   - Iterates each row to populate `out_data` dict with product-level and variant-level fields
   - Validates via `get_status()` — products that fail are removed and added to `rejected_product_list`
5. Outputs per-vendor `.xlsx`, combined `ALL-VENDORS-IMPORT.xlsx`, and `REJECTED_PRODUCTS_v3.xlsx`

### Product Validation (`get_status()`)

Returns `Draft` if valid, or an error code if rejected:
- `inactive-001`: PRICELIST STATUS is INACTIVE
- `inactive-002`: Missing COST/UOM
- `inactive-003`: Missing SELL UNIT
- `inactive-004`: Missing weight data
- `inactive-005`: Zero weight (unless product is Slab or Prefab)

### Title Generation

`get_proposed_new_title()` builds titles from column formulas based on `pricelist.class`:
- **TILE**: SERIES + COLOR + SIZE + SPECIAL ATTRIBUTE + FINISH + MATERIAL
- **MOSAIC**: SERIES + COLOR + MOSAIC CHIP SIZE + MOSAIC CHIP SHAPE + SPECIAL ATTRIBUTE + FINISH + MATERIAL + pricelist.class
- **TRIM**: SERIES + COLOR + SIZE + SPECIAL ATTRIBUTE + FINISH + MATERIAL + PIECE TYPE

`build_title_from_formula()` skips terms already present in the title (case-insensitive dedup) and handles multi-finish values with "and" joining.

### Filter Resolution System

`resolve_filter()` is the core function. It takes an MPL column value, looks it up in `term_dict.json` synonym lists, and returns the standardized Shopify filter term. When a term is unrecognized and warnings are enabled, the user is prompted to either map it as a synonym (updates `term_dict.json` on disk) or skip it for the session.

Filter functions that delegate to `resolve_filter()`:
- `get_color_filter()` — `BASE COLOR` column → `colors` dict
- `get_material_filter()` — `MATERIAL` column → `materials` dict
- `get_finish_filter()` — `FINISH` column → `finishes` dict
- `get_application_filter()` — `RESIDENTIAL APPLICATION` column → `residential_applications` dict
- `get_look_filter()` — `LOOK` column → `looks` dict
- `get_mosaic_shape_filter()` — uses classification taxonomy `TYPE` when `CLASS` is MOSAIC, falls back to `MOSAIC SHAPE (FILTER)` MPL column

`get_size_filter()` and `get_size_display_filter()` do not use `term_dict.json` — they parse dimension strings, convert fractions to decimals, sort dimensions, and round to integers.

### Pricing Logic (`get_metafields2()`)

Computes `cost_sell_unit` and `msrp_sell_unit` by multiplying the per-UOM cost/price by the appropriate conversion factor based on UOM→SELL UNIT combinations:
- SF→SF: direct (1:1)
- SF→EA/SHT: multiply by SF/EA
- SF→BX/SET: multiply by SF/BX
- EA/SHT→EA/SHT: direct
- EA/SHT→BX: multiply by EA/BX

If PRICE/UOM is missing, MSRP defaults to 2× cost.

### Handle Generation

`build_handle()` concatenates SERIES + COLOR + FINISH + pricelist.class + SIZE + E SKU, lowercases, removes accents and special chars, replaces spaces with dashes.

### Tags

`generate_tags()` produces comma-separated tags combining:
1. Series tag: `series-{cleaned-series-name}`
2. Series handle: `{vendor-number}-series-{name}` (vendor number strips leading zeros from E code)
3. Additional tags from filter columns (LOOK, APPLICATION, MATERIAL, COLOR, TYPE, FINISH, SHAPE, FORMAT, THICKNESS, OTHER)

## Tool Pipeline (`create-tool-v2.py`)

Simpler than tile — no filter resolution, no classification taxonomy, no product validation beyond ACTIVE status. Tool-specific metafields include: brand, tool categories, tool type, metal trim attributes, tile spacer attributes, blade attributes, grout attributes, trowel attributes.

Key differences from tile:
- Type is `Tools` instead of `Building Materials`
- Title comes directly from `SHOPIFY NAME` column (no formula generation)
- Handle comes directly from `HANDLE` column
- Uses `et.get_tool_mpl_itshare()` for data
- Brand mapping via `et.get_tool_brand_mapping()`

## Sample Pipeline (`create-samples v2.py`)

Generates Shopify import files for cut sample products. Filters MPL to rows where `HAS CUT SAMPLE == 'YES'` and `PRICELIST STATUS == 'ACTIVE'`.

Processing:
1. Looks up each sample's image from the image manifest (checks `m1` then `m3` folders)
2. Builds sample product with handle `{e-sku}-s`, title `SAMPLE - {SHOPIFY NAME}`
3. Sets template suffix to `sample-noform`, price/cost to 0, shipping profile to `Sample Products`
4. Creates a second file mapping real products to their samples via `Metafield: sample.sku` and `Metafield: custom.sample_product`

## Output Directories

All output folders are gitignored:
- `shopify-item-creator/Import Files/` — Shopify tile and tool import spreadsheets
- `shopify-item-creator/Filtered Data/` — intermediate filtered data (tool pipeline)
- `shopify-sample-creator/cut samples out/` — sample import spreadsheets
- `shopify-sample-creator/real product mapping/` — real-to-sample mapping spreadsheets

## `term_dict.json`

Located at `shopify-item-creator/Scripts/term_dict.json`. Structure is `{ category: { STANDARD_TERM: [synonym1, synonym2, ...] } }`. The tile pipeline modifies this file at runtime when users add new synonyms via `add_synonym_to_filter_dictionary()`. Categories: `colors`, `finishes`, `materials`, `residential_applications`, `commercial_applications`, `looks`, `mosaic_shapes`, `piece_type`, `styles`.
