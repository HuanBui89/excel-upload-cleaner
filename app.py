import streamlit as st
import pandas as pd
import io

st.title("📦 GHN Excel Upload - Auto + Manual Column Mapping")

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

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()

        try:
            df_temp = pd.read_excel(file, header=None) if ext == "xlsx" else pd.read_csv(file, header=None)
            # Lấy hàng đầu tiên làm tên cột nếu phần lớn giá trị không phải số
            first_row = df_temp.iloc[0].astype(str)
            numeric_count = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])
            if numeric_count >= len(first_row) - 2:  # nếu gần như toàn bộ là số → dữ liệu, không phải tiêu đề
                df = df_temp.copy()
                df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
            else:
                df = df_temp[1:].copy()
                df.columns = first_row
        except Exception as e:
            st.error(f"❌ Lỗi đọc file: {e}")
            continue

        st.write("📄 Các cột có trong file:", df.columns.tolist())

        columns = df.columns.tolist()
        mapping = auto_map_columns(columns)

        required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size"]
        missing = [f for f in required_fields if f not in mapping]

        if missing:
            st.warning("⚠️ Không đủ cột được nhận diện. Vui lòng chọn thủ công các cột sau:")
            for field in required_fields:
                mapping[field] = st.selectbox(f"🛠 Chọn cột cho '{field}'", options=columns, key=field+file.name)

        if "số tiền thu hộ" not in mapping:
            mapping["số tiền thu hộ"] = st.selectbox("🛠 Chọn cột cho 'số tiền thu hộ' (COD)", options=columns, key="cod"+file.name)

        df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)

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

    final = pd.concat(all_data, ignore_index=True)
    st.success("✅ Đã xử lý thành công!")
    st.dataframe(final)

    towrite = io.BytesIO()
    final.to_excel(towrite, index=False, engine="openpyxl")
    st.download_button("📥 Tải file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx")
