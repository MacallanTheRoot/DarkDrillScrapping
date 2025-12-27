import signal
import sys
import time # Bekleme için eklendi
from core.tor_manager import TorManager
from core.discovery import DarkWebDiscovery
from core.scraper import DarkWebScraper
from core.database import DatabaseManager

def main():
    tor = TorManager()
    db = DatabaseManager()
    discovery = DarkWebDiscovery()
    scraper = DarkWebScraper()

    # Ctrl+C yakalama
    signal.signal(signal.SIGINT, lambda s, f: (tor.stop_tor(), sys.exit(0)))

    if not tor.start_tor():
        return

    # Tor'un devreleri (circuits) kurması için kısa bir bekleme
    print("[*] Tor ağının hazır olması bekleniyor (15 sn)...")
    time.sleep(15)

    print("\n--- Dark Drill Intelligence Tool Başlatıldı ---")
    
    # İSTEDİĞİN GÜNCELLEME: Örneklerle arama sorgusu
    query = input("[?] Aramak istediğiniz anahtar kelime (Örnek: database leak, combo list, admin, sql dump): ")
    
    if not query.strip():
        print("[!] Boş bir sorgu girdiniz, çıkılıyor.")
        return

    # 1. Keşif Aşaması
    links = discovery.search_ahmia(query)
    
    if not links:
        print("[!] Potansiyel hedef bulunamadı. Tor bağlantısını kontrol edin veya başka bir kelime deneyin.")
    else:
        print(f"[+] {len(links)} adet potansiyel hedef bulundu.")

        # 2. Tarama ve Kaydetme Aşaması
        for url in links:
            if scraper.check_health(url):
                findings = scraper.scrape_and_parse(url)
                if findings:
                    site_id = db.save_site(url, "UP")
                    count = db.save_findings(site_id, findings)
                    print(f"   [OK] {url} -> {count} yeni bulgu kaydedildi.")
            else:
                db.save_site(url, "DOWN")
                print(f"   [!] {url} erişilemez, atlanıyor.")

    print("\n[+] Operasyon tamamlandı. Dashboard üzerinden verileri inceleyebilirsiniz.")
    
    # Dashboard'u açık tutmak için programı kapatmıyoruz, manuel çıkış bekleniyor
    print("[*] Kapatmak için Ctrl+C tuşlarına basın.")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
