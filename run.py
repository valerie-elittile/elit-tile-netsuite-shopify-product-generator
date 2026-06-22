import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

SCRIPTS = {
    "shopify-tile":     ROOT / "shopify/shopify-item-creator/Scripts/create-tile-v4.py",
    "shopify-tool":     ROOT / "shopify/shopify-item-creator/Scripts/create-tool-v2.py",
    "shopify-samples":  ROOT / "shopify/shopify-sample-creator/create-samples-v2.py",
    "netsuite-real":    ROOT / "netsuite/netsuite-item-creator/real_prod.py",
    "netsuite-samples": ROOT / "netsuite/netsuite-item-creator/sample_prod.py",
    "images-manifest":  ROOT / "images/et-img-manifest/create-image-manifest.py",
    "images-import":    ROOT / "images/et-image-import-creator/et-image-import-creator.py",
    "qr-generate":      ROOT / "qr-code/qr code generator/qr-code.py",
    "qr-check":         ROOT / "qr-code/qr code generator/check-404.py",
}

parser = argparse.ArgumentParser(description="Elit Tile data pipeline runner")
parser.add_argument("task", choices=SCRIPTS.keys(), help="Which script to run")
parser.add_argument("--vendor", nargs="+", help="Vendor code(s) e.g. E0164 E0991")
args = parser.parse_args()

script = SCRIPTS[args.task]
env = None
if args.vendor:
    import os
    env = {**os.environ, "ET_VENDORS": ",".join(v.upper() for v in args.vendor)}

subprocess.run([sys.executable, str(script)], cwd=script.parent, env=env)
