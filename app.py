import streamlit as st
import pandas as pd
import os
import re

def extract_size(note):
    if pd.isna(note):
        return ""
    match = re.search(r"(\d{2,3})\s?kg", note.lower())
    return f"{match.group(1)}kg" if match else ""

def generate_product_name_mapping(df):
    name_map = {}
    counters = {}
    for idx, row in df.iterrows():
        original = row['TÊN SẢN PHẨM']
        original_stripped = original.strip()
        if original_stripped not in counters:
            counters[original_stripped] = 1
        else:
            counters[original_stripped] += 1
        stt = counters[original_stripped]

        # Bỏ 3 ký tự đầu
        new_base_name = original_stripped[3:].strip()
        new_name = f"{new_base_name} D.12.6.{stt}"

        size = extract_size(str(row.get('GHI CHÚ', '')))
        full_note = f"{new_name} [{original_stripped} {size}] - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"

        name_map[idx] = {
            "new_name": new_name,
            "full_note": full_note
        }
    return name_map

def apply_mau_chi_thuy(df):
    mapping = generate_product_name_mapping(df)
    for idx, update in mapping.items():
        df.at[idx, 'TÊN SẢN PHẨM'] = update['new_name']
        df.at[idx, 'GHI CHÚ'] = update['full_note']
    return df

st.title("GHN Excel Processor")

template_option = st.selectbox("Chọn mẫu xử lý", ["Chị Tiền", "Chị Linh", "Chị Thúy"])

uploaded_files = st.file_uploader("Tải lên file Excel", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        st.write(f"Đang xử lý: {file.name}")
        df = pd.read_excel(file)

        if template_option == "Chị Tiền":
            st.dataframe(df)
        elif template_option == "Chị Linh":
            st.dataframe(df)
        elif template_option == "Chị Thúy":
            df = apply_mau_chi_thuy(df)
            st.dataframe(df)

        # Xuất file
        output_file = file.name.replace(".xlsx", f" - Xuất theo mẫu {template_option}.xlsx")
        df.to_excel(output_file, index=False)
        with open(output_file, "rb") as f:
            st.download_button(
                label="Tải về file đã xử lý",
                data=f,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        os.remove(output_file)
