import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from tempfile import NamedTemporaryFile
from datetime import datetime
import io

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 GHN Excel Upload - Auto Mapping + Chuẩn File Mẫu GHN")

template_option = st.radio("🎯 Chọn mẫu xuất file", ["Mẫu 1 (Chị Tiền)", "Mẫu 2 (Chị Linh)"], index=1)
uploaded_files = st.file_uploader("📤 Tải lên file Excel (.xlsx)", type=["xlsx"], accept_multiple_files=True)

def auto_map_columns(columns):
    keywords = {
        "họ tên": ["họ", "tên", "khách"],
        "số điện thoại": ["sdt", "số điện thoại", "mobile"],
        "địa chỉ": ["địa chỉ", "phường", "quận", "đường"],
        "tên hàng": ["tên hàng", "sản phẩm"],
        "size": ["size", "kích thước", "ghi chú"],
        "số tiền thu hộ": ["tiền", "thu hộ", "cod"]
    }
    mapping = {}
    for key, keys in keywords.items():
        for col in columns:
            if any(k in str(col).lower() for k in keys):
                mapping[key] = col
                break
    return mapping

if uploaded_files:
    all_data = []
    seen_files = set()
    duplicate_files = set()

    for file in uploaded_files:
        if file.name in seen_files:
            duplicate_files.add(file.name)
            continue
        seen_files.add(file.name)

        try:
            xls = pd.ExcelFile(file)
            for sheet in xls.sheet_names:
                df_raw = pd.read_excel(xls, sheet_name=sheet, header=None)
                header = df_raw.iloc[0].astype(str)
                df = df_raw[1:].copy()
                df.columns = header

                mapping = auto_map_columns(df.columns)
                required = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                if not all(k in mapping for k in required):
                    st.error(f"❌ Thiếu cột trong file {file.name}, sheet {sheet}")
                    continue

                df["Tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)
                df["Ghi chú thêm"] = ""
                if template_option == "Mẫu 2 (Chị Linh)":
                    df["Ghi chú thêm"] = df["Tên sản phẩm"] + " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"

                new_df = pd.DataFrame({
                    "Tên người nhận": df[mapping["họ tên"]],
                    "Số điện thoại": df[mapping["số điện thoại"]],
                    "Số nhà/ngõ/ngách/hẻm, Đường/Phố, Phường/Xã, Quận/Huyện, Tỉnh/Thành": df[mapping["địa chỉ"]],
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
                    "Sản phẩm": df["Tên sản phẩm"],
                    "Ghi chú thêm": df["Ghi chú thêm"],
                    "Ca lấy": 1,
                    "Giao hàng thất bại thu tiền": 30000
                })

                all_data.append(new_df)
        except Exception as e:
            st.error(f"❌ Lỗi xử lý file {file.name}: {e}")

    if duplicate_files:
        st.warning(f"⚠️ Có file trùng tên bị bỏ qua: {', '.join(duplicate_files)}")

    if all_data:
        final = pd.concat(all_data, ignore_index=True)

        if template_option == "Mẫu 2 (Chị Linh)":
            final["Tên người nhận"] = [f"{i+1}_{name}" for i, name in enumerate(final["Tên người nhận"])]

        st.success("✅ Đã xử lý thành công! Xem trước dữ liệu:")
        st.dataframe(final)

        # Load file mẫu
        try:
            template_path = "GHN_FileMauChuyenPhat_HangNhe_2023 (11).xlsx"
            wb = load_workbook(template_path)
            ws = wb.active

            for row in final.itertuples(index=False, name=None):
                ws.append(row)

            with NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
                wb.save(f.name)
                f.seek(0)
                st.download_button("📥 Tải file GHN", data=f.read(), file_name="GHN_output.xlsx")
        except Exception as e:
            st.error(f"❌ Lỗi xuất file: {e}")

        # Tách nếu mẫu 2 > 300
        if template_option == "Mẫu 2 (Chị Linh)" and len(final) > 300:
            st.subheader("📂 Tách file GHN thành từng 300 đơn")
            try:
                for i in range(0, len(final), 300):
                    chunk = final.iloc[i:i+300]
                    wb = load_workbook(template_path)
                    ws = wb.active
                    for row in chunk.itertuples(index=False, name=None):
                        ws.append(row)

                    today = datetime.today().strftime("%-d.%-m")
                    start = i + 1
                    end = i + len(chunk)
                    filename = f"GHN_{today}_SHOP TUONG VY_TOI {start}-{end}.xlsx"

                    with NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
                        wb.save(f.name)
                        f.seek(0)
                        st.download_button(f"📎 Tải file {filename}", data=f.read(), file_name=filename)
            except Exception as e:
                st.error(f"❌ Lỗi khi tách file: {e}")
