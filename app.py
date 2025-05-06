
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import zipfile
import os

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 GHN Excel Upload - GHN Formatted Export (Multi-Sheet + Smart Split)")

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

def check_duplicate_files(file_list):
    file_contents = [file.getvalue() for file in file_list]
    seen = set()
    duplicates = []
    for idx, content in enumerate(file_contents):
        if content in seen:
            duplicates.append(file_list[idx].name)
        seen.add(content)
    return duplicates

def load_template():
    return pd.read_excel("GHN_FileMauChuyenPhat_HangNhe_2023 (11).xlsx", skiprows=4)

def export_with_template(df, filename):
    template = pd.read_excel("GHN_FileMauChuyenPhat_HangNhe_2023 (11).xlsx", header=None)
    writer_buffer = io.BytesIO()
    with pd.ExcelWriter(writer_buffer, engine='openpyxl') as writer:
        template.iloc[:4].to_excel(writer, index=False, header=False)
        df.to_excel(writer, startrow=4, index=False, header=False)
    writer_buffer.seek(0)
    return writer_buffer

def split_dataframe(df, rows=300):
    return [df.iloc[i:i + rows] for i in range(0, df.shape[0], rows)]

# -- Main Upload Section --
uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)
export_option = st.radio("🎯 Chọn mẫu xuất file", ["Mẫu 1 (Chị Tiền)", "Mẫu 2 (Chị Linh)"], index=1)

if uploaded_files:
    duplicated_files = check_duplicate_files(uploaded_files)
    if duplicated_files:
        st.warning(f"⚠️ Các file bị trùng nội dung hoàn toàn: {', '.join(duplicated_files)}")

    all_data = []
    global_index = 1

    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()

        try:
            if ext == "xlsx":
                xls = pd.ExcelFile(file)
                sheet_names = xls.sheet_names
            else:
                sheet_names = [None]

            for sheet_name in sheet_names:
                df_temp = pd.read_excel(file, sheet_name=sheet_name, header=None) if ext == "xlsx" else pd.read_csv(file, header=None)
                first_row = df_temp.iloc[0].astype(str)
                numeric_count = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])

                if numeric_count >= len(first_row) - 2:
                    df = df_temp.copy()
                    df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                    auto_mapping = {
                        "họ tên": df.columns[2],
                        "số điện thoại": df.columns[3],
                        "địa chỉ": df.columns[4],
                        "tên hàng": df.columns[5],
                        "size": df.columns[6],
                        "số tiền thu hộ": df.columns[7]
                    }
                else:
                    df = df_temp[1:].copy()
                    df.columns = first_row
                    auto_mapping = auto_map_columns(df.columns.tolist())

                required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                mapping = {}

                for field in required_fields:
                    mapping[field] = auto_mapping.get(field) or st.selectbox(
                        f"Chọn cột cho '{field}'", options=df.columns.tolist(), key=field + sheet_name + file.name)

                if export_option == "Mẫu 2 (Chị Linh)":
                    df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)
                    df["Họ tên người nhận"] = [f"{i}_{name}" for i, name in enumerate(df[mapping["họ tên"]], start=global_index)]
                    df["Số điện thoại người nhận"] = df[mapping["số điện thoại"]]
                    df["Địa chỉ"] = df[mapping["địa chỉ"]]
                    df["Tiền thu hộ"] = df[mapping["số tiền thu hộ"]]
                    df["Ghi chú thêm"] = df["tên sản phẩm"] + " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
                    global_index += len(df)
                else:
                    df["Họ tên người nhận"] = df[mapping["họ tên"]]
                    df["Số điện thoại người nhận"] = df[mapping["số điện thoại"]]
                    df["Địa chỉ"] = df[mapping["địa chỉ"]]
                    df["Tên sản phẩm"] = df[mapping["tên hàng"]] + " Size " + df[mapping["size"]].astype(str)
                    df["Tiền thu hộ"] = df[mapping["số tiền thu hộ"]]
                    df["Ghi chú thêm"] = ""

                df["Gói cước"] = 2
                df["Yêu cầu đơn hàng"] = 2
                df["Khối lượng (gram)"] = 500
                df["Chiều dài (cm)"] = 10
                df["Chiều rộng (cm)"] = 10
                df["Chiều cao (cm)"] = 10
                df["Khai giá (Có/Không)"] = "x"
                df["Giá trị hàng hóa"] = df["Tiền thu hộ"]
                df["Shop trả phí vận chuyển"] = "x"
                df["Gửi hàng tại bưu cục"] = ""
                df["Mã hàng riêng của shop"] = ""
                df["Ca lấy hàng"] = 1
                df["Giao thất bại thu tiền"] = 30000

                export_df = df[[
                    "Họ tên người nhận", "Số điện thoại người nhận", "Địa chỉ", "Gói cước", "Tiền thu hộ", "Yêu cầu đơn hàng",
                    "Khối lượng (gram)", "Chiều dài (cm)", "Chiều rộng (cm)", "Chiều cao (cm)", "Khai giá (Có/Không)",
                    "Giá trị hàng hóa", "Shop trả phí vận chuyển", "Gửi hàng tại bưu cục", "Mã hàng riêng của shop",
                    "Tên sản phẩm", "Ghi chú thêm", "Ca lấy hàng", "Giao thất bại thu tiền"
                ]]
                all_data.append(export_df)

        except Exception as e:
            st.error(f"❌ Lỗi xử lý file {file.name}: {e}")

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        st.success("✅ Đã xử lý thành công tất cả file và sheet!")

        if export_option == "Mẫu 2 (Chị Linh)" and full_df.shape[0] > 300:
            chunks = split_dataframe(full_df, rows=300)
            zip_buffer = io.BytesIO()
            now = datetime.now()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for idx, chunk in enumerate(chunks):
                    file_name = f"GHN_{now.day}.{now.month}_SHOP TUONG VY_TOI {idx*300+1}-{(idx+1)*300 if (idx+1)*300 < len(full_df) else len(full_df)}.xlsx"
                    output = export_with_template(chunk, file_name)
                    zip_file.writestr(file_name, output.read())
            zip_buffer.seek(0)
            st.download_button("📁 Tải file GHN thành từng 300 đơn (.zip)", data=zip_buffer, file_name="GHN_Files_Split.zip")
        else:
            fileout = export_with_template(full_df, "GHN_full_output.xlsx")
            st.download_button("📥 Tải file GHN", data=fileout.getvalue(), file_name="GHN_output.xlsx")
