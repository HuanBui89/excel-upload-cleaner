import streamlit as st
import pandas as pd
from io import BytesIO
import unicodedata

# Hàm tiện ích: bỏ dấu tiếng Việt (để so khớp không phân biệt dấu)
def remove_accents(input_str: str) -> str:
    if not isinstance(input_str, str):
        input_str = str(input_str)
    return ''.join(ch for ch in unicodedata.normalize('NFD', input_str) if unicodedata.category(ch) != 'Mn')

# Hàm đọc CSV với encoding phù hợp (thử một số encoding phổ biến)
def read_csv_any_encoding(file):
    encodings = ['utf-8', 'utf-8-sig', 'latin1']
    for enc in encodings:
        try:
            file.seek(0)
            return pd.read_csv(file, header=None, encoding=enc)
        except Exception:
            continue
    file.seek(0)
    return pd.read_csv(file, header=None)

# Tiêu đề ứng dụng
st.title("Excel to GHN Format Converter")
st.write("Upload Excel/CSV files and map the columns to GHN format. Hỗ trợ tự động nhận diện và chọn thủ công khi cần.")

# Upload nhiều file
uploaded_files = st.file_uploader("📂 Tải lên file Excel hoặc CSV", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

if uploaded_files:
    combined_output = []   # Danh sách dữ liệu sau khi chuẩn hóa từ các file/sheet
    all_mapped = True      # Cờ để kiểm tra xem mọi trường bắt buộc đã được map hay chưa

    # Cho phép người dùng chọn khối lượng mặc định nếu không có cột khối lượng
    default_weight = st.number_input("Khối lượng mặc định (gram) nếu không có cột khối lượng:", min_value=0, value=100, step=50)

    # Duyệt từng file đã upload
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        try:
            # Đọc file vào DataFrame (hỗ trợ nhiều sheet nếu là Excel)
            if file_name.lower().endswith(('.csv', '.txt')):
                # File CSV
                df_list = [ read_csv_any_encoding(uploaded_file) ]
                sheet_names = ["CSV"]
            else:
                # File Excel
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                df_list = []
                for sheet in sheet_names:
                    df_sheet = pd.read_excel(xls, sheet_name=sheet, header=None)
                    # Bỏ qua sheet trống
                    if df_sheet.shape[0] == 0:
                        continue
                    df_list.append(df_sheet)
        except Exception as e:
            st.error(f"❌ Lỗi khi đọc file {file_name}: {e}")
            all_mapped = False
            continue

        # Duyệt từng DataFrame (tương ứng với từng sheet)
        for idx, df in enumerate(df_list):
            sheet_name = sheet_names[idx] if idx < len(sheet_names) else f"Sheet{idx+1}"
            header_present = False

            # Kiểm tra dòng đầu tiên để xác định header
            if df.shape[0] > 0:
                first_row = df.iloc[0].astype(str).fillna("").tolist()
                first_row_texts = [remove_accents(x).lower() for x in first_row]
                # Tập từ khóa gợi ý header (viết không dấu, chữ thường)
                header_keywords = [
                    "tên", "ten", "họ tên", "ho ten", "họ", "ho ", 
                    "sdt", "điện tho", "dien tho", "đt", "so dt", "phone", 
                    "địa chỉ", "dia chi", "đc", "dc ", "address", 
                    "sản ph", "san ph", "hàng", "hang", "sp ", "product", 
                    "size", "phân loại", "phan loai", "màu", "mau", 
                    "cod", "thu hộ", "thu ho", "tiền thu", "tien thu", 
                    "số lượng", "so luong", "sl", 
                    "khối lượng", "khoi luong", "trọng lượng", "trong luong", "weight", 
                    "ghi chú", "ghi chu"
                ]
                matches = 0
                for cell in first_row_texts:
                    for kw in header_keywords:
                        if kw in cell:
                            matches += 1
                            break
                # Nếu xuất hiện từ khóa >=2 cột, giả định có header
                if matches >= 2:
                    header_present = True

            # Nếu có header: đặt tên cột và bỏ dòng header khỏi data
            if header_present:
                new_header = df.iloc[0].fillna("").astype(str).tolist()
                df = df[1:].reset_index(drop=True)
                # Xử lý trường hợp trùng tên cột
                cols = []
                seen = {}
                for col in new_header:
                    col = col.strip()
                    if col == "" or col is None:
                        col = "Column"
                    if col in seen:
                        seen[col] += 1
                        col = f"{col}_{seen[col]}"
                    else:
                        seen[col] = 1
                    cols.append(col)
                df.columns = cols
            else:
                # Nếu không có header: đặt tên cột là số thứ tự (0,1,2,...)
                df.columns = list(range(df.shape[1]))

            # Hiển thị tên file và sheet hiện tại
            st.subheader(f"📑 {file_name} - {sheet_name}")
            # Hiển thị thông tin cột hoặc dòng đầu tùy trường hợp
            if header_present:
                st.write("Các cột tiêu đề tìm thấy:", list(df.columns))
            else:
                st.write("Dòng đầu tiên của dữ liệu (để tham khảo các cột):")
                st.json(df.head(1).to_dict(orient='records'))

            # Tự động gợi ý mapping cột theo tiêu đề/dữ liệu
            name_col = phone_col = addr_col = product_col = size_col = cod_col = qty_col = weight_col = note_col = order_col = None
            if header_present:
                for col in df.columns:
                    col_str = str(col)
                    col_lower = remove_accents(col_str).lower()
                    # Mã đơn hàng (ưu tiên nhận diện trước vì chứa từ 'hàng')
                    if any(x in col_lower for x in ["mã", "ma ", "code", "đơn hàng", "don hang", "order"]):
                        order_col = col
                        continue
                    # Họ tên
                    if any(x in col_lower for x in ["họ tên", "ho ten", "ten nguoi", "tên nguoi", "ten kh", "tên kh", "khach", "người nhận", "nguoi nhan", "name"]):
                        if not ("sản" in col_lower or "hang" in col_lower or "hàng" in col_lower or "don hang" in col_lower):
                            name_col = col
                            continue
                    # Số điện thoại
                    if any(x in col_lower for x in ["sdt", "điện tho", "dien tho", "phone", "mobile", "số điện thoại", "so dt"]):
                        phone_col = col
                        continue
                    # Địa chỉ
                    if any(x in col_lower for x in ["địa chỉ", "dia chi", "address", "đc", "dc ", "đ/c"]):
                        addr_col = col
                        continue
                    # Tên sản phẩm/hàng hóa
                    if any(x in col_lower for x in ["sản phẩm", "san pham", "tên hàng", "ten hang", "hàng hóa", "hang hoa", "sp "]):
                        product_col = col
                        continue
                    # Size / Phân loại / Màu sắc
                    if "size" in col_lower or "phân loại" in col_lower or "phan loai" in col_lower or "màu" in col_lower or "mau" in col_lower:
                        size_col = col
                        continue
                    # Tiền thu hộ (COD)
                    if "cod" in col_lower or "thu hộ" in col_lower or "thu ho" in col_lower or "tiền thu" in col_lower or "tien thu" in col_lower:
                        cod_col = col
                        continue
                    # Số lượng
                    if any(x in col_lower for x in ["số lượng", "so luong", "sl", "qty", "quantity"]):
                        qty_col = col
                        continue
                    # Khối lượng
                    if any(x in col_lower for x in ["khối lượng", "khoi luong", "gram", "trọng lượng", "trong luong", "weight"]):
                        weight_col = col
                        continue
                    # Ghi chú
                    if any(x in col_lower for x in ["ghi chú", "ghi chu", "note"]):
                        note_col = col
                        continue
            else:
                # Nếu không có header: gợi ý theo vị trí mặc định
                if 2 in df.columns: name_col = 2
                if 3 in df.columns: phone_col = 3
                if 4 in df.columns: addr_col = 4
                if 5 in df.columns: product_col = 5
                if 6 in df.columns: size_col = 6
                if 7 in df.columns: cod_col = 7
                # Cột 1 thường là số lượng (nếu toàn số)
                if 1 in df.columns:
                    col1_vals = df[1].dropna()
                    if len(col1_vals) > 0 and pd.to_numeric(col1_vals, errors='coerce').notna().mean() > 0.9:
                        qty_col = 1
                # Cột 0 có thể là mã đơn hàng nếu không phải toàn số
                if 0 in df.columns:
                    col0_vals = df[0].astype(str).fillna("")
                    if not pd.to_numeric(col0_vals, errors='coerce').notna().all():
                        order_col = 0

            # Tạo danh sách lựa chọn cho các cột
            options = []
            for col in df.columns:
                if header_present:
                    label = str(col)
                else:
                    label = f"Cột {col+1}" if isinstance(col, int) else f"Cột {col}"
                options.append(label)
            label_to_col = {options[i]: df.columns[i] for i in range(len(df.columns))}
            placeholder_option = "- Chọn -"

            # Danh sách các trường cần map (tên trường, cột gợi ý, bắt buộc hay không)
            fields = [
                ("họ tên", name_col, True),
                ("số điện thoại", phone_col, True),
                ("địa chỉ", addr_col, True),
                ("tên hàng", product_col, True),
                ("size", size_col, True),
                ("tiền thu hộ (COD)", cod_col, True),
                ("số lượng", qty_col, False),
                ("khối lượng (gram)", weight_col, False),
                ("ghi chú", note_col, False),
                ("mã đơn hàng", order_col, False)
            ]

            # Hiển thị các selectbox cho mapping
            selected_cols = {}
            for field_label, suggested_col, required in fields:
                opts = [placeholder_option] + options if not required else options
                default_index = 0
                if suggested_col is not None:
                    for lab, colval in label_to_col.items():
                        if colval == suggested_col:
                            if required:
                                default_index = options.index(lab)
                            else:
                                default_index = opts.index(lab) if lab in opts else 0
                            break
                # Tạo selectbox cho trường
                choice = st.selectbox(f"Chọn cột cho '{field_label}'", options=opts, index=default_index, key=f"{file_name}_{sheet_name}_{field_label}")
                if choice == placeholder_option or choice is None:
                    selected_cols[field_label] = None
                else:
                    selected_cols[field_label] = label_to_col[choice]

            # Kiểm tra các trường bắt buộc đã được chọn chưa
            dataset_mapped = True
            for field_label, _, required in fields:
                if required and selected_cols.get(field_label) is None:
                    dataset_mapped = False
                    all_mapped = False
                    st.error(f"⚠️ Chưa chọn cột cho trường bắt buộc: {field_label}")
            # Nếu tất cả trường bắt buộc đã có, tạo DataFrame kết quả cho sheet này
            if dataset_mapped:
                out_df = pd.DataFrame()
                out_df["Họ tên"] = df[selected_cols["họ tên"]].astype(str).fillna("")
                # Số điện thoại dạng text (giữ các số 0 đầu nếu có)
                out_df["Số điện thoại"] = df[selected_cols["số điện thoại"]].apply(lambda x: str(x).split('.')[0] if pd.notna(x) else "")
                out_df["Địa chỉ"] = df[selected_cols["địa chỉ"]].astype(str).fillna("")
                out_df["Tên hàng"] = df[selected_cols["tên hàng"]].astype(str).fillna("")
                out_df["Size"] = df[selected_cols["size"]].astype(str).fillna("")
                # Xử lý COD: loại bỏ dấu phẩy/chấm và chuyển thành số int
                cod_series = df[selected_cols["tiền thu hộ (COD)"]]
                cod_cleaned = cod_series.apply(lambda x: str(x).replace(",", "").replace(".", "") if pd.notna(x) else "0")
                out_df["Số tiền thu hộ (COD)"] = pd.to_numeric(cod_cleaned, errors='coerce').fillna(0).astype(int)
                # Số lượng
                if selected_cols.get("số lượng") is not None:
                    qty_series = df[selected_cols["số lượng"]]
                    qty_cleaned = pd.to_numeric(qty_series, errors='coerce').fillna(1).astype(int)
                    out_df["Số lượng"] = qty_cleaned
                else:
                    out_df["Số lượng"] = 1
                # Khối lượng (gram)
                if selected_cols.get("khối lượng (gram)") is not None:
                    wt_series = df[selected_cols["khối lượng (gram)"]]
                    wt_cleaned = pd.to_numeric(wt_series, errors='coerce').fillna(default_weight).astype(int)
                    out_df["Khối lượng (gram)"] = wt_cleaned
                else:
                    out_df["Khối lượng (gram)"] = int(default_weight) if default_weight is not None else 0
                # Ghi chú
                if selected_cols.get("ghi chú") is not None:
                    out_df["Ghi chú"] = df[selected_cols["ghi chú"]].astype(str).fillna("")
                else:
                    out_df["Ghi chú"] = ""
                # Mã đơn hàng
                if selected_cols.get("mã đơn hàng") is not None:
                    out_df["Mã đơn hàng"] = df[selected_cols["mã đơn hàng"]].astype(str).fillna("")
                else:
                    out_df["Mã đơn hàng"] = ""
                # Thêm kết quả của sheet vào danh sách chung
                combined_output.append(out_df)
                # Hiển thị xem trước 5 dòng đầu của kết quả chuẩn hóa
                st.write("Xem trước dữ liệu xuất (5 hàng đầu):")
                st.dataframe(out_df.head())
            # Nếu chưa map đủ, bỏ qua sheet này (đã hiển thị cảnh báo ở trên)

    # Sau khi xử lý tất cả file/sheet, nếu tất cả đều đã map xong:
    if combined_output and all_mapped:
        final_df = pd.concat(combined_output, ignore_index=True)
        st.subheader("Kết quả tổng hợp")
        st.dataframe(final_df)
        # Xuất file Excel chuẩn GHN
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False, sheet_name="GHN_Output")
        processed_data = output.getvalue()
        st.download_button(
            label="Tải xuống file GHN.xlsx",
            data=processed_data,
            file_name="GHN_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif not all_mapped:
        st.warning("Vui lòng chọn đầy đủ các trường bắt buộc trước khi tải xuống.")
