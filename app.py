import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="EBP Tracking System", layout="wide")

# URL Spreadsheet Anda
URL_GSHEET = "https://docs.google.com/spreadsheets/d/1NUIuYhkusKMvPhjhMb4QHPBrTgBpQytle3PJf4k7opY/edit"

# --- 2. FUNGSI LOAD DATA (DENGAN CACHING) ---
@st.cache_data(ttl=60)
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
        try:
            master_sheet = spreadsheet.worksheet("Master_Data")
            df_m = pd.DataFrame(master_sheet.get_all_records())
            df_m['Company'] = df_m['Company'].astype(str).str.strip()
            df_m['Brand'] = df_m['Brand'].astype(str).str.strip()
            df_m = df_m[df_m['Company'] != ""]
        except:
            df_m = pd.DataFrame(columns=["Company", "Brand"])
            
        return spreadsheet.sheet1, df_m
    except Exception as e:
        st.error(f"❌ Koneksi Gagal: {e}")
        return None, pd.DataFrame()

sheet_utama, df_master = load_all_data()

# --- 3. UI APLIKASI UTAMA ---
st.title("📊 EBP & Brand Revenue Tracking")

if df_master.empty:
    st.warning("⚠️ Data Master kosong atau tab 'Master_Data' tidak ditemukan.")
    st.stop()

tab1, tab2 = st.tabs(["📝 Input Manual", "📤 Upload Bulk (CSV)"])

with tab1:
    st.subheader("Form Input Category Manager")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        id_val = st.text_input("ID")
        sub_date = st.date_input("Submission Date", datetime.now())
        ads_type = st.selectbox("Ads Revenue Type", ["EBP", "Non-EBP", "Others"])
        eff_date = st.date_input("Effective Date")
        end_date = st.date_input("Ending Date")
        
    with col2:
        list_company = sorted(df_master["Company"].unique().tolist())
        selected_company = st.selectbox("Brand Group Company", list_company)
        
        filtered_brands = df_master[df_master["Company"] == selected_company]["Brand"].unique().tolist()
        brand_options = sorted([str(b) for b in filtered_brands])
        brand_name = st.selectbox("Brand Name", ["All"] + brand_options)
        
        brand_id = st.text_input("Brand Group Company ID")
        vendor_name = st.text_input("Vendor Name")

    with col3:
        vendor_id = st.text_input("Vendor ID")
        rev_type = st.selectbox("Ads Revenue", ["Percentage", "Fixed Value"])
        rev_val = st.number_input("Ads Revenue Value", value=0)
        percent = st.text_input("% (Contoh: 4.0%)")
        multiplier = st.selectbox("Multiplier", ["GV", "Sell In", "Fixed"])
        claim_period = st.selectbox("Claim Period", ["Monthly", "Quarterly", "Yearly"])
        payment_method = st.selectbox("Method", ["Transfer", "Potong Tagihan"])
        link_cl = st.text_input("Link CL")
        catman = st.text_input("Catman Name")

    if st.button("🚀 Simpan ke Spreadsheet", use_container_width=True):
        if not id_val:
            st.error("ID tidak boleh kosong!")
        else:
            sub_str = sub_date.strftime("%d %b %Y")
            eff_str = eff_date.strftime("%d %b %Y")
            end_str = end_date.strftime("%d %b %Y")

            new_row = [
                id_val, sub_str, ads_type, eff_str, end_str, 
                f"{ads_type} {selected_company}", selected_company, brand_id, brand_name, 
                "", vendor_name, vendor_id, "", "", rev_type, rev_val, 
                percent, multiplier, "", "", claim_period, payment_method, 
                "", link_cl, "", "", "", "", eff_str, end_str, 
                "", "", "", "FALSE", "", "", "", "", catman
            ]
            
            try:
                # Mencari baris kosong
                all_col_a = sheet_utama.col_values(1)
                next_row = len(all_col_a) + 1
                
                # PERBAIKAN ERROR: Menggunakan format update yang lebih stabil
                range_name = f"A{next_row}"
                
                # Menggunakan update tanpa argumen range_name eksplisit jika versi gspread terbaru
                sheet_utama.update([new_row], range_name, value_input_option='USER_ENTERED')
                
                st.success(f"✅ Berhasil disimpan di Baris {next_row}!")
                st.balloons()
            except Exception as err:
                # Jika masih error, gunakan alternatif method append_row yang lebih simpel
                try:
                    sheet_utama.append_row(new_row, value_input_option='USER_ENTERED')
                    st.success("✅ Berhasil disimpan menggunakan metode Append!")
                except Exception as e2:
                    st.error(f"Gagal simpan: {err}")

with tab2:
    st.subheader("Upload Bulk CSV")
    uploaded_file = st.file_uploader("Pilih file CSV", type="csv")
    if uploaded_file:
        df_csv = pd.read_csv(uploaded_file)
        if st.button("Konfirmasi Upload CSV"):
            try:
                data_list = df_csv.fillna("").values.tolist()
                # Gunakan append_rows untuk bulk upload agar lebih stabil
                sheet_utama.append_rows(data_list, value_input_option='USER_ENTERED')
                st.success(f"✅ Berhasil upload {len(data_list)} baris!")
            except Exception as err:
                st.error(f"Gagal upload: {err}")
