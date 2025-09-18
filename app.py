import io
import os
import streamlit as st
import pandas as pd
from converter import convert_dataframe

st.set_page_config(page_title="Payments Converter", initial_sidebar_state="auto")
st.title("Payments Converter")
st.write("Upload a CSV or Excel file. The app will apply the conversion rules and let you download a cleaned CSV.")

uploaded_file = st.file_uploader("Choose a file", type=["csv", "xls", "xlsx"]) 

if uploaded_file is not None:
    try:
        # Load as strings, skip first 3 rows
        if uploaded_file.name.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file, skiprows=3, dtype=str)
        else:
            df = pd.read_csv(uploaded_file, skiprows=3, dtype=str)

        # Convert
        cleaned_df = convert_dataframe(df)

        st.subheader("Preview (first 50 rows)")
        st.dataframe(cleaned_df.head(50))

        # Prepare CSV in memory
        csv_buffer = io.StringIO()
        cleaned_df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode("utf-8")

        base_name = os.path.splitext(uploaded_file.name)[0]
        out_name = f"{base_name}_Cleaned.csv"
        st.download_button(
            label="Download cleaned CSV",
            data=csv_bytes,
            file_name=out_name,
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Failed to process file: {e}")
