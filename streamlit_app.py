import streamlit as st
import psycopg2
from datetime import datetime, timedelta
from PIL import Image
import pytesseract
import re
import io
import pytz

DB_URL = st.secrets["NEON_DATABASE_URL"]

def get_conn():
    return psycopg2.connect(DB_URL)

with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fridge_items (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                expiry DATE
            )
        """)
        conn.commit()

def extract_expiry_with_ocr(file):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
        if match:
            try:
                return datetime.strptime(match.group(1), "%m/%d/%Y").date()
            except ValueError:
                return datetime.strptime(match.group(1), "%m/%d/%y").date()
    except Exception as e:
        st.warning(f"OCR failed: {e}")
    return None

st.title("🥕 SpoilSense – Reduce Food Waste")

st.header("➕ Add a new food item")
camera_file = st.camera_input("Snap your food item")

if camera_file and st.button("Save Item"):
    file_bytes = io.BytesIO(camera_file.getvalue())
    expiry = extract_expiry_with_ocr(file_bytes)
    product_name = f"item_{int(datetime.now().timestamp())}"  # unique auto-name

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO fridge_items (name, expiry) VALUES (%s, %s)",
                (product_name, expiry)
            )
            conn.commit()
    st.success(f"Saved {product_name} expiring on {expiry}")

st.header("📅 Items expiring tomorrow")

local_tz = pytz.timezone("America/Los_Angeles")
today_local = datetime.now(local_tz).date()
tomorrow_local = today_local + timedelta(days=1)

with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT name, expiry FROM fridge_items WHERE expiry = %s ORDER BY expiry",
            (tomorrow_local,)
        )
        expiring = cur.fetchall()

if not expiring:
    st.info("No items expiring tomorrow 🎉")
else:
    for name, expiry in expiring:
        st.subheader(name)
        st.write(f"Expiration date: {expiry}")