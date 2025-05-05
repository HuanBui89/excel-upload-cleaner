import streamlit as st
import pandas as pd
import io

st.title("📦 GHN Smart Excel Upload - Auto Mapping + Debug")

def auto_map_columns(columns):
    mapping = {}
    keywords = {
        "họ tên": ["tên", "họ", "full name", "hoten"],
        "số điện thoại": ["điện", "sdt", "phone", "mobile", "dt", "số dt"],
        "địa chỉ": ["địa", "đường", "address", "dc"],
        "tên hàng": ["hàng", "tên hàng", "sản phẩm", "product"],
        "size": ["size", "kích thước", "sz"],
        "số tiền thu hộ": ["thu hộ", "cod", "tiền", "giá trị"]
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
            df = pd.read_excel(file, header=0) if ext == "xlsx" else pd.read_csv(file, header=0)
            df.columns = df.columns.str.strip().str.lower()
        except:
            df = pd.read_excel(file, header=None) if ext == "xlsx" else pd.read_csv(file, header=None)
            if df.shape[1] >= 6:
                df.columns = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"] + [f"cột_{i}" for i in range(len(df.columns)-6)]
            else:
                st.error("❌ File không có tiêu đề và không đủ 6 cột cần thiết để gán tên tự động.")
                st.stop()

        st.write("📄 Các cột có trong file:", df.columns.tolist())

        columns = df.columns.tolist()
        mapping = auto_map_columns(columns)
        st.write("🔎 Mapping tự động:", mapping)

        required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size"]
        missing = [f for f in required_fields if f not in mapping]

        if missing:
            st.error(f"❌ Thiếu các cột: {', '.join(missing)}")
            st.stop()

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
            "Giá trị hàng hóa": df.get(mapping.get("số tiền thu hộ"), 0),
            "Khai giá (Có/Không)": "x",
            "Tiền thu hộ (COD)": df.get(mapping.get("số tiền thu hộ"), 0),
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
