import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# Giả sử final_df là DataFrame đã được xử lý
final_df = ...  # Data bạn đã gộp
chunk_size = 300
today = datetime.today().strftime("%-d.%-m")
prefix = "GHN"
shop_name = "SHOP TUONG VY"

st.subheader("📁 Tải file đã tách (mỗi file 300 đơn)")

if len(final_df) > 300:
    for i in range(0, len(final_df), chunk_size):
        chunk = final_df.iloc[i:i+chunk_size]
        start = i + 1
        end = i + len(chunk)
        filename = f"{prefix}_{today}_{shop_name}_TOI {start}-{end}.xlsx"
        buffer = BytesIO()
        chunk.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            label=f"📥 Tải {filename}",
            data=buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
