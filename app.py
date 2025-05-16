import streamlit as st
import pandas as pd
import io
import hashlib
import os
from datetime import datetime
from unicodedata import normalize
import re

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 APP TẠO ĐƠN ĐƠN THEO MẪU GHN")

log_file = "history_logs.csv"
if not os.path.exists(log_file):
    pd.DataFrame(columns=["Time", "Filename", "Total Orders"]).to_csv(log_file, index=False)

# Thiết lập mặc định nếu chưa có
if "template_option" not in st.session_state:
    st.session_state.template_option = "Mẫu 2 - Chị Linh"

# Danh sách mẫu và nhãn có icon
template_labels = {
    "Mẫu 1 - Chị Tiền": "📗 Mẫu 1 - Chị Tiền",
    "Mẫu 2 - Chị Linh": "📕 Mẫu 2 - Chị Linh"
}
label_to_value = {v: k for k, v in template_labels.items()}
default_option = template_labels[st.session_state.get("template_option", "Mẫu 2 - Chị Linh")]

# CSS giao diện selectbox
st.markdown(f"""
<style>
div[data-baseweb="select"] {{
    width: fit-content !important;
    min-width: 280px;
    padding: 2px;
}}
div[data-baseweb="select"] > div {{
    background-color: {"#28a745" if "Mẫu 1" in default_option else "#dc3545"} !important;
    color: white !important;
    font-weight: bold;
    border-radius: 6px;
    border: 2px solid #000;
}}
label[for="template_label"] {{
    font-weight: bold;
    font-size: 16px;
    color: #dc3545;
    margin-bottom: 5px;
    display: block;
}}
</style>
""", unsafe_allow_html=True)

selected_label = st.selectbox(
    "📝 Chọn mẫu xuất kết quả:",
    options=list(template_labels.values()),
    index=list(template_labels.values()).index(default_option),
    key="template_label"
)

st.session_state.template_option = label_to_value[selected_label]
template_option = st.session_state.template_option

# Hàm đổi tên file an toàn sau upload

def safe_filename(name):
    name = normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)

uploaded_files_raw = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)
uploaded_files = []
uploaded_file_names = {}

if uploaded_files_raw:
    for f in uploaded_files_raw:
        original_name = f.name
        f.name = safe_filename(f.name)
        uploaded_file_names[f.name] = original_name
        uploaded_files.append(f)

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

if uploaded_files:
    all_data = []
    duplicates = set()
    content_hashes = set()

    for file in uploaded_files:
        original_name = uploaded_file_names.get(file.name, file.name)
        file_content = file.getvalue()
        file_hash = hashlib.md5(file_content).hexdigest()

        if file_hash in content_hashes:
            duplicates.add(original_name)
            continue
        else:
            content_hashes.add(file_hash)

        ext = file.name.split(".")[-1].lower()
        try:
            if ext == "xlsx":
                xls = pd.ExcelFile(file)
                sheets = xls.sheet_names
            else:
                sheets = [None]

            for sheet in sheets:
                df_temp = pd.read_excel(file, sheet_name=sheet, header=None) if ext == "xlsx" else pd.read_csv(file, header=None)
                first_row = df_temp.iloc[0].astype(str)
                numeric_count = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])

                if numeric_count >= len(first_row) - 2:
                    df = df_temp.copy()
                    df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                    auto_mapping = {key: df.columns[i+2] for i, key in enumerate(["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"])}
                else:
                    df = df_temp[1:].copy()
                    df.columns = first_row
                    auto_mapping = auto_map_columns(df.columns.tolist())

                required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                final_mapping = {field: auto_mapping.get(field) or st.selectbox(
                    f"Chọn cột cho '{field}'", df.columns.tolist(), key=f"{field}_{sheet}_{file.name}") for field in required_fields}

                df["Tên sản phẩm"] = df[final_mapping["tên hàng"]].astype(str)
                df["Ghi chú thêm"] = (
                    df[final_mapping["tên hàng"]].astype(str) + " Size " +
                    df[final_mapping["size"]].astype(str) +
                    " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
                )

                all_data.append(pd.DataFrame({
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
                }))

        except Exception as e:
            st.error(f"❌ Lỗi đọc file {original_name}: {e}")

    if duplicates:
        st.error(f"⚠️ File trùng nội dung bị bỏ qua: {', '.join(duplicates)}")

    if all_data:
        final = pd.concat(all_data, ignore_index=True)
        total_orders = len(final)

        if template_option == "Mẫu 2 - Chị Linh":
            final["Tên người nhận"] = (final.index + 1).astype(str) + "_" + final["Tên người nhận"].astype(str)

        mau_text = "Theo mẫu Chị Linh" if template_option == "Mẫu 2 - Chị Linh" else "Theo mẫu Chị Tiền"
        st.success(f"✅ Xử lý thành công! Tổng số đơn: {total_orders} – {mau_text}")

        st.dataframe(final)

        towrite = io.BytesIO()
        final.to_excel(towrite, index=False)
        st.download_button("📥 Tải file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx")

        log_df = pd.read_csv(log_file)
        new_log = pd.DataFrame([[datetime.now(), ', '.join([uploaded_file_names.get(f.name, f.name) for f in uploaded_files]), total_orders]],
                               columns=["Time", "Filename", "Total Orders"])
        log_df = pd.concat([log_df, new_log])
        log_df["Time"] = pd.to_datetime(log_df["Time"])
        log_df = log_df.sort_values(by="Time", ascending=False)
        log_df.to_csv(log_file, index=False)

        if len(final) > 300 and template_option == "Mẫu 2 - Chị Linh":
            st.subheader("📂 Tách file mỗi 300 đơn")
            today = datetime.now().strftime("%d.%m")

            for i in range(0, len(final), 300):
                chunk = final.iloc[i:i+300]
                fname = f"GHN_{today}_SHOP_TUONG_VY_{i+1}-{i+len(chunk)}.xlsx"
                buf_chunk = io.BytesIO()
                chunk.to_excel(buf_chunk, index=False)
                st.download_button(f"📥 Tải {fname}", buf_chunk.getvalue(), file_name=fname, key=f"chunk_{i}")

with st.expander("📜 Lịch sử 3 ngày gần đây"):
    log_df = pd.read_csv(log_file)
    log_df["Time"] = pd.to_datetime(log_df["Time"])
    recent_log = log_df[log_df["Time"] >= pd.Timestamp.now() - pd.Timedelta(days=3)]
    st.dataframe(recent_log)
