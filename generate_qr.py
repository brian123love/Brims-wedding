import pandas as pd
import qrcode
import uuid
import os
import re

RENDER_URL = ""

# Create folder for QR codes 
os.makedirs("qr_codes", exist_ok=True)

# Load CSV
if os.path.exists("guests_with_ids.csv"):
    guests = pd.read_csv("guests_with_ids.csv")
else: 
    try:
        guests = pd.read_csv("guests.csv")
    except FileNotFoundError:
        # Create an empty DataFrame if no CSV exists yet
        guests = pd.DataFrame(columns=["name", "email", "unique_id", "checked_in"])

# Ensure required columns exist
for col in ["unique_id", "checked_in", "email"]:
    if col not in guests.columns:
        guests[col] = None if col != "checked_in" else "NO"

print("--- QR Management System ---")
print("1 - Generate QR for ALL existing guests")
print("2 - Add SINGLE new guest")
print("3 - Add MULTIPLE guests (Bulk last minute)")

choice = input("Enter 1, 2, or 3: ").strip()

# =========================
# MODE 1: GENERATE ALL
# =========================
if choice == "1":
    for index, row in guests.iterrows():
        # Only generate new UUID if missing
        if pd.isna(row["unique_id"]) or row["unique_id"] == "":
            guests.at[index, "unique_id"] = str(uuid.uuid4())

        name = str(row["name"])
        uid = guests.at[index, "unique_id"]

        data = f"{RENDER_URL}/checkin?id={uid}"
        img = qrcode.make(data)

        # Sanitize filename
        safe_name = re.sub(r"[^\w]", "_", name).strip()
        img.save(f"qr_codes/{safe_name}.png")
        print(f"✅ QR generated for {name}")

    guests.to_csv("guests_with_ids.csv", index=False)
    print("\n✅ All QR codes have been generated successfully!")

# =========================
# MODE 2: ADD SINGLE GUEST
# =========================
elif choice == "2":
    name = input("Enter guest full name: ").strip()
    email = input("Enter guest email: ").strip()

    if name.lower() in guests["name"].str.lower().values:
        print("⚠️ This guest already exists in the system.")
    else:
        new_uid = str(uuid.uuid4())
        new_row = {"name": name, "email": email, "unique_id": new_uid, "checked_in": "NO"}
        guests = pd.concat([guests, pd.DataFrame([new_row])], ignore_index=True)
        
        # Save and Generate
        img = qrcode.make(f"{RENDER_URL}/checkin?id={new_uid}")
        safe_name = re.sub(r"[^\w]", "_", name).strip()
        img.save(f"qr_codes/{safe_name}.png")
        
        guests.to_csv("guests_with_ids.csv", index=False)
        print(f"✅ QR generated and guest saved for: {name}")

# =========================
# MODE 3: ADD MULTIPLE GUESTS (NEW)
# =========================
elif choice == "3":
    try:
        count_input = input("How many guests do you want to add? (e.g., 10): ")
        count = int(count_input)
        new_entries = []

        for i in range(count):
            print(f"\n--- Guest {i+1} of {count} ---")
            m_name = input("Full Name: ").strip()
            m_email = input("Email: ").strip()

            # Check for duplicates within the current list and the main file
            if m_name.lower() in guests["name"].str.lower().values:
                print(f"⚠️ {m_name} is already in the list. Skipping...")
                continue
            
            m_uid = str(uuid.uuid4())
            new_entries.append({
                "name": m_name,
                "email": m_email,
                "unique_id": m_uid,
                "checked_in": "NO"
            })

        if new_entries:
            # Update the main DataFrame
            new_df = pd.DataFrame(new_entries)
            guests = pd.concat([guests, new_df], ignore_index=True)
            
            # Save CSV
            guests.to_csv("guests_with_ids.csv", index=False)

            # Generate QR codes for the new batch
            print("\nGenerating QR codes...")
            for entry in new_entries:
                data = f"{RENDER_URL}/checkin?id={entry['unique_id']}"
                img = qrcode.make(data)
                safe_name = re.sub(r"[^\w]", "_", entry['name']).strip()
                img.save(f"qr_codes/{safe_name}.png")
                print(f"✅ QR ready for: {entry['name']}")
            
            print(f"\n🚀 Successfully added and generated {len(new_entries)} guests!")
        else:
            print("No new guests were added.")

    except ValueError:
        print("❌ Invalid input. Please enter a number.")

else:
    print("❌ Invalid choice. Please restart and select 1, 2, or 3.")
