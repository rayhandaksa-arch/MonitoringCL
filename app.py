import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="EBP Tracking System", layout="wide")

# --- 1. KONEKSI GOOGLE SHEETS ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    secret_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in secret_dict:
        secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    url_gsheet = "https://docs.google.com/spreadsheets/d/1NUIuYhkusKMvPhjhMb4QHPBrTgBpQytle3PJf4k7opY/edit"
    sheet = client.open_by_url(url_gsheet).sheet1
    
except Exception as e:
    st.error(f"❌ Koneksi Gagal: {e}")
    st.stop()

# --- 2. UI APLIKASI UTAMA ---
st.title("📊 EBP & Brand Revenue Tracking")

tab1, tab2 = st.tabs(["📝 Input Manual", "📤 Upload Bulk (CSV)"])

with tab1:
    st.subheader("Form Input Category Manager")
    with st.form("input_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_val = st.text_input("ID")
            sub_date = st.date_input("Submission Date", datetime.now())
            ads_type = st.selectbox("Ads Revenue Type", ["EBP", "Non-EBP", "Others"])
            eff_date = st.date_input("Effective Date")
            end_date = st.date_input("Ending Date")
            brand_group = st.text_input("Brand Group Company")
        with col2:
            brand_id = st.text_input("Brand Group Company ID")
            brand_name = st.text_input("Brand Name")
            vendor_name = st.text_input("Vendor Name")
            vendor_id = st.text_input("Vendor ID")
            rev_type = st.selectbox("Ads Revenue", ["Percentage", "Fixed Value"])
            rev_val = st.number_input("Ads Revenue Value", value=0)
        with col3:
            percent = st.text_input("% (e.g. 4.0%)")
            multiplier = st.selectbox("Multiplier", ["GV", "Sell In", "Fixed"])
            claim_period = st.selectbox("Claim Period", ["Monthly", "Quarterly", "Yearly"])
            payment_method = st.selectbox("Method", ["Transfer", "Potong Tagihan"])
            link_cl = st.text_input("Link CL")
            catman = st.text_input("Catman Name")

        submitted = st.form_submit_button("Simpan ke Spreadsheet")
        
        if submitted:
            sub_date_str = sub_date.strftime("%d %b %Y")
            eff_date_str = eff_date.strftime("%d %b %Y")
            end_date_str = end_date.strftime("%d %b %Y")

            new_row = [
                id_val, sub_date_str, ads_type, eff_date_str, end_date_str, 
                f"{ads_type} {brand_group}", brand_group, brand_id, brand_name, 
                "", vendor_name, vendor_id, "", "", rev_type, rev_val, 
                percent, multiplier, "", "", claim_period, payment_method, 
                "", link_cl, "", "", "", "", "", "", "", "", "", "FALSE", "", "", "", "", catman
            ]
            
            try:
                # CEK LIMIT BARIS
                all_col_a = sheet.col_values(1)
                next_row = len(all_col_a) + 1
                
                # Jika baris yang akan diisi melebihi kapasitas sheet, tambah 10 baris
                if next_row > sheet.row_count:
                    sheet.add_rows(10)
                
                range_target = f"A{next_row}"
                sheet.update(range_target, [new_row], value_input_option='USER_ENTERED')
                st.success(f"✅ Berhasil! Data masuk ke Baris {next_row}")
            except Exception as err:
                st.error(f"Gagal simpan data: {err}")

with tab2:
    st.subheader("Upload Bulk CSV")
    uploaded_file = st.file_uploader("Pilih file CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if st.button("Proses Upload CSV"):
            try:
                data_list = df.fillna("").values.tolist()
                all_col_a = sheet.col_values(1)
                next_row = len(all_col_a) + 1
                
                # Tambah baris sesuai jumlah data CSV jika kurang
                needed_rows = (next_row + len(data_list)) - sheet.row_count
                if needed_rows > 0:
                    sheet.add_rows(needed_rows)

                sheet.update(f"A{next_row}", data_list, value_input_option='USER_ENTERED')
                st.success(f"✅ {len(data_list)} baris berhasil ditambahkan!")
            except Exception as err:
                st.error(f"Gagal upload CSV: {err}")
