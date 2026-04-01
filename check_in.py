import pandas as pd
import qrcode
from pyzbar.pyzbar import decode
from PIL import Image

#Load guests list with unique IDs
guests = pd.read_csv("guests_with_ids.csv")

#Load the QR image to scan (example: Ana_Said.png)
img = Image.open("qr_codes/Colin_Amani.png")  #change to the actual filename you want to scan result=decode(img)
result = decode(img)

if result:
    scanned_data = result[0].data.decode("utf-8")
    scanned_id = scanned_data.split("ID: ")[-1].strip()

    # Check if the ID exists in the guest list
    match = guests[guests['unique_id'] == scanned_id]
    if not match.empty:
        name = match.iloc[0]['name']
        print(f"✅ {name} Access granted.")
    else:
        print("❌ Guest not found in the list.")
else:
    print("⚠️ QR code not read.")


