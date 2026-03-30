import streamlit as st
import pandas as pd
import sqlite3
import os
import sys
import time

# Klasör yapısı fix'i (core modülüne erişim için)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tor_manager import TorManager
from core.discovery import DarkWebDiscovery
from core.scraper import DarkWebScraper
from core.database import DatabaseManager

st.set_page_config(page_title="DarkDrill Intelligence", layout="wide", page_icon="🕵️‍♂️")

DB_NAME = "darkweb_intel.db"
LOG_FILE = "activity.log"

if "tor_running" not in st.session_state:
    st.session_state.tor_running = False

def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def load_data(query):
    if not os.path.exists(DB_NAME): return pd.DataFrame()
    conn = get_db_connection()
    try:
        return pd.read_sql_query(query, conn)
    except: return pd.DataFrame()
    finally: conn.close()

def run_scan_from_ui(query):
    """Streamlit arayüzünden tarama akışını çalıştırır (CLI akışından bağımsız)."""
    tor = TorManager()
    db = DatabaseManager()
    discovery = DarkWebDiscovery()
    webhook_url = os.getenv("DARKDRILL_WEBHOOK_URL", "").strip() or None
    scraper = DarkWebScraper(webhook_url=webhook_url)

    with st.status("Tarama hazırlanıyor...", expanded=True) as status:
        # UI'da önceden başlatılmadıysa tarama öncesi otomatik Tor başlatmayı dener.
        if not st.session_state.tor_running:
            status.write("Tor servisi başlatılıyor, lütfen bekleyin...")
            if not tor.start_tor():
                status.update(label="Tarama başarısız", state="error", expanded=True)
                st.error("Tor başlatılamadı. Lütfen Tor kurulumunu/servisini kontrol edin.")
                return
            st.session_state.tor_running = True
        else:
            status.write("Tor zaten aktif, taramaya geçiliyor...")

        try:
            # Tor devrelerinin oturması için kullanıcıya bekleme bilgisini adım adım gösteriyoruz.
            for i in range(15, 0, -1):
                st.info(f"Tor ağı hazırlanıyor... yaklaşık {i} sn kaldı")
                time.sleep(1)

            status.write("Hedefler Ahmia üzerinde aranıyor...")
            links = discovery.search_ahmia(query)

            if not links:
                status.update(label="Tarama tamamlandı", state="complete", expanded=True)
                st.warning("Hedef bulunamadı. Farklı bir anahtar kelime deneyin.")
                return

            total_links = len(links)
            status.write(f"{total_links} hedef bulundu, tarama başlatılıyor...")

            progress = st.progress(0, text="Tarama başlıyor...")
            saved_total = 0

            # Her hedefte progress bar güncellenir; kullanıcı canlı olarak ilerlemeyi görür.
            for idx, url in enumerate(links, start=1):
                with st.spinner(f"[{idx}/{total_links}] Hedef kontrol ediliyor: {url}"):
                    if scraper.check_health(url):
                        findings = scraper.scrape_and_parse(url)
                        if findings:
                            site_id = db.save_site(url, "UP")
                            new_count = db.save_findings(site_id, findings)
                            saved_total += new_count
                            status.write(f"{url} tarandı, {new_count} yeni bulgu kaydedildi")
                        else:
                            db.save_site(url, "UP")
                            status.write(f"{url} tarandı, kayda değer bulgu çıkmadı")
                    else:
                        db.save_site(url, "DOWN")
                        status.write(f"{url} erişilemedi, hedef atlandı")

                progress_value = int((idx / total_links) * 100)
                progress.progress(progress_value, text=f"İlerleme: {idx}/{total_links} hedef tarandı")

            status.update(label="Tarama tamamlandı", state="complete", expanded=False)
            st.success(f"Tarama başarıyla tamamlandı. Toplam {saved_total} yeni bulgu kaydedildi.")

            # Yeni verilerin anlık tablolar üzerinde görünmesi için sayfa yenilenir.
            st.rerun()
        finally:
            # Tor servisini burada otomatik kapatmıyoruz; kullanıcı UI'dan manuel yönetir.
            pass

# --- ARAYÜZ ---
st.title("🌐 DarkDrill Intelligence Framework")

# Yeni tarama başlatma bölümü (hibrit çalışma için GUI tetikleyici)
st.sidebar.markdown("---")
st.sidebar.subheader("🧅 Tor Servisi")
tor_col1, tor_col2 = st.sidebar.columns(2)
with tor_col1:
    if st.button("Tor Başlat", key="btn_tor_start"):
        tor = TorManager()
        if tor.start_tor():
            st.session_state.tor_running = True
            st.sidebar.success("Tor servisi başlatıldı.")
        else:
            st.sidebar.error("Tor başlatılamadı.")
with tor_col2:
    if st.button("Tor Durdur", key="btn_tor_stop"):
        tor = TorManager()
        tor.stop_tor()
        st.session_state.tor_running = False
        st.sidebar.info("Tor durdurma komutu gönderildi.")

st.sidebar.caption(f"Tor Durumu: {'Aktif' if st.session_state.tor_running else 'Pasif'}")

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Yeni Tarama Başlat")
with st.sidebar.form("scan_form"):
    scan_query = st.text_input(
        "Anahtar kelime",
        placeholder="Örn: database leak, combo list, admin, sql dump"
    )
    start_scan = st.form_submit_button("Taramayı Başlat")

if start_scan:
    if not scan_query.strip():
        st.warning("Lütfen geçerli bir anahtar kelime girin.")
    else:
        run_scan_from_ui(scan_query.strip())

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
            # Tabloyu ekran genişliğine yayarak daha okunur hale getirir.
            st.dataframe(df, width="stretch", hide_index=True)

            # Export için tüm leaks kayıtlarını ayrı sorgu ile alıyoruz.
            export_df = load_data("SELECT id, site_id, type, content, discovery_date FROM leaks ORDER BY id DESC")
            if not export_df.empty:
                csv_bytes = export_df.to_csv(index=False).encode("utf-8")
                json_bytes = export_df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")

                ex_col1, ex_col2 = st.columns(2)
                with ex_col1:
                    st.download_button(
                        label="⬇️ leaks.csv indir",
                        data=csv_bytes,
                        file_name="leaks_export.csv",
                        mime="text/csv",
                        key="download_leaks_csv"
                    )
                with ex_col2:
                    st.download_button(
                        label="⬇️ leaks.json indir",
                        data=json_bytes,
                        file_name="leaks_export.json",
                        mime="application/json",
                        key="download_leaks_json"
                    )
            else:
                st.info("Dışa aktarım için leaks tablosunda kayıt bulunamadı.")

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