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
    # Mengonversi st.secrets menjadi dictionary murni untuk menghindari error <Response [200]>
    secret_dict = dict(st.secrets["gcp_service_account"])
    
    # Memperbaiki karakter newline pada private_key jika ada
    secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Masukkan URL Google Sheets kamu di sini
    url_gsheet = "https://docs.google.com/spreadsheets/d/1NUIuYhkusKMvPhjhMb4QHPBrTgBpQytle3PJf4k7opY/edit"
    sheet = client.open_by_url(url_gsheet).sheet1
    
except Exception as e:
    st.error(f"❌ Koneksi Gagal: {e}")
    st.info("Pastikan email service account sudah di-invite sebagai Editor di Spreadsheet.")
    st.stop()

# --- 2. UI APLIKASI UTAMA ---
st.title("📊 EBP & Brand Revenue Tracking")
st.caption("Mode Testing - Masukkan data untuk otomatis sinkron ke Google Sheets")

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
            brand_name = st.text_input("Brand Name (All / Specific)")
            vendor_name = st.text_input("Vendor Name")
            vendor_id = st.text_input("Vendor ID")
            rev_type = st.selectbox("Ads Revenue", ["Percentage", "Fixed Value"])
            rev_val = st.number_input("Ads Revenue Value (Fixed)", value=0)

        with col3:
            percent = st.text_input("% (Percentage only)", placeholder="e.g. 4.0%")
            multiplier = st.selectbox("Multiplier", ["GV", "Sell In", "Fixed"])
            claim_period = st.selectbox("Claim Period", ["Monthly", "Quarterly", "Yearly"])
            payment_method = st.selectbox("Method", ["Transfer", "Potong Tagihan"])
            link_cl = st.text_input("Link CL (signed MOU)")
            catman = st.text_input("Catman Name")

        submitted = st.form_submit_button("Simpan ke Spreadsheet")
        
        if submitted:
            # Konversi tanggal ke format string yang rapi
            sub_date_str = sub_date.strftime("%d %b %Y")
            eff_date_str = eff_date.strftime("%d %b %Y")
            end_date_str = end_date.strftime("%d %b %Y")

            # Susun data sesuai urutan kolom A sampai AM (40 Kolom)
            new_row = [
                id_val,          # A: ID
                sub_date_str,    # B: Submission Date
                ads_type,        # C: Ads Revenue Type
                eff_date_str,    # D: Effective Date
                end_date_str,    # E: Ending Date
                f"{ads_type} {brand_group} {eff_date_str}", # F: Details
                brand_group,     # G: Brand Group Company
                brand_id,        # H: Brand Group Company ID
                brand_name,      # I: Brand Name
                "",              # J: Brand Id
                vendor_name,     # K: Vendor Name
                vendor_id,       # L: Vendor ID
                "",              # M: Vendor Billing Name
                "",              # N: Vendor Billing Id
                rev_type,        # O: Ads Revenue
                rev_val,         # P: Ads Revenue Value
                percent,         # Q: %
                multiplier,      # R: Multiplier
                "",              # S: Max Claim
                "",              # T: Partnership Period
                claim_period,    # U: Claim Period
                payment_method,  # V: Method
                "",              # W: TOP
                link_cl,         # X: Link CL
                "",              # Y: Remarks
                "",              # Z: Target Q1
                "",              # AA: Target 2025
                "",              # AB: Brand Check
                eff_date_str,    # AC: Eff Date Claim
                end_date_str,    # AD: End Date Claim
                "",              # AE: Blank
                "",              # AF: Sub Month
                "",              # AG: Eff Month
                "FALSE",         # AH: Back Date
                "",              # AI: Unique Brand
                "",              # AJ: Month Group
                "",              # AK: Promo Funds
                "",              # AL: Invoice Scheme
                catman           # AM: Catman Name
            ]
            
            try:
                # 1. Cari baris kosong berikutnya
                # Kita ambil semua data di kolom A untuk menghitung jumlah baris yang terisi
                col_a_values = sheet.col_values(1)
                next_row = len(col_a_values) + 1
                
                # 2. Tentukan range yang akan diisi (A sampai AM adalah 39 kolom)
                # Kita akan mengisi mulai dari kolom A di baris 'next_row'
                range_to_update = f"A{next_row}"
                
                # 3. Masukkan data
                sheet.update(range_to_update, [new_row], value_input_option='USER_ENTERED')
                
                st.success(f"✅ Berhasil! Data {brand_group} masuk ke baris {next_row} mulai dari kolom A.")
            except Exception as err:
                st.error(f"Gagal simpan data: {err}")

with tab2:
    st.subheader("Upload CSV untuk Data Banyak")
    st.info("Gunakan fitur ini untuk upload banyak baris sekaligus. Pastikan urutan kolom di CSV sama dengan Spreadsheet.")
    uploaded_file = st.file_uploader("Pilih file CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Preview 5 Baris Teratas:")
        st.dataframe(df.head())
        
        if st.button("Konfirmasi Upload CSV"):
            try:
                data = df.fillna("").values.tolist()
                # Upload masal
                sheet.append_rows(data, value_input_option='USER_ENTERED')
                st.success(f"✅ Berhasil upload {len(data)} baris data!")
            except Exception as err:
                st.error(f"Gagal upload CSV: {err}")
