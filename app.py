import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="EBP Tracking System", layout="wide")

# --- 1. KONEKSI GOOGLE SHEETS ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_data(ttl=600)  # Cache selama 10 menit agar tidak berat loadingnya
def load_master_data():
    try:
        secret_dict = dict(st.secrets["gcp_service_account"])
        secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Ambil data dari sheet Master_Data
        # Pastikan Anda punya sheet bernama "Master_Data"
        master_sheet = client.open_by_url(url_gsheet).worksheet("Master_Data")
        data = master_sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        # Jika sheet Master_Data belum ada, beri data dummy untuk testing
        return pd.DataFrame({
            "Company": ["Unilever", "Unilever", "P&G", "P&G"],
            "Brand": ["Pepsodent", "Dove", "Pantene", "Gillette"]
        })

try:
    secret_dict = dict(st.secrets["gcp_service_account"])
    secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    url_gsheet = "https://docs.google.com/spreadsheets/d/1NUIuYhkusKMvPhjhMb4QHPBrTgBpQytle3PJf4k7opY/edit"
    sheet = client.open_by_url(url_gsheet).sheet1
    
    # Load data Brand & Company
    df_master = load_master_data()
    
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
            
            # --- FITUR DEPENDENT DROPDOWN ---
            # 1. Pilih Company
            list_company = sorted(df_master["Company"].unique().tolist())
            selected_company = st.selectbox("Brand Group Company", list_company)
            
        with col2:
            # 2. Filter Brand berdasarkan Company yang dipilih
            filtered_brands = df_master[df_master["Company"] == selected_company]["Brand"].unique().tolist()
            brand_name = st.selectbox("Brand Name", ["All"] + sorted(filtered_brands))
            
            brand_id = st.text_input("Brand Group Company ID")
            vendor_name = st.text_input("Vendor Name")
            vendor_id = st.text_input("Vendor ID")
            rev_type = st.selectbox("Ads Revenue", ["Percentage", "Fixed Value"])

        with col3:
            rev_val = st.number_input("Ads Revenue Value", value=0)
            percent = st.text_input("% (e.g. 4.0%)")
            multiplier = st.selectbox("Multiplier", ["GV", "Sell In", "Fixed"])
            claim_period = st.selectbox("Claim Period", ["Monthly", "Quarterly", "Yearly"])
            payment_method = st.selectbox("Method", ["Transfer", "Potong Tagihan"])
            link_cl = st.text_input("Link CL")
            catman = st.text_input("Catman Name")

        submitted = st.form_submit_button("Simpan ke Spreadsheet")
        
        if submitted:
            # (Logika simpan data sama seperti sebelumnya menggunakan sheet.update)
            # ... simpan data ...
            st.success("Data Tersimpan!")
