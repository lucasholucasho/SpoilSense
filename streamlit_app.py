import streamlit as st
import psycopg2
from datetime import datetime, timedelta
from PIL import Image
import pytesseract
import re
import io
import pytz

# --- Database ---
DB_URL = st.secrets["NEON_DATABASE_URL"]

def get_conn():
    return psycopg2.connect(DB_URL)

# Ensure table exists
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

# --- OCR function ---
def extract_expiry_with_ocr(file):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img).upper()  # uppercase for month matching

        # --- Numeric dates: MM/DD/YYYY or MM/DD/YY ---
        numeric_match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
        if numeric_match:
            try:
                return datetime.strptime(numeric_match.group(1), "%m/%d/%Y").date()
            except ValueError:
                return datetime.strptime(numeric_match.group(1), "%m/%d/%y").date()

        # --- Abbreviated month dates: allow optional prefix like 'BB ' or 'Best by: ' ---
        month_match = re.search(
            r"(?:\w+\s+|[\w\s]+:?\s*)?"            # optional prefix
            r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+"  # month
            r"(\d{1,2})\s+"                        # day
            r"(\d{2,4})",                           # year
            text
        )
        if month_match:
            month_str, day_str, year_str = month_match.groups()
            month_num = datetime.strptime(month_str, "%b").month
            day_num = int(day_str)
            year_num = int(year_str)
            # convert 2-digit year to 4-digit (assume 2000+)
            if year_num < 100:
                year_num += 2000
            return datetime(year=year_num, month=month_num, day=day_num).date()

    except Exception as e:
        st.warning(f"OCR failed: {e}")

    return None

# --- Streamlit UI ---
st.title("🥕 SpoilSense – Reduce Food Waste")

st.header("➕ Add a new food item")

# User can type a name
product_name = st.text_input("Item name", placeholder="e.g., Milk, Tomato Paste")

# Camera input
camera_file = st.camera_input("Snap your food item")

if camera_file and st.button("Save Item"):
    if not product_name:
        st.warning("Please enter a name for the item.")
    else:
        file_bytes = io.BytesIO(camera_file.getvalue())
        expiry = extract_expiry_with_ocr(file_bytes)

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO fridge_items (name, expiry) VALUES (%s, %s)",
                    (product_name, expiry)
                )
                conn.commit()
        st.success(f"Saved {product_name} expiring on {expiry}")

# --- Display items expiring tomorrow ---
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