import streamlit as st
import pandas as pd
import io

st.title("📦 GHN Excel Upload - Auto + Manual Column Mapping (Multi-Sheet)")

def auto_map_columns(columns):
    mapping = {}
    keywords = {
        "họ tên": ["khách", "họ", "tên", "khách hàng"],
        "số điện thoại": ["sdt", "sđt", "điện", "mobile", "phone"],
        "địa chỉ": ["địa chỉ", "địa", "dc", "address"],
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

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()

        try:
            if ext == "xlsx":
                xls = pd.ExcelFile(file)
                sheet_names = xls.sheet_names
            else:
                sheet_names = [None]  # CSV

            for sheet_name in sheet_names:
                df_raw = pd.read_excel(file, sheet_name=sheet_name, header=None) if ext == "xlsx" else pd.read_csv(file, header=None)
                first_row = df_raw.iloc[0].astype(str)
                numeric_count = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])

                if numeric_count >= len(first_row) - 2:
                    # Không có tiêu đề
                    df = df_raw.copy()
                    df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                    df.columns.values[2:10] = ["Họ tên", "Số điện thoại", "Địa chỉ", "Tên hàng", "Size", "Tiền COD", "Ngày tạo", "Nguồn đơn"]
                    df = df.rename(columns={
                        "Họ tên": "họ tên",
                        "Số điện thoại": "số điện thoại",
                        "Địa chỉ": "địa chỉ",
                        "Tên hàng": "tên hàng",
                        "Size": "size",
                        "Tiền COD": "số tiền thu hộ"
                    })
                    mapping = {
                        "họ tên": "họ tên",
                        "số điện thoại": "số điện thoại",
                        "địa chỉ": "địa chỉ",
                        "tên hàng": "tên hàng",
                        "size": "size",
                        "số tiền thu hộ": "số tiền thu hộ"
                    }
                else:
                    df = df_raw[1:].copy()
                    df.columns = first_row
                    columns = df.columns.tolist()
                    mapping = auto_map_columns(columns)

                st.subheader(f"🔎 Sheet: {sheet_name if sheet_name else 'CSV'}")
                st.write("📋 Các cột:", df.columns.tolist())

                # Cho phép chỉnh sửa nếu thiếu
                required = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                for field in required:
                    if field not in mapping:
                        mapping[field] = st.selectbox(f"🛠 Chọn cột cho '{field}'", options=df.columns, key=field+str(sheet_name)+file.name)

                # Gộp tên hàng và size
                df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)

                # Tạo file chuẩn GHN
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
            st.error(f"❌ Lỗi xử lý file {file.name}: {e}")

    if all_data:
        final = pd.concat(all_data, ignore_index=True)
        st.success("✅ Hoàn tất xử lý toàn bộ file!")
        st.dataframe(final)

        towrite = io.BytesIO()
        final.to_excel(towrite, index=False, engine='openpyxl')
        st.download_button("📥 Tải file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx")
