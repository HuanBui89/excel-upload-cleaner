import streamlit as st
import pandas as pd
import io
import hashlib
from datetime import datetime
import os

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 GHN Excel Upload - Auto + Manual Column Mapping (Multi-Sheet)")

# CSS tùy chỉnh chữ to và tô màu nút chọn
st.markdown("""
<style>
div[data-baseweb="radio"] > div {
    flex-direction: row;
    gap: 20px;
}
div[data-baseweb="radio"] label {
    font-size: 20px !important;
    font-weight: bold;
    padding: 15px 25px;
    border-radius: 10px;
    border: 2px solid #ccc;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    cursor: pointer;
    transition: 0.3s;
}
div[data-baseweb="radio"] label:nth-child(1) {
    background-color: #28a745 !important;
    color: white;
}
div[data-baseweb="radio"] label:nth-child(2) {
    background-color: #dc3545 !important;
    color: white;
}
div[data-baseweb="radio"] label:hover {
    transform: scale(1.05);
    opacity: 0.9;
}
div[data-baseweb="radio"] label div:first-child {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


template_option = st.radio("Chọn mẫu xuất kết quả:", ["Mẫu 1 - Chị Tiền", "Mẫu 2 - Chị Linh"], index=1)

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
            if any(kw in str(col).lower() for kw in kws):
                mapping[key] = col
                break
    return mapping

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

if uploaded_files:
    all_data, filenames, duplicates = [], set(), set()
    content_hashes = {}

    for file in uploaded_files:
        file_content = file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        file.seek(0)

        if file_hash in content_hashes:
            duplicates.add(file.name)
            continue
        content_hashes[file_hash] = file.name

        ext = file.name.split(".")[-1].lower()
        sheets = pd.ExcelFile(file).sheet_names if ext == "xlsx" else [None]

        for sheet in sheets:
            df = pd.read_excel(file, sheet_name=sheet, header=None) if sheet else pd.read_csv(file, header=None)

            numeric_count = sum(cell.replace('.', '', 1).isdigit() for cell in df.iloc[0].astype(str))
            if numeric_count >= len(df.columns) - 2:
                df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                mapping = {
                    "họ tên": df.columns[2],
                    "số điện thoại": df.columns[3],
                    "địa chỉ": df.columns[4],
                    "tên hàng": df.columns[5],
                    "size": df.columns[6],
                    "số tiền thu hộ": df.columns[7]
                }
            else:
                df.columns = df.iloc[0]
                df = df[1:]
                mapping = auto_map_columns(df.columns)

            df["Tên sản phẩm"] = df[mapping["tên hàng"]]

            ghi_chu = df[mapping["tên hàng"]] + " Size " + df[mapping["size"]] + \
                      " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN" \
                      if template_option == "Mẫu 2 - Chị Linh" else ""

            data_final = pd.DataFrame({
                "Tên người nhận": df[mapping["họ tên"]],
                "Số điện thoại": df[mapping["số điện thoại"]],
                "Địa chỉ": df[mapping["địa chỉ"]],
                "Gói cước": 2,
                "Tiền thu hộ": df[mapping["số tiền thu hộ"]],
                "Yêu cầu đơn hàng": 3,
                "Khối lượng": 500,
                "Dài": 10, "Rộng": 10, "Cao": 10,
                "Khai giá": "x",
                "Giá trị hàng": df[mapping["số tiền thu hộ"]],
                "Shop trả ship": "x",
                "Bưu cục": "", "Mã đơn riêng": "",
                "Sản phẩm": df["Tên sản phẩm"],
                "Ghi chú thêm": ghi_chu,
                "Ca lấy": 1, "Thất bại thu": 30000
            })

            all_data.append(data_final)

    if duplicates:
        st.error(f"🚨 File trùng nội dung: {', '.join(duplicates)}")

    if all_data:
        final = pd.concat(all_data, ignore_index=True)

        if template_option == "Mẫu 2 - Chị Linh":
            final["Tên người nhận"] = [f"{i+1}_{name}" for i, name in enumerate(final["Tên người nhận"])]

        st.success("✅ Xử lý thành công!")
        st.dataframe(final)

        buffer = io.BytesIO()
        final.to_excel(buffer, index=False)
        st.download_button("📥 Tải file GHN", buffer, f"GHN_{datetime.now():%d-%m-%Y_%H-%M}.xlsx")

        if len(final) > 300 and template_option == "Mẫu 2 - Chị Linh":
            st.subheader("📂 Tách file mỗi 300 đơn")
            today = datetime.now().strftime("%d.%m")

            for i in range(0, len(final), 300):
                chunk = final.iloc[i:i+300]
                fname = f"GHN_{today}_SHOP TUONG VY_{i+1}-{i+len(chunk)}.xlsx"
                buf_chunk = io.BytesIO()
                chunk.to_excel(buf_chunk, index=False)
                st.download_button(f"📥 Tải {fname}", buf_chunk, fname)

# Lịch sử 3 ngày
with st.expander("🕒 Lịch sử 3 ngày gần đây"):
    os.makedirs("history", exist_ok=True)
    history = sorted([f for f in os.listdir("history") if (datetime.now() - datetime.fromtimestamp(os.path.getmtime(f"history/{f}"))).days <= 3])

    if history:
        for f in history:
            with open(f"history/{f}", "rb") as file_data:
                st.download_button(f"📥 {f}", file_data, file_name=f)
    else:
        st.info("Không có file nào gần đây.")
