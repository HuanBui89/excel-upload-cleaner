import streamlit as st
import pandas as pd
import io
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Đường dẫn đến template GHN
TEMPLATE_PATH = "GHN_FileMauChuyenPhat_HangNhe_2023 (11).xlsx"

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 GHN Excel Upload - Auto + Manual Column Mapping (Multi-Sheet)")

template_option = st.radio("🎯 Chọn mẫu xuất file", options=["Mẫu 1 (Chị Tiền)", "Mẫu 2 (Chị Linh)"], index=1)

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

uploaded_files = st.file_uploader("📂 Tải lên file Excel", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    filenames = set()
    duplicates = set()

    for file in uploaded_files:
        if file.name in filenames:
            duplicates.add(file.name)
            continue
        filenames.add(file.name)

        try:
            xls = pd.ExcelFile(file)
            for sheet_name in xls.sheet_names:
                df_temp = pd.read_excel(file, sheet_name=sheet_name, header=None)
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
                        "số tiền thu hộ": df.columns[7],
                    }
                else:
                    df = df_temp[1:].copy()
                    df.columns = first_row
                    auto_mapping = auto_map_columns(df.columns.tolist())

                required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                final_mapping = {}
                for field in required_fields:
                    if auto_mapping.get(field):
                        final_mapping[field] = auto_mapping[field]
                    else:
                        final_mapping[field] = st.selectbox(
                            f"Chọn cột cho '{field}'", df.columns.tolist(), key=field + file.name
                        )

                df["tên sản phẩm"] = df[final_mapping["tên hàng"]].astype(str) + " Size " + df[final_mapping["size"]].astype(str)
                df["Ghi chú thêm"] = ""

                if template_option == "Mẫu 2 (Chị Linh)":
                    df["Tên người nhận"] = df[final_mapping["họ tên"]].reset_index(drop=True)
                    df["Số thứ tự"] = range(1, len(df)+1)
                    df["Tên người nhận"] = df["Số thứ tự"].astype(str) + "_" + df["Tên người nhận"]
                    df["Ghi chú thêm"] = df["tên sản phẩm"] + " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
                else:
                    df["Tên người nhận"] = df[final_mapping["họ tên"]]

                df_final = pd.DataFrame({
                    "Tên người nhận": df["Tên người nhận"],
                    "Số điện thoại": df[final_mapping["số điện thoại"]],
                    "Số nhà/ngõ/ngách/hẻm, Đường/Phố, Phường/Xã, Quận/Huyện, Tỉnh/Thành": df[final_mapping["địa chỉ"]],
                    "Gói cước": 2,
                    "Tiền thu hộ": df[final_mapping["số tiền thu hộ"]],
                    "Yêu cầu đơn hàng": 2,
                    "Khối lượng (gram)": 500,
                    "Chiều dài (cm)": 10,
                    "Chiều rộng (cm)": 10,
                    "Chiều cao (cm)": 10,
                    "Khai giá": "x",
                    "Giá trị hàng hóa": df[final_mapping["số tiền thu hộ"]],
                    "Shop trả ship": "x",
                    "Gửi hàng tại bưu cục": "",
                    "Mã đơn hàng riêng": "",
                    "Sản phẩm": df["tên sản phẩm"],
                    "Ghi chú thêm": df["Ghi chú thêm"],
                    "Ca lấy": 1,
                    "Giao hàng thất bại thu tiền": 30000
                })

                all_data.append(df_final)

        except Exception as e:
            st.error(f"❌ Lỗi xử lý file {file.name}: {e}")

    if duplicates:
        st.warning(f"⚠️ File trùng tên đã bị bỏ qua: {', '.join(duplicates)}")

    if all_data:
        full_data = pd.concat(all_data, ignore_index=True)
        st.success("✅ Đã xử lý thành công tất cả file và sheet!")
        st.dataframe(full_data)

        # Xuất file GHN đầy đủ
        output = io.BytesIO()
        full_data.to_excel(output, index=False, engine="openpyxl")
        st.download_button("📥 Tải file GHN", data=output.getvalue(), file_name="GHN_output.xlsx")

        # Tách file nếu mẫu 2 và nhiều hơn 300 dòng
        if template_option == "Mẫu 2 (Chị Linh)" and len(full_data) > 300:
            st.subheader("📂 Tách file GHN thành từng 300 đơn")

            today = datetime.today().strftime("%-d.%-m")
            for i in range(0, len(full_data), 300):
                chunk = full_data.iloc[i:i+300].copy()
                start, end = i + 1, i + len(chunk)

                # Load template
                try:
                    wb = load_workbook(TEMPLATE_PATH)
                    ws = wb.active

                    # Ghi dữ liệu từ dòng 5
                    for r in dataframe_to_rows(chunk, index=False, header=False):
                        ws.append(r)

                    temp_bytes = io.BytesIO()
                    wb.save(temp_bytes)
                    temp_bytes.seek(0)

                    filename = f"GHN_{today}_SHOP TUONG VY_TOI {start}-{end}.xlsx"
                    st.download_button(f"📥 Tải {filename}", data=temp_bytes, file_name=filename)

                except Exception as e:
                    st.error(f"Lỗi khi tạo file tách {start}-{end}: {e}")
