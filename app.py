import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="EBP Tracking System", layout="wide")

# URL Spreadsheet Anda
URL_GSHEET = "https://docs.google.com/spreadsheets/d/1NUIuYhkusKMvPhjhMb4QHPBrTgBpQytle3PJf4k7opY/edit"

# --- 1. FUNGSI LOAD DATA ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        secret_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in secret_dict:
            secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url(URL_GSHEET)
        
        # Load Master Data
        master_sheet = spreadsheet.worksheet("Master_Data")
        df_master = pd.DataFrame(master_sheet.get_all_records())
        
        # --- CLEANING DATA ---
        # Pastikan kolom Company dan Brand tidak ada yang kosong dan semuanya teks
        df_master = df_master.dropna(subset=['Company', 'Brand'])
        df_master['Company'] = df_master['Company'].astype(str)
        df_master['Brand'] = df_master['Brand'].astype(str)
        
        return spreadsheet.sheet1, df_master
    except Exception as e:
        st.error(f"❌ Error Detail: {e}")
        return None, pd.DataFrame(columns=["Company", "Brand"])

# Jalankan fungsi load
sheet, df_master = load_all_data()

# --- 2. UI APLIKASI ---
st.title("📊 EBP & Brand Revenue Tracking")

if df_master.empty:
    st.error("⚠️ Data Master tidak terbaca. Pastikan Tab 'Master_Data' ada dan kolom 'Company' & 'Brand' terisi.")
    st.stop()

tab1, tab2 = st.tabs(["📝 Input Manual", "📤 Upload Bulk (CSV)"])

with tab1:
    st.subheader("Form Input Category Manager")
    
    # Inisialisasi variabel di luar form agar tidak error jika form gagal render
    with st.form("input_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            id_val = st.text_input("ID")
            sub_date = st.date_input("Submission Date", datetime.now())
            ads_type = st.selectbox("Ads Revenue Type", ["EBP", "Non-EBP", "Others"])
            eff_date = st.date_input("Effective Date")
            end_date = st.date_input("Ending Date")
            
        with col2:
            # Dropdown Company (Sudah di-fix agar tidak error sorted)
            list_company = sorted(df_master["Company"].unique().tolist())
            selected_company = st.selectbox("Brand Group Company", list_company)
            
            # Filter Brand berdasarkan Company
            filtered_brands = df_master[df_master["Company"] == selected_company]["Brand"].unique().tolist()
            brand_name = st.selectbox("Brand Name", ["All"] + sorted(filtered_brands))
            
            brand_id = st.text_input("Brand Group Company ID")
            vendor_name = st.text_input("Vendor Name")
            vendor_id = st.text_input("Vendor ID")

        with col3:
            rev_type = st.selectbox("Ads Revenue", ["Percentage", "Fixed Value"])
            rev_val = st.number_input("Ads Revenue Value (Fixed)", value=0)
            percent = st.text_input("% (e.g. 4.0%)")
            multiplier = st.selectbox("Multiplier", ["GV", "Sell In", "Fixed"])
            claim_period = st.selectbox("Claim Period", ["Monthly", "Quarterly", "Yearly"])
            payment_method = st.selectbox("Method", ["Transfer", "Potong Tagihan"])
            link_cl = st.text_input("Link CL")
            catman = st.text_input("Catman Name")

        # Tombol Submit harus berada di dalam blok 'with st.form'
        submitted = st.form_submit_button("Simpan ke Spreadsheet")
        
        if submitted:
            sub_date_str = sub_date.strftime("%d %b %Y")
            eff_date_str = eff_date.strftime("%d %b %Y")
            end_date_str = end_date.strftime("%d %b %Y")

            new_row = [
                id_val, sub_date_str, ads_type, eff_date_str, end_date_str, 
                f"{ads_type} {selected_company}", selected_company, brand_id, brand_name, 
                "", vendor_name, vendor_id, "", "", rev_type, rev_val, 
                percent, multiplier, "", "", claim_period, payment_method, 
                "", link_cl, "", "", "", "", eff_date_str, end_date_str, 
                "", "", "", "FALSE", "", "", "", "", catman
            ]
            
            try:
                # Pastikan sheet ditemukan
                if sheet:
                    all_col_a = sheet.col_values(1)
                    next_row = len(all_col_a) + 1
                    
                    if next_row > sheet.row_count:
                        sheet.add_rows(10)
                        
                    sheet.update(range_name=f"A{next_row}", values=[new_row], value_input_option='USER_ENTERED')
                    st.success(f"✅ Berhasil! Data masuk ke Baris {next_row}")
                else:
                    st.error("Koneksi ke Sheet utama hilang.")
            except Exception as err:
                st.error(f"Gagal simpan: {err}")

with tab2:
    st.subheader("Upload Bulk CSV")
    # ... (bagian CSV sama seperti sebelumnya)
    st.write("Fitur CSV aktif.")
