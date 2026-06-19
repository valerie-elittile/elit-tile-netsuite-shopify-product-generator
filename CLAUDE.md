# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based data pipeline for **Elit Tile** that generates bulk import files for **NetSuite** (ERP) and **Shopify** (e-commerce). It reads product data from a Master Price List (MPL), transforms it, and outputs CSV/XLSX files formatted for each platform's import requirements. There are two product categories: **Tile** and **Tool**, each with separate processing logic.

## Running Scripts

All scripts are interactive CLI tools that prompt for vendor codes (e.g., `E0164`, `E0991`) and processing options. Run them with `python <script>` from their respective directories.

| Task | Script | Run From |
|------|--------|----------|
| Shopify tile/tool import (entry point) | `shopify/shopify-item-creator/create-item.py` | `shopify/shopify-item-creator/` |
| Shopify tile import (direct, current) | `shopify/shopify-item-creator/Scripts/create-tile-v4.py` | `shopify/shopify-item-creator/Scripts/` |
| Shopify tool import (multi-vendor) | `shopify/shopify-item-creator/Scripts/create-tool-v2.py` | `shopify/shopify-item-creator/Scripts/` |
| Shopify sample products | `shopify/shopify-sample-creator/create-samples v2.py` | `shopify/shopify-sample-creator/` |
| NetSuite real product import | `netsuite/netsuite-item-creator/real_prod.py` | `netsuite/netsuite-item-creator/` |
| NetSuite sample product import | `netsuite/netsuite-item-creator/sample_prod.py` | `netsuite/netsuite-item-creator/` |
| Image manifest (FTP scan) | `images/et-img-manifest/create-image-manifest.py` | `images/et-img-manifest/` |
| Image import file | `images/et-image-import-creator/et-image-import-creator.py` | `images/et-image-import-creator/` |
| QR code generation | `qr-code/qr code generator/qr-code.py` | `qr-code/qr code generator/` |
| QR code 404 checker | `qr-code/qr code generator/check-404.py` | `qr-code/qr code generator/` |

Scripts must be run from their own directory because they use relative paths for output folders and `subprocess` calls.

## Dependencies

Core: `pandas`, `numpy`, `openpyxl`, `xlsxwriter`
QR tools: `qrcode`, `pyzbar`, `Pillow`, `requests`

There is no `requirements.txt` or `pyproject.toml` — install packages manually with pip.

## Architecture

### ETlib (shared library)

`ETlib.py` is gitignored and must exist at the repo root. Every script imports it as `import ETlib as et`. It provides:
- **FTP access**: `et.ftp_login()` connects to the tiledata.net FTP server hosting product images and data files
- **MPL data loaders**: `et.get_tile_mpl_itshare()`, `et.get_tool_mpl_itshare()`, `et.get_tile_mpl_ftpserver(ftp)`, `et.get_tool_mpl_by_vendor_2(ven_code)` — reads the Master Price List from IT Share (network/SharePoint) or FTP
- **Vendor mappings**: `et.get_tile_vendors()`, `et.get_tool_vendors()`, `et.get_all_vendors()`, `et.get_retail_vendor_mapping()`, `et.get_tool_brand_mapping()`
- **UOM/unit mappings**: `et.get_uom_mapping()`, `et.get_sell_unit_mapping()`, `et.get_plural_uom_mapping()`, `et.get_unit_plural_mapping()`, `et.get_uom_mapping_abb()`
- **Classification**: `et.get_class_mapping()`, `et.get_classification_table_itshare()`
- **Image manifest**: `et.get_image_manifest(ftp, ven_code)`, `et.get_current_prod(ftp)`
- **Constants**: `et.SKU_PATTERN` (regex for E-code SKUs), `et.tile_vendor_mapping`, `et.tool_vendor_mapping`, `et.inventory_tracked_vendors`
- **Pack info**: `et.get_pack_info_mapping()`

### Data Flow

1. **MPL (Master Price List)** → source of truth for all product data. Loaded via ETlib from either IT Share or FTP. Key columns: `E SKU`, `V SKU`, `VENDOR`, `SERIES`, `COLOR`, `SIZE`, `FINISH`, `UOM`, `SELL UNIT`, `COST/UOM`, `PRICELIST STATUS`, `HAS CUT SAMPLE`, `CLASSIFICATION ID`
2. **Processing scripts** transform MPL rows into platform-specific import formats
3. **Output files** are written to subdirectories (`Import Files/`, `Real Product Add Item Files/`, etc.) — all output folders are gitignored

### Shopify Tile Pipeline (`create-tile-v4.py`)

The most complex script. It:
- Loads MPL + classification taxonomy table from IT Share
- For each vendor, calls `process_vendor()` which builds the full Shopify import DataFrame
- Computes pricing metafields via `get_metafields2()` (cost/MSRP per sell unit, calculator ratios)
- Resolves Shopify filter values (color, material, finish, look, application, mosaic shape) using `term_dict.json` as a synonym dictionary
- Generates product titles from formulas based on `pricelist.class` (TILE, MOSAIC, TRIM)
- Validates products via `get_status()` — rejects items missing cost, weight, sell unit, or marked INACTIVE
- Outputs per-vendor `.xlsx` files plus a combined `ALL-VENDORS-IMPORT.xlsx` and `REJECTED_PRODUCTS_v3.xlsx`

### Filter Synonym System (`term_dict.json`)

Located at `shopify/shopify-item-creator/Scripts/term_dict.json`. Maps raw MPL values to standardized Shopify filter categories. Categories: `colors`, `finishes`, `materials`, `residential_applications`, `commercial_applications`, `looks`, `mosaic_shapes`, `piece_type`, `styles`. During processing, unrecognized terms trigger interactive prompts to add synonyms or skip.

### NetSuite Pipeline

- `real_prod.py` generates two CSVs per vendor: ADD ITEM (product data with vendor/pricing/Shopify fields) and UOM (unit of measure conversion table)
- `sample_prod.py` generates four output sets: E-code samples, E-code sample UOMs, V-code samples, V-code sample UOMs
- Both use ETlib's UOM/vendor mappings extensively
- E0207 has a special warning in sample_prod.py — that vendor does not have automatic samples

### Product Code Conventions

- **E codes** (`E0164`): Elit Tile internal vendor codes, used as the primary vendor identifier
- **E SKU** (`E0164-00001`): Elit Tile product SKU
- **V SKU**: Retail's own SKU for the same product
- **V codes** (`V164`): Retail-facing vendor codes (strip leading zero from E code number)
- Sample SKUs append `-S` (e.g., `E0164-00001-S`, `V164-00001`)

### Image System

Images are hosted on tiledata.net FTP under `ElitTile_images/{vendor_code}/products/{m1-m7}/` (photos) and `ElitTile_images/{vendor_code}/videos/` (motion clips). The image manifest script scans FTP directories, matches filenames to SKUs via regex, and builds a manifest spreadsheet. The image import creator then uses the manifest to generate Shopify image import files with proper URLs.

## Key Conventions

- Vendor codes are always uppercased before use
- All scripts filter to `PRICELIST STATUS == 'ACTIVE'` unless processing rejected/inactive items
- Shopify products default to `Status: Draft`, `Published: FALSE`
- NetSuite subsidiary is always `Elit Tile Consolidated : ElitTile.com` for E-code products
- Location defaults to `LA ElitTile.com` for NetSuite
- `OLD/` subdirectories contain deprecated script versions — do not modify
- Current versions: tile = v4, tool = v2, samples = v2
