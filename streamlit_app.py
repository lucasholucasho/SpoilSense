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