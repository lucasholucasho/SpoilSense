import streamlit as st
import json
import os
from datetime import datetime, timedelta
from PIL import Image
import pytesseract
import re

DATA_FILE = "fridge_items.json"

# --- Load/save data ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- OCR with Tesseract ---
def extract_expiry_with_ocr(file):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)
        # Look for MM/DD/YYYY or MM/DD/YY
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
        if match:
            try:
                return datetime.strptime(match.group(1), "%m/%d/%Y").date()
            except ValueError:
                return datetime.strptime(match.group(1), "%m/%d/%y").date()
    except Exception as e:
        st.warning(f"OCR failed: {e}")
    return None

# --- UI ---
st.title("🥕 SpoilSense – Reduce Food Waste")

st.header("➕ Add a new food item")
camera_file = st.camera_input("Snap your food item")

if camera_file and st.button("Save Item"):
    items = load_data()
    expiry = extract_expiry_with_ocr(camera_file)
    product_name = f"item_{len(items)+1}"  # simple auto-name
    items.append({"name": product_name, "expiry": str(expiry)})
    save_data(items)
    st.success(f"Saved {product_name} expiring on {expiry}")

# --- Show expiring items ---
st.header("📅 Items expiring tomorrow")
items = load_data()
tomorrow = (datetime.today() + timedelta(days=1)).date()
expiring = [item for item in items if item["expiry"] and datetime.fromisoformat(item["expiry"]).date() == tomorrow]

if not expiring:
    st.info("No items expiring tomorrow 🎉")
else:
    for item in expiring:
        st.subheader(item["name"])