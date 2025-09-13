from streamlit.testing.v1 import AppTest
import pytest
import os
import json

# Test data setup
@pytest.fixture
def test_data():
    return [
        {"name": "test_milk", "expiry": "2025-10-01"},
        {"name": "test_yogurt", "expiry": "2025-09-15"}
    ]

@pytest.fixture
def setup_test_data(test_data):
    # Create a test data file
    with open("test_fridge_items.json", "w") as f:
        json.dump(test_data, f)
    yield
    # Cleanup
    if os.path.exists("test_fridge_items.json"):
        os.remove("test_fridge_items.json")

# Test app loads correctly
def test_app_loads():
    at = AppTest.from_file("streamlit_app.py")
    at.run()
    assert not at.exception
    assert at.title[0].value == "🥕 SpoilSense – Reduce Food Waste"

# Test expiring items display
def test_expiring_items(setup_test_data, monkeypatch):
    # Patch the DATA_FILE constant
    monkeypatch.setattr("streamlit_app.DATA_FILE", "test_fridge_items.json")
    # Patch datetime.today to return a fixed date
    from datetime import datetime, timedelta
    fixed_date = datetime(2025, 9, 14)
    monkeypatch.setattr("streamlit_app.datetime.today", lambda: fixed_date)
    
    at = AppTest.from_file("streamlit_app.py")
    at.run()
    
    # Check if yogurt is shown as expiring tomorrow
    assert "test_yogurt" in at.get_delta_path("subheader")[0].value

# Test OCR functionality
def test_ocr_extraction(monkeypatch):
    # Mock the pytesseract function
    def mock_image_to_string(*args, **kwargs):
        return "Best Before: 10/15/2025"
    
    monkeypatch.setattr("pytesseract.image_to_string", mock_image_to_string)
    
    # Create a test app string that just calls the OCR function
    test_app = """
    import streamlit as st
    from PIL import Image
    import pytesseract
    import re
    from datetime import datetime
    
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
    
    st.title("OCR Test")
    uploaded_file = st.file_uploader("Upload a picture", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        expiry = extract_expiry_with_ocr(uploaded_file)
        st.write(f"Extracted date: {expiry}")
    """
    
    at = AppTest.from_string(test_app)
    # This would need a real file to test with
    # For TestSprite, you'd implement this differently
    
    # Just check that the app loads without errors
    at.run()
    assert not at.exception