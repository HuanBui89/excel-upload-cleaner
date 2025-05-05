import streamlit as st
import pandas as pd
import io

st.title("📦 Tạo File GHN từ Excel")

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()
        df = pd.read_excel(file) if ext == "xlsx" else pd.read_csv(file)
        df.columns = df.columns.str.strip().str.lower()

        st.write("📄 Các cột có trong file:", df.columns.tolist())

        # Kiểm tra cột bắt buộc
        required_cols = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.error(f"❌ Thiếu các cột bắt buộc: {', '.join(missing_cols)}")
            st.stop()

        df["tên sản phẩm"] = df["tên hàng"].astype(str) + " Size " + df["size"].astype(str)

        new_df = pd.DataFrame({
            "Họ tên người nhận": df.get("họ tên"),
            "Số điện thoại người nhận": df.get("số điện thoại"),
            "Địa chỉ": df.get("địa chỉ"),
            "Gói cước": 2,
            "Yêu cầu đơn hàng": 2,
            "Tên sản phẩm": df["tên sản phẩm"],
            "Số lượng": 1,
            "Khối lượng (gram)": 500,
            "Chiều dài (cm)": 10,
            "Chiều rộng (cm)": 10,
            "Chiều cao (cm)": 10,
            "Giá trị hàng hóa": df.get("số tiền thu hộ", 0),
            "Khai giá (Có/Không)": "x",
            "Tiền thu hộ (COD)": df.get("số tiền thu hộ", 0),
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
