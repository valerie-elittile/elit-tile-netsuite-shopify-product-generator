import pandas as pd
import numpy as np
import sys
import os
import re
import ETlib as et
import qrcode

def generate_small_qr_code(data, file_name):
    qr = qrcode.QRCode(
        version=1,  # Choose the QR code version (1 to 40, higher values for larger codes)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Set error correction level
        box_size=2,  # Set the size of each box (pixels)
        border=1,  # Set the size of the border (box_size * border)
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Generate QR code image file
    qr.make_image(fill_color="black", back_color="white").save(".\\qrs\\"+file_name)

if not os.path.exists('qrs'):
    os.mkdir('qrs')


#------------------------------------------Code starts here---------------------------------------------------------------#

ftp = et.ftp_login()

active_vendors = et.get_tile_vendors()

ven_code = input('Enter vendor code(not case sensitive): ').upper()

out = {
    'SKU': [],
    'VEN CODE': [],
    'QR FILENAME': [],
    'QR URL': [],
    'PRODUCT ID': [],
    'VARIANT ID': [],
    'VARIANT INVENTORY ID': []
}

mpl = et.get_tile_mpl_by_vendor(ftp,ven_code)

mpl_for_sample = mpl[(mpl['HAS CUT SAMPLE'] == 'YES') & (mpl['PRICELIST STATUS'] == 'ACTIVE')]
mpl_for_sample = mpl_for_sample.reset_index(drop=True)

for i, r in mpl_for_sample.iterrows():

    if not os.path.exists(f'qrs/{ven_code}'):
        os.mkdir(f'qrs/{ven_code}')

    sku = r['E SKU']
    handle = r['HANDLE']

    qr_fn = f'{ven_code}/{str(sku)}.png'
    qr_url = "elittile.com/products/"+str(handle)

    generate_small_qr_code(qr_url, qr_fn)
    print(f'Created {qr_fn}')


print("Task Complete!")