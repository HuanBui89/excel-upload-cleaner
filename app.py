import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="APP TẠO ĐƠN GHN", layout="centered")
st.title("📦 APP TẠO ĐƠN GHN")
st.markdown("👉 Chọn mẫu xuất kết quả:")

# Chọn mẫu
template_option = st.selectbox(
    "📑 Chọn mẫu:",
    ["📗 Mẫu 1 - Chị Tiền", "📕 Mẫu 2 - Chị Linh", "📘 Mẫu 3 - Chị Thúy"]
)

uploaded_file = st.file_uploader("📤 Tải file Excel", type=["xlsx"])

# Hàm xử lý sản phẩm và ghi chú cho mẫu chị Thúy
def process_chi_thuy(df):
    df = df.copy()
    stt_map = {}

    for i, row in df.iterrows():
        ten_sp_goc = str(row.get("Sản phẩm", "")).strip()
        ghi_chu_goc = str(row.get("Ghi chú", "")).strip()

        # Bỏ 3 ký tự đầu
        sp_core = ten_sp_goc[3:].strip() if len(ten_sp_goc) > 3 else ten_sp_goc

        # STT theo từng tên gốc
        stt_map.setdefault(sp_core, 0)
        stt_map[sp_core] += 1
        stt = stt_map[sp_core]

        # Sản phẩm mới
        ten_sp_moi = f"{sp_core} D.12.6.{stt}"

        # Tìm size từ ghi chú (ví dụ: 50kg)
        size = ""
        for word in ghi_chu_goc.split():
            if "kg" in word.lower():
                size = word
                break

        # Ghi chú mới
        ghi_chu_moi = f"{ten_sp_moi} [{ten_sp_goc} {size}] - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"

        df.at[i, "Sản phẩm"] = ten_sp_moi
        df.at[i, "Ghi chú"] = ghi_chu_moi

    return df

# Hàm xuất file Excel
def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Đơn hàng")
    return output.getvalue()

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    if "Chị Tiền" in template_option:
        st.success("✅ Đang xử lý theo Mẫu 1 - Chị Tiền")
        df_result = df.copy()  # hoặc xử lý riêng theo logic chị Tiền nếu có

    elif "Chị Linh" in template_option:
        st.success("✅ Đang xử lý theo Mẫu 2 - Chị Linh")
        df_result = df.copy()  # hoặc xử lý riêng theo logic chị Linh nếu có

    elif "Chị Thúy" in template_option:
        st.success("✅ Đang xử lý theo Mẫu 3 - Chị Thúy")
        df_result = df.copy()
        df_result = process_chi_thuy(df_result)

    st.dataframe(df_result)

    # Nút tải về
    if st.button("📥 Tải file kết quả"):
        excel_bytes = to_excel_bytes(df_result)
        st.download_button(
            label="📄 Tải file Excel",
            data=excel_bytes,
            file_name="output_don_chi_thuy.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
