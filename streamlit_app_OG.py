import streamlit as st
import json
import os
from datetime import datetime, timedelta
from gpt4all import GPT4All
from PIL import Image
import pytesseract
import re

DATA_FILE = "fridge_items.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def extract_expiry_with_ocr(file):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)
        # Try to match MM/DD/YYYY or MM/DD/YY
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
        if match:
            return datetime.strptime(match.group(1), "%m/%d/%Y").date()
    except Exception as e:
        st.warning(f"OCR failed: {e}")
    return None

@st.cache_resource
def load_model():
    return GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

model = load_model()

st.title("🥕 SpoilSense – Reduce Food Waste")

st.header("➕ Add a new food item")
uploaded_file = st.file_uploader("Upload a picture of the item", type=["jpg", "jpeg", "png"])

if uploaded_file and st.button("Save Item"):
    items = load_data()
    expiry = extract_expiry_with_ocr(uploaded_file)

    product_name = os.path.splitext(uploaded_file.name)[0]  # filename as name
    items.append({"name": product_name, "expiry": str(expiry)})
    save_data(items)
    st.success(f"Saved {product_name} expiring on {expiry}")

st.header("📅 Items expiring tomorrow")
items = load_data()
tomorrow = (datetime.today() + timedelta(days=1)).date()

expiring = [item for item in items if datetime.fromisoformat(item["expiry"]).date() == tomorrow]

if not expiring:
    st.info("No items expiring tomorrow 🎉")
else:
    for item in expiring:
        st.subheader(item["name"])
        if item.get("ocr_text"):
            with st.expander("OCR text / debug"):
                st.code(item["ocr_text"])

        question = f"Can you eat/drink {item['name']} on its own? Answer Yes or No only."
        # with st.expander("LLM question"):
        #     st.write(question)

        with model.chat_session():
            consumable_resp = model.generate(
                question,
                max_tokens=50
            ).strip().lower()

        # st.write("LLM answer:", consumable_resp)

        if "yes" in consumable_resp:
            st.success("✅ Consumable on its own")
        else:
            with model.chat_session():
                recipe = model.generate(
                    f"Suggest a simple, quick recipe using {item['name']} as the main ingredient.",
                    max_tokens=350
                )
            st.warning("🍴 Needs a recipe:")
            st.write(recipe)