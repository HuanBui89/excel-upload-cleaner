import streamlit as st
import pandas as pd
import zipfile
import io
from datetime import datetime

st.set_page_config(page_title="GHN Excel Processor", layout="wide")

def read_excel_files(uploaded_files):
    all_data = []
    file_names = set()
    for uploaded_file in uploaded_files:
        if uploaded_file.name in file_names:
            st.warning(f"⚠️ File '{uploaded_file.name}' đã được tải lên trước đó và sẽ bị bỏ qua.")
            continue
        file_names.add(uploaded_file.name)
        xls = pd.ExcelFile(uploaded_file)
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name)
            df["Tên File"] = uploaded_file.name
            df["Tên Sheet"] = sheet_name
            all_data.append(df)
    return all_data

def normalize_columns(df):
    columns_map = {
        "Số điện thoại người nhận": "phone",
        "Số điện thoại": "phone",
        "Tên người nhận": "name",
        "Địa chỉ": "address",
        "Tỉnh/Thành phố": "province",
        "Quận/Huyện": "district",
        "Phường/Xã": "ward",
        "Ghi chú": "note",
        "Tên sản phẩm": "product_name",
        "Giá thu hộ": "cod"
    }
    df = df.rename(columns={col: columns_map.get(col, col) for col in df.columns})
    return df

def apply_chi_thuy_format(df):
    df = normalize_columns(df)
    if "product_name" not in df.columns:
        st.error("❌ Không tìm thấy cột 'Tên sản phẩm'.")
        return df

    counter_map = {}
    new_names = []
    new_notes = []

    for _, row in df.iterrows():
        original_name = str(row.get("product_name", "")).strip()
        note = str(row.get("note", "")).strip()

        # Lấy size từ ghi chú
        size = ""
        for word in note.split():
            if "kg" in word.lower():
                size = word
                break

        name_with_size = f"{original_name} [{size}]" if size else original_name
        base_name = original_name.replace("4B", "").strip()

        count = counter_map.get(base_name, 0) + 1
        counter_map[base_name] = count

        new_name = f"{base_name} D.12.6.{count} [{size}]" if size else f"{base_name} D.12.6.{count}"
        new_note = f"{name_with_size} - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"

        new_names.append(new_name)
        new_notes.append(new_note)

    df["product_name"] = new_names
    df["note"] = new_notes
    return df

def split_dataframe(df, max_rows=300):
    return [df[i:i + max_rows] for i in range(0, df.shape[0], max_rows)]

def export_to_zip(splits, prefix):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, chunk in enumerate(splits):
            buffer = io.BytesIO()
            chunk.to_excel(buffer, index=False)
            zip_file.writestr(f"{prefix}_part{i+1}.xlsx", buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

st.title("📦 GHN Excel Processor")
st.markdown("Tải lên file Excel đơn hàng từ nhiều mẫu, xử lý và xuất theo định dạng chuẩn.")

uploaded_files = st.file_uploader("📁 Tải lên file Excel", type=["xlsx"], accept_multiple_files=True)

template = st.radio("🎨 Chọn mẫu xử lý", ["Chị Tiền", "Chị Linh", "Chị Thúy"])

if st.button("🚀 Xử lý và Tải xuống"):
    if not uploaded_files:
        st.warning("⚠️ Vui lòng tải lên ít nhất một file Excel.")
    else:
        all_data = read_excel_files(uploaded_files)
        if not all_data:
            st.error("❌ Không có dữ liệu để xử lý.")
        else:
            df_all = pd.concat(all_data, ignore_index=True)

            if template == "Chị Tiền":
                pass  # Không thay đổi
            elif template == "Chị Linh":
                df_all.insert(0, "STT", range(1, len(df_all) + 1))
                df_all["Ghi chú"] = df_all.get("Ghi chú", "") + " - Đơn mẫu Chị Linh"
            elif template == "Chị Thúy":
                df_all = apply_chi_thuy_format(df_all)

            chunks = split_dataframe(df_all)
            zip_file = export_to_zip(chunks, f"{template.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            st.success(f"✅ Hoàn tất xử lý {len(df_all)} đơn hàng theo mẫu {template}.")
            st.download_button("📥 Tải file ZIP", data=zip_file, file_name="don_giao_hang.zip", mime="application/zip")
