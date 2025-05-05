import streamlit as st
import pandas as pd
import io

st.title("📦 GHN Excel Upload - Auto + Manual Column Mapping (Multi-Sheet)")

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

uploaded_files = st.file_uploader("📤 Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []

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
                    mapping = {
                        "họ tên": df.columns[1],
                        "số điện thoại": df.columns[3],
                        "địa chỉ": df.columns[4],
                        "tên hàng": df.columns[5],
                        "size": df.columns[6],
                        "số tiền thu hộ": df.columns[7],
                    }
                else:
                    df = df_temp[1:].copy()
                    df.columns = first_row
                    df = df.reset_index(drop=True)
                    columns = df.columns.tolist()
                    mapping = auto_map_columns(columns)

                st.subheader(f"🔎 Sheet: {sheet_name if sheet_name else 'CSV'}")
                st.write("📋 Các cột:", df.columns.tolist())
                st.write("🔁 Mapping tự động:", mapping)

                required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size"]
                for field in required_fields:
                    if field not in mapping:
                        mapping[field] = st.selectbox(f"🛠 Chọn cột cho '{field}'", df.columns, key=field+str(sheet_name)+file.name)

                if "số tiền thu hộ" not in mapping:
                    mapping["số tiền thu hộ"] = st.selectbox("💵 Chọn cột cho 'số tiền thu hộ (COD)'", df.columns, key="cod"+str(sheet_name)+file.name)

                df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)

                try:
                    new_df = pd.DataFrame({
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

                    all_data.append(new_df)

                except Exception as e:
                    st.error(f"❌ Đã xảy ra lỗi khi xử lý file: '{mapping['số tiền thu hộ']}'\nChi tiết: {e}")

        except Exception as e:
            st.error(f"❌ Lỗi đọc file {file.name}: {e}")

    if all_data:
        final = pd.concat(all_data, ignore_index=True)
        st.success("✅ Đã xử lý thành công tất cả file và sheet!")
        st.dataframe(final)

        towrite = io.BytesIO()
        final.to_excel(towrite, index=False, engine="openpyxl")
        st.download_button("📥 Tải file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx")
