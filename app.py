import pandas as pd
import os
from tkinter import filedialog, Tk

def process_all_files(file_paths):
    all_data = []

    for file_path in file_paths:
        try:
            xls = pd.ExcelFile(file_path)
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                df.columns = df.columns.str.strip().str.lower()

                name_col = next((col for col in df.columns if "tên" in col), None)
                phone_col = next((col for col in df.columns if "điện thoại" in col or "sđt" in col), None)
                address_col = next((col for col in df.columns if "địa" in col), None)
                cod_col = next((col for col in df.columns if "thu hộ" in col or "cod" in col), None)
                weight_col = next((col for col in df.columns if "cân" in col), None)
                size_col = next((col for col in df.columns if "size" in col or "kích" in col), None)
                product_col = next((col for col in df.columns if "tên hàng" in col or "sản phẩm" in col), None)

                df["tên hàng đầy đủ"] = (
                    df.get(product_col).astype(str) + " Size " + df.get(size_col).astype(str)
                    if product_col and size_col else None
                )

                clean_df = pd.DataFrame({
                    "Tên": df.get(name_col),
                    "Số điện thoại": df.get(phone_col),
                    "Địa chỉ": df.get(address_col),
                    "Số tiền thu hộ": df.get(cod_col),
                    "Cân nặng": df.get(weight_col),
                    "Kích thước": df.get(size_col),
                    "Tên hàng": df["tên hàng đầy đủ"]
                })

                all_data.append(clean_df)
        except Exception as e:
            print(f"Lỗi xử lý file {file_path}: {e}")

    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_excel("ket_qua_gop.xlsx", index=False)
    print("✅ Đã xuất kết quả ra file ket_qua_gop.xlsx")

# Giao diện chọn file
Tk().withdraw()
filez = filedialog.askopenfilenames(title="Chọn nhiều file Excel", filetypes=[("Excel Files", "*.xlsx")])
process_all_files(filez)
