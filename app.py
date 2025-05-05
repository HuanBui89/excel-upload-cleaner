import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 GHN Excel Upload - Auto + Manual Mapping + Multi-Sheet")

def auto_map_columns(columns):
    mapping = {}
    keywords = {
        "họ tên": ["khách", "tên", "họ", "người nhận"],
        "số điện thoại": ["sdt", "sđt", "điện thoại"],
        "địa chỉ": ["địa", "địa chỉ", "address"],
        "tên hàng": ["sản phẩm", "tên hàng", "sp", "mã hàng"],
        "size": ["ghi chú", "mô tả", "size", "chi tiết"],
        "số tiền thu hộ": ["cod", "thu hộ", "tiền cod", "tiền thu"]
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

uploaded_files = st.file_uploader("Tải lên file Excel (.xlsx)", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        try:
            xls = pd.ExcelFile(uploaded_file)
            for sheet_name in xls.sheet_names:
                st.header(f"🔍 Sheet: {sheet_name}")
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, dtype=str)
                
                # Kiểm tra nếu dòng đầu tiên không phải là tiêu đề
                first_row = df_raw.iloc[0].astype(str)
                numeric_like = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])
                
                if numeric_like >= len(first_row) - 2:
                    df = df_raw.copy()
                    df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                else:
                    df = df_raw[1:].copy()
                    df.columns = first_row

                columns = df.columns.tolist()
                mapping = auto_map_columns(columns)

                required = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                for field in required:
                    if field not in mapping:
                        mapping[field] = st.selectbox(
                            f"Chọn cột cho '{field}'",
                            columns,
                            key=f"{uploaded_file.name}_{sheet_name}_{field}"
                        )

                # Gộp tên sản phẩm + size
                df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)

                # Xử lý số tiền thu hộ
                df[mapping["số tiền thu hộ"]] = pd.to_numeric(df[mapping["số tiền thu hộ"]].str.replace(",", "").str.extract("(\d+)")[0], errors='coerce').fillna(0).astype(int)

                ghn_df = pd.DataFrame({
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

                all_data.append(ghn_df)

        except Exception as e:
            st.error(f"❌ Lỗi khi xử lý file {uploaded_file.name}: {e}")

    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        st.success("✅ Tất cả sheet đã được xử lý thành công!")
        st.dataframe(result)

        towrite = io.BytesIO()
        result.to_excel(towrite, index=False, engine="openpyxl")
        st.download_button("📥 Tải xuống file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
