import streamlit as st
import pandas as pd
import io
from datetime import datetime
from openpyxl import load_workbook

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 GHN Excel Upload - Chuẩn GHN Template")

template_option = st.radio("Chọn mẫu xuất kết quả:", options=["Mẫu 1 - Chị Tiền", "Mẫu 2 - Chị Linh"], index=1)

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)
template_file = "GHN_FileMauChuyenPhat_HangNhe_2023 (11).xlsx"

def auto_map_columns(columns):
    mapping = {}
    keywords = {
        "họ tên": ["khách", "họ", "tên"],
        "số điện thoại": ["sdt", "điện thoại"],
        "địa chỉ": ["địa", "phường", "quận"],
        "tên hàng": ["sản phẩm", "tên hàng", "áo"],
        "size": ["size", "mô tả"],
        "số tiền thu hộ": ["cod", "thu hộ", "giá"]
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
    duplicated_files = set()

    for file in uploaded_files:
        if file.name in filenames:
            duplicated_files.add(file.name)
            continue
        filenames.add(file.name)

        try:
            df_temp = pd.read_excel(file, header=None)
            first_row = df_temp.iloc[0].astype(str)
            df = df_temp[1:].copy()
            df.columns = first_row

            mapping = auto_map_columns(df.columns.tolist())

            if template_option == "Mẫu 2 - Chị Linh":
                df["Họ tên người nhận"] = df[mapping["họ tên"]].astype(str)
                df["Ghi chú thêm"] = df[mapping["tên hàng"]].astype(str) + " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
            else:
                df["Họ tên người nhận"] = df[mapping["họ tên"]]
                df["Ghi chú thêm"] = ""

            df_final = pd.DataFrame({
                "Tên người nhận": df["Họ tên người nhận"],
                "Số điện thoại": df[mapping["số điện thoại"]],
                "Số nhà/ngõ/hẻm, Đường/Phố, Phường/Xã, Quận/Huyện, Tỉnh/Thành": df[mapping["địa chỉ"]],
                "Gói cước": 2,
                "Tiền thu hộ": df[mapping["số tiền thu hộ"]],
                "Yêu cầu đơn hàng": 2,
                "Khối lượng (gram)": 500,
                "Chiều dài (cm)": 10,
                "Chiều rộng (cm)": 10,
                "Chiều cao (cm)": 10,
                "Khai giá": "x",
                "Giá trị hàng hóa": df[mapping["số tiền thu hộ"]],
                "Shop trả ship": "x",
                "Gửi hàng tại bưu cục": "",
                "Mã đơn hàng riêng": "",
                "Sản phẩm": df[mapping["tên hàng"]],
                "Ghi chú thêm": df["Ghi chú thêm"],
                "Ca lấy": 1,
                "Giao hàng thất bại thu tiền": 30000
            })

            all_data.append(df_final)

        except Exception as e:
            st.error(f"❌ Lỗi đọc file {file.name}: {e}")

    if duplicated_files:
        st.warning(f"⚠️ Có file trùng tên bị bỏ qua: {', '.join(duplicated_files)}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        st.success("✅ Đã xử lý thành công! Xem trước dữ liệu:")
        st.dataframe(final_df)

        output = io.BytesIO()
        template_wb = load_workbook(template_file)
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            writer.book = template_wb
            writer.sheets = {ws.title: ws for ws in template_wb.worksheets}
            final_df.to_excel(writer, sheet_name=template_wb.active.title, index=False, header=False, startrow=4)
        output.seek(0)

        st.download_button("📥 Tải file GHN", data=output, file_name="GHN_output.xlsx")

        if template_option == "Mẫu 2 - Chị Linh" and len(final_df) > 300:
            st.subheader("📂 Tách file GHN thành từng 300 đơn")
            today = datetime.today().strftime("%-d.%-m")
            for i in range(0, len(final_df), 300):
                chunk = final_df.iloc[i:i+300]
                chunk_output = io.BytesIO()
                wb = load_workbook(template_file)
                with pd.ExcelWriter(chunk_output, engine="openpyxl") as writer:
                    writer.book = wb
                    writer.sheets = {ws.title: ws for ws in wb.worksheets}
                    chunk.to_excel(writer, sheet_name=wb.active.title, index=False, header=False, startrow=4)
                chunk_output.seek(0)
                file_name = f"GHN_{today}_SHOP TUONG VY_TOI {i+1}-{i+len(chunk)}.xlsx"
                st.download_button(f"📥 Tải {file_name}", data=chunk_output, file_name=file_name)
