import streamlit as st
import pandas as pd
import io

st.title("📦 GHN Smart Excel Upload")

def guess_column(columns, keyword):
    for col in columns:
        if keyword in col.lower():
            return col
    return columns[0] if columns else None

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
        ho_ten_col = st.selectbox("🧑 Cột chứa Họ tên", columns, index=columns.index(guess_column(columns, "tên")))
        sdt_col = st.selectbox("📞 Cột chứa SĐT", columns, index=columns.index(guess_column(columns, "điện")))
        diachi_col = st.selectbox("📍 Cột chứa Địa chỉ", columns, index=columns.index(guess_column(columns, "địa")))
        tenhang_col = st.selectbox("📦 Cột chứa Tên hàng", columns, index=columns.index(guess_column(columns, "tên hàng")))
        size_col = st.selectbox("📐 Cột chứa Size", columns, index=columns.index(guess_column(columns, "size")))
        cod_col = st.selectbox("💰 Cột chứa Tiền thu hộ", columns, index=columns.index(guess_column(columns, "thu hộ")))

        df["tên sản phẩm"] = df[tenhang_col].astype(str) + " Size " + df[size_col].astype(str)

        new_df = pd.DataFrame({
            "Họ tên người nhận": df.get(ho_ten_col),
            "Số điện thoại người nhận": df.get(sdt_col),
            "Địa chỉ": df.get(diachi_col),
            "Gói cước": 2,
            "Yêu cầu đơn hàng": 2,
            "Tên sản phẩm": df["tên sản phẩm"],
            "Số lượng": 1,
            "Khối lượng (gram)": 500,
            "Chiều dài (cm)": 10,
            "Chiều rộng (cm)": 10,
            "Chiều cao (cm)": 10,
            "Giá trị hàng hóa": df.get(cod_col, 0),
            "Khai giá (Có/Không)": "x",
            "Tiền thu hộ (COD)": df.get(cod_col, 0),
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
