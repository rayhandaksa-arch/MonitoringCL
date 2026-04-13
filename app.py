import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="EBP Tracking System", layout="wide")

URL_GSHEET = "https://docs.google.com/spreadsheets/d/1NUIuYhkusKMvPhjhMb4QHPBrTgBpQytle3PJf4k7opY/edit"

# --- 2. FUNGSI KONEKSI (VERSI STABIL) ---
def get_gspread_client():
    # Mengambil kredensial dari secrets
    secret_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in secret_dict:
        secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_master_data():
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_url(URL_GSHEET)
        master_sheet = spreadsheet.worksheet("Master_Data")
        df_m = pd.DataFrame(master_sheet.get_all_records())
        
        # Cleaning
        df_m['Company'] = df_m['Company'].astype(str).str.strip()
        df_m['Brand'] = df_m['Brand'].astype(str).str.strip()
        return df_m
    except Exception as e:
        st.error(f"Gagal Load Master Data: {e}")
        return pd.DataFrame(columns=["Company", "Brand"])

# --- 3. LOGIKA FORM ---
st.title("📊 EBP & Brand Revenue Tracking")
df_master = load_master_data()

if df_master.empty:
    st.warning("⚠️ Data Master tidak ditemukan di Tab 'Master_Data'.")
    st.stop()

tab1, tab2 = st.tabs(["📝 Input Manual", "📤 Upload Bulk"])

with tab1:
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
        brand_name = st.selectbox("Brand Name", ["All"] + sorted([str(b) for b in filtered_brands]))
        
        brand_id = st.text_input("Brand Group Company ID")
        vendor_name = st.text_input("Vendor Name")
    with col3:
        vendor_id = st.text_input("Vendor ID")
        rev_type = st.selectbox("Ads Revenue", ["Percentage", "Fixed Value"])
        rev_val = st.number_input("Ads Revenue Value", value=0)
        percent = st.text_input("% (e.g. 4.0%)")
        multiplier = st.selectbox("Multiplier", ["GV", "Sell In", "Fixed"])
        claim_period = st.selectbox("Claim Period", ["Monthly", "Quarterly", "Yearly"])
        payment_method = st.selectbox("Method", ["Transfer", "Potong Tagihan"])
        link_cl = st.text_input("Link CL")
        catman = st.text_input("Catman Name")

    if st.button("🚀 Simpan ke Spreadsheet", use_container_width=True):
        if not id_val:
            st.error("ID wajib diisi!")
        else:
            new_row = [
                id_val, sub_date.strftime("%d %b %Y"), ads_type, 
                eff_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y"), 
                f"{ads_type} {selected_company}", selected_company, brand_id, brand_name, 
                "", vendor_name, vendor_id, "", "", rev_type, rev_val, 
                percent, multiplier, "", "", claim_period, payment_method, 
                "", link_cl, "", "", "", "", eff_date.strftime("%d %b %Y"), 
                end_date.strftime("%d %b %Y"), "", "", "", "FALSE", "", "", "", "", catman
            ]
            
            try:
                # Membuka koneksi baru saat tombol diklik (Menghindari Sesi Expired)
                client = get_gspread_client()
                sheet = client.open_by_url(URL_GSHEET).sheet1
                
                # Gunakan cara append yang paling mendasar
                sheet.append_row(new_row, value_input_option='USER_ENTERED')
                
                st.success("✅ Berhasil Disimpan!")
                st.balloons()
            except Exception as e:
                st.error(f"Gagal simpan: {e}")

with tab2:
    st.subheader("Upload CSV")
    uploaded_file = st.file_uploader("Pilih file CSV", type="csv")
    if uploaded_file and st.button("Proses CSV"):
        try:
            df_csv = pd.read_csv(uploaded_file).fillna("")
            client = get_gspread_client()
            sheet = client.open_by_url(URL_GSHEET).sheet1
            sheet.append_rows(df_csv.values.tolist(), value_input_option='USER_ENTERED')
            st.success("✅ Upload Berhasil!")
        except Exception as e:
            st.error(f"Gagal CSV: {e}")
