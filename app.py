import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
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

style = st.radio("📌 Chọn mẫu kết quả", ["Mẫu 1 (Chị Tiền)", "Mẫu 2 (Chị Linh)"], index=1, horizontal=True)
st.markdown(f"<div style='background-color: {'#e0f7fa' if style=='Mẫu 1 (Chị Tiền)' else '#ffebee'}; padding: 10px; font-weight: bold;'>{style}</div>", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

collected_data = []
final_mappings = []

if uploaded_files:
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
                    auto_mapping = {
                        "họ tên": df.columns[2] if len(df.columns) > 2 else None,
                        "số điện thoại": df.columns[3] if len(df.columns) > 3 else None,
                        "địa chỉ": df.columns[4] if len(df.columns) > 4 else None,
                        "tên hàng": df.columns[5] if len(df.columns) > 5 else None,
                        "size": df.columns[6] if len(df.columns) > 6 else None,
                        "số tiền thu hộ": df.columns[7] if len(df.columns) > 7 else None
                    }
                else:
                    df = df_temp[1:].copy()
                    df.columns = first_row
                    auto_mapping = auto_map_columns(df.columns.tolist())

                st.subheader(f"📄 Sheet: {sheet_name if sheet_name else 'CSV'}")
                st.write("📋 Các cột phát hiện:")
                st.write(df.iloc[0].to_dict())

                required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                mapping = {}

                for field in required_fields:
                    if auto_mapping.get(field):
                        mapping[field] = auto_mapping[field]
                    else:
                        mapping[field] = st.selectbox(
                            f"Chọn cột cho '{field.capitalize()}'",
                            options=df.columns.tolist(),
                            key=field + str(sheet_name) + file.name
                        )
                final_mappings.append((df, mapping))

        except Exception as e:
            st.error(f"❌ Lỗi đọc file {file.name}: {e}")

    if final_mappings:
        full_df = pd.DataFrame()
        for df, mapping in final_mappings:
            df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)
            df["họ tên"] = df[mapping["họ tên"]]
            df["số điện thoại"] = df[mapping["số điện thoại"]]
            df["địa chỉ"] = df[mapping["địa chỉ"]]
            df["giá trị"] = df[mapping["số tiền thu hộ"]]
            df["ghi chú thêm"] = ""

            full_df = pd.concat([full_df, df], ignore_index=True)

        # Cảnh báo trùng lặp
        dup_mask = full_df.duplicated(subset=["họ tên", "số điện thoại", "địa chỉ"], keep=False)
        if dup_mask.any():
            st.warning("⚠️ Phát hiện đơn hàng bị trùng tên + số điện thoại + địa chỉ!")
            st.dataframe(full_df[dup_mask])

        if style == "Mẫu 2 (Chị Linh)":
            full_df["STT"] = range(1, len(full_df) + 1)
            full_df["Họ tên người nhận"] = full_df["STT"].astype(str) + "_" + full_df["họ tên"].astype(str)
            full_df["Ghi chú thêm"] = full_df["tên sản phẩm"] + " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
        else:
            full_df["Họ tên người nhận"] = full_df["họ tên"]
            full_df["Ghi chú thêm"] = ""

        result = pd.DataFrame({
            "Tên người nhận": full_df["Họ tên người nhận"],
            "Số điện thoại": full_df["số điện thoại"],
            "Số nhà/ngõ/ngách/hẻm, Đường/Phố, Phường/Xã, Quận/Huyện, Tỉnh/Thành": full_df["địa chỉ"],
            "Gói cước": 2,
            "Tiền thu hộ": full_df["giá trị"],
            "Yêu cầu đơn hàng": 2,
            "Khối lượng (gram)": 500,
            "Chiều dài (cm)": 10,
            "Chiều rộng (cm)": 10,
            "Chiều cao (cm)": 10,
            "Khai giá": "x",
            "Giá trị hàng hoá": full_df["giá trị"],
            "Shop trả ship": "x",
            "Gửi hàng tại bưu cục": "",
            "Mã đơn hàng riêng": "",
            "Sản phẩm": full_df["tên sản phẩm"],
            "Ghi chú thêm": full_df["Ghi chú thêm"],
            "Ca lấy": 1,
            "Giao hàng thất bại thu tiền": 30000
        })

        st.success("✅ Đã xử lý thành công tất cả file và sheet!")
        st.dataframe(result)

        towrite = io.BytesIO()
        result.to_excel(towrite, index=False, engine="openpyxl")
        st.download_button("📥 Tải file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx")
