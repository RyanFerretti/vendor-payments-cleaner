import io
import os
import streamlit as st
import pandas as pd
from converter import convert_csv_text, convert_dataframe

st.set_page_config(page_title="Payments Converter", initial_sidebar_state="auto")
st.title("Payments Converter")
st.write("Upload a CSV or Excel file. The app will apply the conversion rules and let you download a cleaned CSV.")

uploaded_file = st.file_uploader("Choose a file", type=["csv", "xls", "xlsx"])

if uploaded_file is not None:
    try:
        is_excel = uploaded_file.name.lower().endswith((".xls", ".xlsx"))

        if is_excel:
            df = pd.read_excel(uploaded_file, skiprows=3, dtype=str)
            cleaned_df = convert_dataframe(df)
            csv_buffer = io.StringIO()
            cleaned_df.to_csv(csv_buffer, index=False)
            csv_text = csv_buffer.getvalue()
            preview_df = cleaned_df
        else:
            input_text = uploaded_file.getvalue().decode("utf-8")
            csv_text = convert_csv_text(input_text)
            # Build a preview from the data section only (skip preamble + header).
            preview_df = pd.read_csv(io.StringIO(csv_text), skiprows=3, dtype=str)

        st.subheader("Preview (first 50 rows)")
        st.dataframe(preview_df.head(50))

        base_name = os.path.splitext(uploaded_file.name)[0]
        out_name = f"{base_name}_Cleaned.csv"
        st.download_button(
            label="Download cleaned CSV",
            data=csv_text.encode("utf-8"),
            file_name=out_name,
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Failed to process file: {e}")
