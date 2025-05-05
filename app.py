import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("📦 Upload & Chuẩn hóa File Excel giao hàng")

EXPECTED_COLUMNS = [
    "mã đơn hàng", "ghi chú nội bộ", "stt", "họ tên", "số điện thoại", "địa chỉ",
    "tên hàng", "size", "tiền thu hộ", "ngày tạo", "nguồn đơn hàng", "người tạo"
]

REQUIRED_FIELDS = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size"]

def is_probably_header(row):
    return any(str(v).lower() in ["tên", "họ tên", "sđt", "sdt", "địa chỉ", "tên hàng"] for v in row)

def auto_detect_header(df):
    first_row = df.iloc[0].tolist()
    return is_probably_header(first_row)

def convert_no_header(df):
    df.columns = EXPECTED_COLUMNS[:len(df.columns)]
    return df

def guess_column(df, keywords):
    for keyword in keywords:
        for col in df.columns:
            if keyword.lower() in str(col).lower():
                return col
    return None

def prepare_dataframe(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    all_dfs = []
    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name, header=None)
        if auto_detect_header(df):
            df = xls.parse(sheet_name)  # reread with header
        else:
            df = convert_no_header(df)
        df["__sheet__"] = sheet_name
        all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)

uploaded_files = st.file_uploader("📁 Tải lên file Excel", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    full_df = pd.DataFrame()
    for uploaded_file in uploaded_files:
        df = prepare_dataframe(uploaded_file)
        full_df = pd.concat([full_df, df], ignore_index=True)

    st.subheader("📋 Xem trước dữ liệu")
    st.dataframe(full_df.head(20))

    st.markdown("### 🧠 Mapping cột")

    # Mapping thông minh hoặc thủ công
    col_mapping = {}
    for field in REQUIRED_FIELDS:
        guessed = guess_column(full_df, [field])
        col_mapping[field] = st.selectbox(f"🧩 Chọn cột cho '{field}'", full_df.columns, index=full_df.columns.get_loc(guessed) if guessed in full_df.columns else 0)

    missing = [f for f, c in col_mapping.items() if c not in full_df.columns]
    if missing:
        st.error(f"❌ Thiếu các cột: {', '.join(missing)}")
    else:
        st.success("✅ Đã ánh xạ đầy đủ các cột")

        st.markdown("### 📦 Kết quả sau chuẩn hóa:")
        output = pd.DataFrame({
            "Họ tên": full_df[col_mapping["họ tên"]],
            "SĐT": full_df[col_mapping["số điện thoại"]],
            "Địa chỉ": full_df[col_mapping["địa chỉ"]],
            "Tên hàng": full_df[col_mapping["tên hàng"]],
            "Size": full_df[col_mapping["size"]],
            "Tiền thu hộ": full_df[col_mapping.get("tiền thu hộ", 0)] if "tiền thu hộ" in col_mapping else 0,
        })

        st.dataframe(output)

        csv = output.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Tải file kết quả", data=csv, file_name="don_hang_xuat_ra.csv", mime="text/csv")
