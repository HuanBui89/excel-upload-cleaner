import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Excel to GHN Format", layout="wide")
st.title("📦 Tạo File Đơn Hàng GHN từ Excel")

REQUIRED_FIELDS = ["Tên người nhận", "SĐT người nhận", "Địa chỉ", "Tên hàng", "Size"]
DEFAULT_VALUES = {
    "Gói cước": 2,
    "Yêu cầu đơn hàng": 2,
    "Khối lượng (g)": 500,
    "Dài (cm)": 10,
    "Rộng (cm)": 10,
    "Cao (cm)": 10,
    "Có/Không": "x",
    "Shop trả ship": "x",
    "Gửi hàng tại bưu cục": "",
    "Mã hàng riêng": "",
    "Ghi chú thêm": "",
    "Ca lấy": 1,
    "Giao thất bại thu tiền": 30000
}
GHN_COLUMNS = [
    "STT", "Mã đơn hàng của KH", "Mã vận đơn", "Tên người nhận", "SĐT người nhận",
    "Địa chỉ", "Phường xã", "Quận huyện", "Tỉnh thành", "Gói cước", "Yêu cầu đơn hàng",
    "Khối lượng (g)", "Dài (cm)", "Rộng (cm)", "Cao (cm)", "Số tiền thu hộ (COD)",
    "Có/Không", "Giá trị hàng hóa", "Shop trả ship", "Gửi hàng tại bưu cục",
    "Mã hàng riêng", "Ghi chú thêm", "Ca lấy", "Giao thất bại thu tiền"
]

def guess_header(df):
    has_header = df.iloc[0].isnull().sum() < len(df.columns) / 2
    return has_header

def process_file(uploaded_file):
    dfs = pd.read_excel(uploaded_file, sheet_name=None)
    results = []
    for sheet_name, df in dfs.items():
        if not guess_header(df):
            df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
        else:
            df.columns = df.iloc[0].astype(str)
            df = df[1:].reset_index(drop=True)

        # Cho người dùng map cột
        st.subheader(f"🔍 Sheet: {sheet_name}")
        mapping = {}
        for req in REQUIRED_FIELDS:
            mapping[req] = st.selectbox(f"Chọn cột cho '{req}'", df.columns, key=f"{sheet_name}_{req}")

        # Xây dựng dataframe kết quả
        result_df = pd.DataFrame()
        result_df["Tên người nhận"] = df[mapping["Tên người nhận"]]
        result_df["SĐT người nhận"] = df[mapping["SĐT người nhận"]]
        result_df["Địa chỉ"] = df[mapping["Địa chỉ"]]
        result_df["Số tiền thu hộ (COD)"] = pd.to_numeric(df[mapping.get("COD", mapping["Số tiền thu hộ (COD)"])], errors='coerce').fillna(0).astype(int)
        result_df["Giá trị hàng hóa"] = result_df["Số tiền thu hộ (COD)"]
        result_df["Tên hàng"] = df[mapping["Tên hàng"]] + " - " + df[mapping["Size"]].astype(str)

        # Gán các cột mặc định
        for col in GHN_COLUMNS:
            if col not in result_df.columns:
                if col in DEFAULT_VALUES:
                    result_df[col] = DEFAULT_VALUES[col]
                else:
                    result_df[col] = ""

        result_df = result_df[GHN_COLUMNS]
        result_df.insert(0, "STT", range(1, len(result_df)+1))
        results.append((sheet_name, result_df))

    return results

uploaded_file = st.file_uploader("📤 Tải lên file Excel", type=["xlsx"])
if uploaded_file:
    try:
        converted = process_file(uploaded_file)
        for sheet_name, df in converted:
            st.success(f"✅ Xử lý xong sheet: {sheet_name}")
            st.dataframe(df)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
            st.download_button(
                label=f"📥 Tải file {sheet_name} đã xử lý",
                data=buffer.getvalue(),
                file_name=f"GHN_{sheet_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý file: {e}")
