import streamlit as st
import pandas as pd
import sqlite3
import os
import sys

# Klasör yapısı fix'i (core modülüne erişim için)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="DarkDrill Intelligence", layout="wide", page_icon="🕵️‍♂️")

DB_NAME = "darkweb_intel.db"
LOG_FILE = "activity.log"

def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def load_data(query):
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = get_db_connection()
    try:
        return pd.read_sql_query(query, conn)
    except: return pd.DataFrame()
    finally: conn.close()

# --- ARAYÜZ ---
st.title("🌐 DarkDrill Intelligence Framework")

# Sekme Yapısı
tab_main, tab_logs = st.tabs(["📊 Analiz Paneli", "📜 Sistem Logları"])

with tab_main:
    if not os.path.exists(DB_NAME):
        st.error("⚠️ Veritabanı bulunamadı! Lütfen önce bir tarama başlatın.")
    else:
        # Metrikler
        col1, col2, col3 = st.columns(3)
        stats = load_data("SELECT (SELECT COUNT(*) FROM sites) as s, (SELECT COUNT(*) FROM leaks) as l")
        
        col1.metric("Toplam Hedef", stats['s'][0] if not stats.empty else 0)
        col2.metric("Tespit Edilen Sızıntı", stats['l'][0] if not stats.empty else 0)
        col3.metric("Durum", "Aktif", delta="Tor Bağlı")

        st.markdown("---")

        # Veri Tabloları
        l_col, r_col = st.columns([2, 1])
        with l_col:
            st.subheader("🚨 Son Tespitler")
            df = load_data("SELECT discovery_date as 'Tarih', type as 'Tip', content as 'Veri' FROM leaks ORDER BY id DESC LIMIT 15")
            # YENİ: width='stretch' kullanımı (Deprecation Fix)
            st.dataframe(df, width="stretch", hide_index=True)

        with r_col:
            st.subheader("📊 Dağılım")
            dist = load_data("SELECT type, COUNT(*) as c FROM leaks GROUP BY type")
            if not dist.empty:
                st.bar_chart(dist.set_index('type'))

with tab_logs:
    st.subheader("⚙️ Sistem Çalışma Kayıtları (activity.log)")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            # Logları sondan başa doğru göster (En güncel en üstte)
            logs = f.readlines()
            st.code("".join(logs[-50:]), language="log") # Son 50 satır
            
        if st.button("Logları Temizle"):
            open(LOG_FILE, 'w').close()
            st.rerun()
    else:
        st.info("Henüz log kaydı oluşturulmadı.")

# --- SIDEBAR ---
st.sidebar.image("https://img.icons8.com/neon/96/spy.png", width=80)
st.sidebar.title("Operasyon Yönetimi")
if st.sidebar.button("♻️ Verileri Yenile"):
    st.rerun()