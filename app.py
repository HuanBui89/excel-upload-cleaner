import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("📦 GHN Excel Upload - Auto + Manual Mapping")

def auto_map_columns(columns):
    mapping = {}
    keywords = {
        "họ tên": ["khách", "họ", "tên", "người nhận"],
        "số điện thoại": ["sdt", "sđt", "điện", "mobile", "số thoại"],
        "địa chỉ": ["địa chỉ", "địa", "dc"],
        "tên hàng": ["sản phẩm", "gồm", "sp", "tên hàng"],
        "size": ["ghi chú", "mô tả", "size"],
        "số tiền thu hộ": ["cod", "thu hộ", "tiền"]
    }
    for key, kws in keywords.items():
        for col in columns:
            for kw in kws:
                if kw in str(col).lower():
                    mapping[key] = col
                    break
            if key in mapping:
                break
    return mapping

uploaded_file = st.file_uploader("📤 Tải lên file Excel", type=["xlsx", "xls"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    all_data = []

    for sheet_name in xls.sheet_names:
        st.subheader(f"📄 Sheet: {sheet_name}")
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        first_row = df_raw.iloc[0].astype(str)
        numeric_count = sum([cell.replace(".", "").isdigit() for cell in first_row])

        if numeric_count >= len(first_row) - 2:
            df = df_raw.copy()
            df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
            try:
                mapping = {
                    "họ tên": df.columns[2],
                    "số điện thoại": df.columns[3],
                    "địa chỉ": df.columns[4],
                    "tên hàng": df.columns[5],
                    "size": df.columns[6],
                    "số tiền thu hộ": df.columns[7],
                }
                show_manual = False
            except IndexError:
                st.error("❌ File không có đủ số cột để mapping theo vị trí cố định (>= 8 cột).")
                continue
        else:
            df = df_raw[1:].copy()
            df.columns = df_raw.iloc[0]
            mapping = auto_map_columns(df.columns)
            show_manual = True

        if show_manual:
            for key in ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]:
                mapping[key] = st.selectbox(f"🔧 Chọn cột cho '{key}'", df.columns, key=key+sheet_name)

        df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " - Size " + df[mapping["size"]].astype(str)
        out_df = pd.DataFrame({
            "Họ tên người nhận": df[mapping["họ tên"]],
            "Số điện thoại người nhận": df[mapping["số điện thoại"]],
            "Địa chỉ": df[mapping["địa chỉ"]],
            "Gói cước": 2,
            "Yêu cầu đơn hàng": 2,
            "Tên sản phẩm": df["tên sản phẩm"],
            "Số lượng": 1,
            "Khối lượng (gram)": 500,
            "Chiều dài (cm)": 10,
            "Chiều rộng (cm)": 10,
            "Chiều cao (cm)": 10,
            "Giá trị hàng hóa": df[mapping["số tiền thu hộ"]],
            "Khai giá (Có/Không)": "x",
            "Tiền thu hộ (COD)": df[mapping["số tiền thu hộ"]],
            "Shop trả phí vận chuyển": "x",
            "Gửi hàng tại bưu cục": "",
            "Mã hàng riêng của shop": "",
            "Ghi chú thêm": "",
            "Ca lấy hàng": 1,
            "Giao thất bại thu tiền": 30000
        })

        all_data.append(out_df)

    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        towrite = io.BytesIO()
        result.to_excel(towrite, index=False, engine="openpyxl")
        st.download_button("📥 Tải file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx")
