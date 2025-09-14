import streamlit as st
import os
import re
from datetime import datetime, timedelta
from PIL import Image
import pytesseract
import psycopg2

# --- Database setup ---
DB_URL = st.secrets["NEON_DATABASE_URL"]  # Add this to your secrets.toml
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS fridge_items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    expiry DATE
)
""")
conn.commit()

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
    expiry = extract_expiry_with_ocr(camera_file)
    product_name = f"item_{datetime.now().strftime('%Y%m%d%H%M%S')}"  # unique auto-name

    cur.execute(
        "INSERT INTO fridge_items (name, expiry) VALUES (%s, %s)",
        (product_name, expiry)
    )
    conn.commit()
    st.success(f"Saved {product_name} expiring on {expiry}")

# --- Show expiring items ---
st.header("📅 Items expiring tomorrow")
tomorrow = (datetime.today() + timedelta(days=1)).date()
st.header(tomorrow)

cur.execute("SELECT name, expiry FROM fridge_items WHERE expiry = %s", (tomorrow,))
expiring = cur.fetchall()

if not expiring:
    st.info("No items expiring tomorrow 🎉")
else:
    for name, expiry_date in expiring:
        st.subheader(name)
        st.write(f"Expires on: {expiry_date}")

# --- Close DB connection ---
cur.close()
conn.close()