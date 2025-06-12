import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="APP TẠO ĐƠN THEO MẪU GHN", layout="centered")

st.title("📦 APP TẠO ĐƠN THEO MẪU GHN")
st.markdown("📄 **Chọn mẫu xuất kết quả:**")

# Dropdown chọn mẫu
template_option = st.selectbox(
    "📑 Chọn mẫu xuất kết quả:",
    ["📗 Mẫu 1 - Chị Tiền", "📕 Mẫu 2 - Chị Linh", "📘 Mẫu 3 - Chị Thúy"]
)

# Hàm xử lý cho mẫu chị Thúy
def apply_mau_chi_thuy(df):
    df = df.copy()
    stt_counter = {}
    new_san_pham = []
    new_ghi_chu = []

    for idx, row in df.iterrows():
        ten_sp_goc = str(row.get("Sản phẩm", ""))
        ghi_chu_goc = str(row.get("Ghi chú", ""))
        
        # Tìm size từ ghi chú gốc (ví dụ: "49kg")
        size = ""
        for token in ghi_chu_goc.split():
            if "kg" in token.lower():
                size = token
                break

        # Bỏ "4B" nếu có
        sp_clean = ten_sp_goc.strip()
        if sp_clean.upper().startswith("4B "):
            sp_core = sp_clean[3:].strip()
        else:
            sp_core = sp_clean

        # Đếm thứ tự theo tên gốc (sau khi bỏ "4B")
        stt_counter.setdefault(sp_core, 0)
        stt_counter[sp_core] += 1
        stt = stt_counter[sp_core]

        # Gán lại tên sản phẩm
        new_name = f"{sp_core} D.12.6.{stt}"
        new_san_pham.append(new_name)

        # Gán lại ghi chú
        new_note = f"{new_name} [{ten_sp_goc} {size}] - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
        new_ghi_chu.append(new_note)

    df["Sản phẩm"] = new_san_pham
    df["Ghi chú"] = new_ghi_chu
    return df


uploaded_file = st.file_uploader("📤 Upload file Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    if "Chị Tiền" in template_option:
        st.success("✅ Đang xử lý theo Mẫu 1 - Chị Tiền")
        # Logic gốc giữ nguyên
        st.dataframe(df)

    elif "Chị Linh" in template_option:
        st.success("✅ Đang xử lý theo Mẫu 2 - Chị Linh")
        # Logic gốc giữ nguyên
        st.dataframe(df)

    elif "Chị Thúy" in template_option:
        st.success("✅ Đang xử lý theo Mẫu 3 - Chị Thúy")
        df = apply_mau_chi_thuy(df)
        st.dataframe(df)

    # Nút tải xuống
    @st.cache_data
    def convert_df(df):
        return df.to_excel(index=False, engine='openpyxl')

    if st.button("📥 Tải về file kết quả"):
        out = convert_df(df)
        st.download_button(
            label="📄 Tải file Excel",
            data=out,
            file_name="output_mau_giaodich.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
