import streamlit as st
import json
import os
from datetime import datetime, timedelta
import requests
import re

DATA_FILE = "fridge_items.json"
OCR_API_KEY = "K86661616188957"

# --- Data handling ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- OCR using OCR.Space ---
def extract_expiry_with_ocr(file):
    try:
        # Prepare file for OCR.Space
        files = {"file": file.getvalue()}
        payload = {"apikey": OCR_API_KEY, "language": "eng"}

        response = requests.post("https://api.ocr.space/parse/image", files=files, data=payload)
        result = response.json()
        text = result["ParsedResults"][0]["ParsedText"]

        # Match MM/DD/YYYY or MM/DD/YY
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
        if match:
            return datetime.strptime(match.group(1), "%m/%d/%Y").date()
    except Exception as e:
        st.warning(f"OCR failed: {e}")
    return None

# --- Streamlit UI ---
st.title("🥕 SpoilSense – Reduce Food Waste")

# Camera input
st.header("➕ Add a new food item")
camera_file = st.camera_input("Take a picture of your food item")

if camera_file and st.button("Save Item"):
    items = load_data()
    expiry = extract_expiry_with_ocr(camera_file)

    product_name = f"item_{len(items)+1}"  # simple auto-name
    items.append({"name": product_name, "expiry": str(expiry)})
    save_data(items)
    st.success(f"Saved {product_name} expiring on {expiry}")

# Show items expiring tomorrow
st.header("📅 Items expiring tomorrow")
items = load_data()
tomorrow = (datetime.today() + timedelta(days=1)).date()

expiring = [item for item in items if datetime.fromisoformat(item["expiry"]).date() == tomorrow]

if not expiring:
    st.info("No items expiring tomorrow 🎉")
else:
    for item in expiring:
        st.subheader(item["name"])