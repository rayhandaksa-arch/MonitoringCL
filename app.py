import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="EBP Tracking System - Testing Mode", layout="wide")

# --- 1. KONEKSI GOOGLE SHEETS ---
# Pastikan nama di st.secrets sesuai dengan di file secrets.toml atau Settings Streamlit Cloud
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    # Mengambil kredensial dari secrets
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client = gspread.authorize(creds)
    
    # GANTI: Pastikan nama file Google Sheets kamu sama persis
    # Jika menggunakan nama di secrets.toml kamu: "DataStreamlit"
    sheet = client.open("DataStreamlit").sheet1 
except Exception as e:
    st.error(f"❌ Koneksi Gagal: {e}")
    st.info("Pastikan email service account sudah di-invite sebagai Editor di Google Sheets.")
    st.stop()

# --- 2. UI APLIKASI UTAMA ---
st.title("📊 EBP & Brand Revenue Tracking (Testing Mode)")
st.caption("Akses Publik Aktif - Fitur Login Dinonaktifkan")

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
            # List 40 kolom (sesuaikan dengan urutan kolom di Google Sheets kamu)
            new_row = [
                id_val, str(sub_date), ads_type, str(eff_date), str(end_date), 
                f"{ads_type} {brand_group}", brand_group, brand_id, brand_name, 
                "", vendor_name, vendor_id, "", "", rev_type, rev_val, 
                percent, multiplier, "", "", claim_period, payment_method, 
                "", link_cl, "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", catman
            ]
            
            try:
                sheet.append_row(new_row)
                st.success(f"✅ Data untuk {brand_group} berhasil disimpan!")
            except Exception as err:
                st.error(f"Gagal simpan data: {err}")

with tab2:
    st.subheader("Upload CSV untuk Data Banyak")
    st.info("Pastikan urutan kolom di file CSV sama dengan urutan kolom di Google Sheets.")
    uploaded_file = st.file_uploader("Upload file CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Preview Data (5 baris pertama):")
        st.dataframe(df.head())
        
        if st.button("Konfirmasi Upload Semua"):
            try:
                data = df.fillna("").values.tolist()
                sheet.append_rows(data)
                st.success(f"✅ {len(data)} Baris berhasil ditambahkan!")
            except Exception as err:
                st.error(f"Gagal upload CSV: {err}")