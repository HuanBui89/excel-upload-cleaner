import streamlit as st
import pandas as pd
import io
import hashlib
import os
from datetime import datetime

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 GHN Excel Upload - Auto + Manual Column Mapping (Multi-Sheet)")

log_file = "history_logs.csv"
if not os.path.exists(log_file):
    pd.DataFrame(columns=["Time", "Filename", "Total Orders"]).to_csv(log_file, index=False)

template_option = st.radio(
    "Chọn mẫu xuất kết quả:",
    options=["Mẫu 1 - Chị Tiền", "Mẫu 2 - Chị Linh"],
    index=1,
    help="Mẫu 1 giữ nguyên dữ liệu | Mẫu 2 sẽ thêm tên + đánh số + ghi chú đặc biệt"
)

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

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
    filenames = set()
    duplicates = set()
    content_hashes = set()

    for file in uploaded_files:
        file_content = file.getvalue()
        file_hash = hashlib.md5(file_content).hexdigest()

        if file_hash in content_hashes:
            duplicates.add(file.name)
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
                df["Ghi chú thêm"] = df[final_mapping["tên hàng"]].astype(str) + " Size " + df[final_mapping["size"]].astype(str) + \
                    " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN" if template_option == "Mẫu 2 - Chị Linh" else ""

                all_data.append(pd.DataFrame({
                    "Tên người nhận": df[final_mapping["họ tên"]],
                    "Số điện thoại": df[final_mapping["số điện thoại"]],
                    "Địa chỉ": df[final_mapping["địa chỉ"]],
                    "Gói cước": 2,
                    "Tiền thu hộ": df[final_mapping["số tiền thu hộ"]],
                    "Yêu cầu đơn hàng": 2,
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
            st.error(f"❌ Lỗi đọc file {file.name}: {e}")

    if duplicates:
        st.error(f"⚠️ File trùng nội dung bị bỏ qua: {', '.join(duplicates)}")

    if all_data:
        final = pd.concat(all_data, ignore_index=True)
        total_orders = len(final)

        if template_option == "Mẫu 2 - Chị Linh":
            final["Tên người nhận"] = final.index + 1
            final["Tên người nhận"] = final["Tên người nhận"].astype(str) + "_" + final["Tên người nhận"]

        st.success(f"✅ Xử lý thành công! Tổng số đơn: {total_orders}")
        st.dataframe(final)

        towrite = io.BytesIO()
        final.to_excel(towrite, index=False)
        st.download_button("📥 Tải file GHN", data=towrite, file_name="GHN_output.xlsx")

        # Lưu vào log lịch sử
        log_df = pd.read_csv(log_file)
        new_log = pd.DataFrame([[datetime.now(), ', '.join([f.name for f in uploaded_files]), total_orders]],
                               columns=["Time", "Filename", "Total Orders"])
        log_df = pd.concat([log_df, new_log])
        log_df.to_csv(log_file, index=False)

    # Xem lịch sử
    with st.expander("📜 Lịch sử 3 ngày gần đây"):
        log_df = pd.read_csv(log_file)
        log_df["Time"] = pd.to_datetime(log_df["Time"])
        recent_log = log_df[log_df["Time"] >= pd.Timestamp.now() - pd.Timedelta(days=3)]
        st.dataframe(recent_log)

# CSS lớn hơn và nổi bật
st.markdown("""
<style>
div[data-baseweb="radio"] label {padding:10px 20px; font-size:18px!important; font-weight:bold; border-radius:5px; border:2px solid #ccc; box-shadow:0 4px 8px rgba(0,0,0,0.2); margin-right:10px;}
div[data-baseweb="radio"] label:nth-child(1){background:#28a745!important;color:#fff;}
div[data-baseweb="radio"] label:nth-child(2){background:#dc3545!important;color:#fff;}
div[data-baseweb="radio"] label div:first-child{display:none!important;}
</style>
""", unsafe_allow_html=True)
