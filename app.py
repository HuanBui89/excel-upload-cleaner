import streamlit as st
import pandas as pd
import io
import hashlib
import os
import tempfile
from datetime import datetime
import re
from collections import defaultdict
import streamlit.components.v1 as components

st.set_page_config(page_title="GHN Upload Tool", layout="wide")
st.title("📦 APP TẠO ĐƠN THEO MẪU GHN")

log_file = "history_logs.csv"
if not os.path.exists(log_file):
    pd.DataFrame(columns=["Time", "Filename", "Total Orders"]).to_csv(log_file, index=False)

if "template_option" not in st.session_state:
    st.session_state.template_option = "Mẫu 2 - Chị Linh"

template_labels = {
    "Mẫu 1 - Chị Tiền": "📗 Mẫu 1 - Chị Tiền",
    "Mẫu 2 - Chị Linh": "📕 Mẫu 2 - Chị Linh",
    "Mẫu 3 - Chị Thúy": "📘 Mẫu 3 - Chị Thúy"
}
label_to_value = {v: k for k, v in template_labels.items()}
default_option = template_labels[st.session_state.get("template_option", "Mẫu 2 - Chị Linh")]

st.markdown(f"""
<style>
div[data-baseweb="select"] {{
    width: fit-content !important;
    min-width: 280px;
    padding: 2px;
}}
div[data-baseweb="select"] > div {{
    background-color: {"#28a745" if "Mẫu 1" in default_option else "#dc3545"} !important;
    color: white !important;
    font-weight: bold;
    border-radius: 6px;
    border: 2px solid #000;
}}
label[for="template_label"] {{
    font-weight: bold;
    font-size: 16px;
    color: #dc3545;
    margin-bottom: 5px;
    display: block;
}}
</style>
""", unsafe_allow_html=True)

selected_label = st.selectbox(
    "📝 Chọn mẫu xuất kết quả:",
    options=list(template_labels.values()),
    index=list(template_labels.values()).index(default_option),
    key="template_label"
)

st.session_state.template_option = label_to_value[selected_label]
template_option = st.session_state.template_option

def auto_map_columns(columns):
    mapping = {}
    keywords = {
        "họ tên": ["khách", "họ", "tên", "khách hàng"],
        "số điện thoại": ["sdt", "sđt", "điện", "mobile"],
        "địa chỉ": ["địa chỉ", "địa", "dc"],
        "tên hàng": ["sản phẩm", "gồm", "sp", "tên hàng"],
        "size": ["ghi chú", "size", "mô tả", "note"],
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

def is_valid_row(row):
    phone_pattern = re.compile(r"\b0\d{9,10}\b")
    cod_pattern = re.compile(r"\b\d{5,}\b")
    row_str = " ".join([str(cell) for cell in row])
    if phone_pattern.search(row_str) and cod_pattern.search(row_str):
        return True
    keywords = ['khách hàng', 'tổng', 'số lượng', 'sản phẩm', 'địa chỉ']
    if any(kw in row_str.lower() for kw in keywords):
        return False
    return False

uploaded_files = st.file_uploader("Tải lên file .xlsx hoặc .csv", accept_multiple_files=True)

if uploaded_files:
    all_rows = []
    duplicates = set()
    content_hashes = set()

    for file in uploaded_files:
        file_bytes = file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()

        if file_hash in content_hashes:
            duplicates.add(file.name)
            continue
        else:
            content_hashes.add(file_hash)

        ext = file.name.split(".")[-1].lower()
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            if ext == "xlsx":
                xls = pd.ExcelFile(tmp_path)
                sheets = xls.sheet_names
            else:
                sheets = [None]

            for sheet in sheets:
                df_temp = pd.read_excel(tmp_path, sheet_name=sheet, header=None) if ext == "xlsx" else pd.read_csv(tmp_path, header=None)
                first_row = df_temp.iloc[0].astype(str)
                numeric_count = sum([cell.strip().replace('.', '', 1).isdigit() for cell in first_row])

                if numeric_count >= len(first_row) - 2:
                    df = df_temp.copy()
                    df.columns = [f"Cột {i+1}" for i in range(df.shape[1])]
                    auto_mapping = {key: df.columns[i+2] for i, key in enumerate(["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"])}
                else:
                    df = df_temp[1:].copy()
                    df.columns = first_row
                    auto_mapping = auto_map_columns(df.columns.tolist())

                df = df[df.apply(is_valid_row, axis=1)].reset_index(drop=True)

                required_fields = ["họ tên", "số điện thoại", "địa chỉ", "tên hàng", "size", "số tiền thu hộ"]
                final_mapping = {
                    field: auto_mapping.get(field) or st.selectbox(
                        f"Chọn cột cho '{field}'", df.columns.tolist(), key=f"{field}_{sheet}_{file.name}"
                    ) for field in required_fields
                }

                df["Tên sản phẩm"] = df[final_mapping["tên hàng"]].astype(str).str.strip()
                df["Size gốc"] = df[final_mapping["size"]].astype(str).str.strip()
                df["Ghi chú thêm"] = ""
                df["Tên người nhận"] = df[final_mapping["họ tên"]]
                df["Số điện thoại"] = df[final_mapping["số điện thoại"]]
                df["Địa chỉ"] = df[final_mapping["địa chỉ"]]
                df["Tiền thu hộ"] = df[final_mapping["số tiền thu hộ"]]

                all_rows.append(df)

        except Exception as e:
            st.error(f"❌ Lỗi đọc file {file.name}: {e}")

    if duplicates:
        st.error(f"⚠️ File trùng nội dung bị bỏ qua: {', '.join(duplicates)}")

    if all_rows:
        df_all = pd.concat(all_rows, ignore_index=True)

        final = pd.DataFrame({
            "Tên người nhận": df_all["Tên người nhận"],
            "Số điện thoại": df_all["Số điện thoại"],
            "Địa chỉ": df_all["Địa chỉ"],
            "Gói cước": 2,
            "Tiền thu hộ": df_all["Tiền thu hộ"],
            "Yêu cầu đơn hàng": 3,
            "Khối lượng": 500,
            "Dài": 10, "Rộng": 10, "Cao": 10,
            "Khai giá": "x",
            "Giá trị hàng": df_all["Tiền thu hộ"],
            "Shop trả ship": "x", "Bưu cục": "",
            "Mã đơn riêng": "",
            "Sản phẩm": df_all["Tên sản phẩm"],
            "Ghi chú thêm": "",
            "Ca lấy": 1, "Giao thất bại thu": 30000
        })

    if template_option == "Mẫu 3 - Chị Thúy":
        import re
        now = datetime.now()
        day = now.day
        month = now.month

        product_counter = defaultdict(int)
        ma_don_list = []
        ghi_chu_list = []

        # Gốc: dùng trong Ghi chú
        ten_sp_raw_list = df_all["Tên sản phẩm"].tolist()
        # Size gốc
        size_goc_list = df_all["Size gốc"].tolist()

        for idx, row in final.iterrows():
            ten_sp_goc = str(ten_sp_raw_list[idx]).strip()
            size_goc = str(size_goc_list[idx]).strip()

            # ✅ Rút gọn tiền tố (4B, 2, v.v.) cho mã đơn riêng
            ten_sp_rut_gon = re.sub(r'^\\s*\\d+[A-Z]*\\s+', '', ten_sp_goc)

            # ✅ Tính số thứ tự theo tên rút gọn
            product_counter[ten_sp_rut_gon] += 1
            stt = product_counter[ten_sp_rut_gon]

            # ✅ Mã đơn riêng (dùng tên rút gọn)
            ma_don_rieng = f"{ten_sp_rut_gon} D.{day}.{month}.{stt}"
            ma_don_list.append(ma_don_rieng)

            # ✅ Ghi chú (dùng tên sản phẩm gốc)
            ghi_chu = f"{ma_don_rieng} [{ten_sp_goc} {size_goc}] - KHÁCH KHÔNG NHẬN THU 30K, GỌI VỀ SHOP KHI ĐƠN SAI THÔNG TIN"
            ghi_chu_list.append(ghi_chu)

            final["Mã đơn riêng"] = ma_don_list
            final["Ghi chú thêm"] = ghi_chu_list



        if template_option == "Mẫu 2 - Chị Linh":
            final["Tên người nhận"] = (final.index + 1).astype(str) + "_" + final["Tên người nhận"].astype(str)

        mau_text = template_option.replace("Mẫu", "Theo mẫu")
        st.success(f"✅ Xử lý thành công! Tổng số đơn: {len(final)} – {mau_text}")
        st.dataframe(final)

        towrite = io.BytesIO()
        final.to_excel(towrite, index=False)
        st.download_button("📥 Tải file GHN", data=towrite.getvalue(), file_name="GHN_output.xlsx")

        log_df = pd.read_csv(log_file)
        new_log = pd.DataFrame([[datetime.now(), ', '.join([f.name for f in uploaded_files]), len(final)]],
                               columns=["Time", "Filename", "Total Orders"])
        log_df = pd.concat([log_df, new_log])
        log_df["Time"] = pd.to_datetime(log_df["Time"])
        log_df = log_df.sort_values(by="Time", ascending=False)
        log_df.to_csv(log_file, index=False)

with st.expander("📜 Lịch sử 3 ngày gần đây"):
    log_df = pd.read_csv(log_file)
    log_df["Time"] = pd.to_datetime(log_df["Time"])
    recent_log = log_df[log_df["Time"] >= pd.Timestamp.now() - pd.Timedelta(days=3)]
    st.dataframe(recent_log)

components.html("""
<script>
const fileInput = window.parent.document.querySelector('input[type=file]');
if (fileInput) {
  fileInput.addEventListener('change', (e) => {
    let newFiles = [];
    for (let i = 0; i < fileInput.files.length; i++) {
      let file = fileInput.files[i];
      const safeName = file.name.normalize('NFD')
                                 .replace(/[̀-ͯ]/g, '')
                                 .replace(/[^A-Za-z0-9_.]/g, '_');
      if (file.name !== safeName) {
        const renamed = new File([file], safeName, {
          type: file.type,
          lastModified: file.lastModified
        });
        newFiles.push(renamed);
      } else {
        newFiles.push(file);
      }
    }
    const dt = new DataTransfer();
    newFiles.forEach(f => dt.items.add(f));
    fileInput.files = dt.files;
  });
}
</script>
""", height=0)
