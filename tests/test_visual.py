from seleniumbase import BaseCase
import os

class VisualTest(BaseCase):
    def test_spoilsense_visual(self):
        # Start the Streamlit app (you'd need to run this separately)
        # self.open("http://localhost:8501")
        
        # For demonstration purposes only
        # In a real test, you'd start the Streamlit server first
        if os.environ.get("STREAMLIT_TEST_URL"):
            self.open(os.environ.get("STREAMLIT_TEST_URL"))
            self.assert_text("SpoilSense")
            self.check_window(name="spoilsense_main", level=2)