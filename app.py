import streamlit as st
import pandas as pd
import io
import hashlib
import datetime
import os

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

uploaded_files = st.file_uploader("📤 Tải lên file .xlsx", accept_multiple_files=True, type=["xlsx"])
mau = st.radio("🎨 Chọn mẫu xuất kết quả", ["Mẫu 1 (Chị Tiền)", "Mẫu 2 (Chị Linh)"], index=1)
mau_color = "green" if mau.startswith("Mẫu 1") else "red"
st.markdown(f"<span style='color:{mau_color}; font-weight:bold'>Bạn đang chọn {mau}</span>", unsafe_allow_html=True)

if uploaded_files:
    all_dfs = []
    file_hashes = set()
    duplicate_files = []
    split_filenames = []

    for file in uploaded_files:
        file_content = file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        if file_hash in file_hashes:
            duplicate_files.append(file.name)
            continue
        file_hashes.add(file_hash)
        file.seek(0)

        try:
            xls = pd.ExcelFile(file)
            for sheet_name in xls.sheet_names:
                df_temp = pd.read_excel(file, sheet_name=sheet_name, header=None)
                first_row = df_temp.iloc[0].astype(str)
                numeric_count = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])

                if numeric_count >= len(first_row) - 2:
                    df = df_temp.copy()
                    df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                    mapping = {
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
                    mapping = auto_map_columns(df.columns.tolist())

                for key in ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]:
                    if mapping.get(key) is None:
                        mapping[key] = st.selectbox(
                            f"🛠 Chọn cột cho '{key}' trong sheet {sheet_name} - {file.name}",
                            options=df.columns.tolist(),
                            key=key + sheet_name + file.name
                        )

                df = df.dropna(subset=[mapping["họ tên"], mapping["số điện thoại"], mapping["địa chỉ"]])
                df["tên sản phẩm"] = df[mapping["tên hàng"]].astype(str) + " Size " + df[mapping["size"]].astype(str)
                df["Tiền COD"] = pd.to_numeric(df[mapping["số tiền thu hộ"]], errors="coerce").fillna(0).astype(int)
                df["Tên"] = df[mapping["họ tên"]].astype(str)
                df["SĐT"] = df[mapping["số điện thoại"]].astype(str)
                df["Địa chỉ"] = df[mapping["địa chỉ"]].astype(str)
                df["Ghi chú thêm"] = ""

                all_dfs.append(df)

        except Exception as e:
            st.error(f"❌ Lỗi đọc file {file.name}: {e}")

    if duplicate_files:
        st.warning(f"⚠️ Các file trùng lặp nội dung đã bị bỏ qua: {', '.join(duplicate_files)}")

    if all_dfs:
        full_df = pd.concat(all_dfs, ignore_index=True)

        if mau.startswith("Mẫu 2"):
            full_df.insert(0, "Tên người nhận", [f"{i+1}_{name}" for i, name in enumerate(full_df["Tên"])])
            full_df["Ghi chú thêm"] = full_df["tên sản phẩm"] + " - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
        else:
            full_df.insert(0, "Tên người nhận", full_df["Tên"])

        result = pd.DataFrame({
            "Tên người nhận": full_df["Tên người nhận"],
            "Số điện thoại": full_df["SĐT"],
            "Số nhà/ngõ/ngách/hẻm, Đường/Phố, Phường/Xã, Quận/Huyện, Tỉnh/Thành": full_df["Địa chỉ"],
            "Gói cước": 2,
            "Tiền thu hộ": full_df["Tiền COD"],
            "Yêu cầu đơn hàng": 2,
            "Khối lượng (gram)": 500,
            "Chiều dài (cm)": 10,
            "Chiều rộng (cm)": 10,
            "Chiều cao (cm)": 10,
            "Khai giá": "x",
            "Giá trị hàng hoá": full_df["Tiền COD"],
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

        output = io.BytesIO()
        result.to_excel(output, index=False, engine='openpyxl')
        st.download_button("📥 Tải file GHN", data=output.getvalue(), file_name="GHN_output.xlsx")

        if mau.startswith("Mẫu 2") and len(result) > 300:
            if st.button("📂 Tách file GHN thành từng 300 đơn"):
                now = datetime.datetime.now().strftime("%-d.%-m")
                for idx, chunk in enumerate([result[i:i+300] for i in range(0, len(result), 300)]):
                    start = idx * 300 + 1
                    end = min((idx + 1) * 300, len(result))
                    filename = f"GHN_{now}_SHOP TUONG VY_TOI {start}-{end}.xlsx"
                    filepath = os.path.join("/mnt/data", filename)
                    chunk.to_excel(filepath, index=False)
                    st.markdown(f"📥 [Tải {filename}](sandbox:/mnt/data/{filename})")
                st.success("✅ Đã tách và tạo link tải nhanh các file!")
