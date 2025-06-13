import streamlit as st
import pandas as pd
import io
import hashlib
import os
import tempfile
from datetime import datetime
import re
from collections import defaultdict
import streamlit.components.v1 as components

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 APP TẠO ĐƠN THEO MẮU GHN")

log_file = "history_logs.csv"
if not os.path.exists(log_file):
    pd.DataFrame(columns=["Time", "Filename", "Total Orders"]).to_csv(log_file, index=False)

if "template_option" not in st.session_state:
    st.session_state.template_option = "Mẫu 2 - Chị Linh"

template_labels = {
    "Mẫu 1 - Chị Tiền": "📗 Mẫu 1 - Chị Tiền",
    "Mẫu 2 - Chị Linh": "📕 Mẫu 2 - Chị Linh",
    "Mẫu 3 - Chị Thúy": "📘 Mẫu 3 - Chị Thúy"
}
label_to_value = {v: k for k, v in template_labels.items()}
def_option = template_labels[st.session_state.get("template_option", "Mẫu 2 - Chị Linh")]

selected_label = st.selectbox("📝 Chọn mẫu xuất kết quả:", list(template_labels.values()), index=list(template_labels.values()).index(def_option), key="template_label")
st.session_state.template_option = label_to_value[selected_label]
template_option = st.session_state.template_option

def auto_map_columns(columns):
    mapping = {}
    keywords = {
        "họ tên": ["khách", "họ", "tên", "khách hàng"],
        "số điện thoại": ["sdt", "sđt", "điện", "mobile"],
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

def is_valid_row(row):
    phone_pattern = re.compile(r"\b0\d{9,10}\b")
    cod_pattern = re.compile(r"\b\d{5,}\b")
    row_str = " ".join([str(cell) for cell in row])
    if phone_pattern.search(row_str) and cod_pattern.search(row_str):
        return True
    keywords = ['khách hàng', 'tổng', 'số lượng', 'sản phẩm', 'địa chỉ']
    if any(kw in row_str.lower() for kw in keywords):
        return False
    return False

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    duplicates = set()
    content_hashes = set()

    for file in uploaded_files:
        file_bytes = file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()
        if file_hash in content_hashes:
            duplicates.add(file.name)
            continue
        content_hashes.add(file_hash)

        ext = file.name.split(".")[-1].lower()
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            if ext == "xlsx":
                xls = pd.ExcelFile(tmp_path)
                sheets = xls.sheet_names
            else:
                sheets = [None]

            for sheet in sheets:
                df_temp = pd.read_excel(tmp_path, sheet_name=sheet, header=None) if ext == "xlsx" else pd.read_csv(tmp_path, header=None)
                first_row = df_temp.iloc[0].astype(str)
                numeric_count = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])

                is_lon_xon_sheet = "LỘN XỘN" in str(sheet).upper()

                if numeric_count >= len(first_row) - 2:
                    df = df_temp.copy()
                    df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                    auto_mapping = {key: df.columns[i+2] for i, key in enumerate(["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"])}
                else:
                    df = df_temp[1:].copy()
                    df.columns = first_row
                    auto_mapping = auto_map_columns(df.columns.tolist())

                df = df[df.apply(is_valid_row, axis=1)].reset_index(drop=True)

                required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                final_mapping = {
                    field: auto_mapping.get(field) or st.selectbox(
                        f"Chọn cột cho '{field}'", df.columns.tolist(), key=f"{field}_{sheet}_{file.name}"
                    ) for field in required_fields
                }

                df["Tên sản phẩm"] = df[final_mapping["tên hàng"]].astype(str)
                df["Ghi chú thêm"] = (
                    df[final_mapping["tên hàng"]].astype(str) + " Size " +
                    df[final_mapping["size"]].astype(str) +
                    " - KHÁCH KHÔNG NHỌN THU 30K, GỌI VỌ SHOP KHI ĐƯỚN SAI THÔNG TIN"
                )

                df_out = pd.DataFrame({
                    "Tên người nhận": df[final_mapping["họ tên"]],
                    "Số điện thoại": df[final_mapping["số điện thoại"]],
                    "Địa chỉ": df[final_mapping["địa chỉ"]],
                    "Gói cước": 2,
                    "Tiền thu hộ": df[final_mapping["số tiền thu hộ"]],
                    "Yêu cầu đơn hàng": 3,
                    "Khối lượng": 500,
                    "Dài": 10, "Rộng": 10, "Cao": 10,
                    "Khai giá": "x",
                    "Giá trị hàng": df[final_mapping["số tiền thu hộ"]],
                    "Shop trả ship": "x", "Bưu cục": "", "Mã đơn riêng": "",
                    "Sản phẩm": df["Tên sản phẩm"],
                    "Ghi chú thêm": df["Ghi chú thêm"],
                    "Ca lấy": 1, "Giao thất bại thu": 30000
                })

                # Xử lý sheet Lộn Xộn chỉ cho Mẫu 3
                if template_option == "Mẫu 3 - Chị Thúy" and is_lon_xon_sheet:
                    now = datetime.now()
                    day = now.day
                    month = now.month
                    product_counter = defaultdict(int)

                    for idx in range(len(df_out)):
                        ten_sp = df_out.iloc[idx]["Sản phẩm"]
                        size_match = re.search(r"(\d+kg)", str(df_out.iloc[idx]["Ghi chú thêm"]))
                        size_text = size_match.group(1) if size_match else ""

                        product_counter["LỘN XỘN"] += 1
                        stt = product_counter["LỘN XỘN"]

                        ma_don = f"LỘN XỘN D.{day}.{month}.{stt}"
                        ghi_chu = f"{ma_don} [{ten_sp} {size_text}] - KHÁCH KHÔNG NHỌN THU 30K, GỌI VỌ SHOP KHI ĐƯỚN SAI THÔNG TIN"

                        df_out.at[idx, "Mã đơn riêng"] = ma_don
                        df_out.at[idx, "Ghi chú thêm"] = ghi_chu

                all_data.append(df_out)

        except Exception as e:
            st.error(f"❌ Lỗi đọc file {file.name}: {e}")
