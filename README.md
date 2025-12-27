# DarkDrillScrapping

DarkDrillScrapping, Tor ağı üzerinden `.onion` sitelerde sızıntı (e-posta, kimlik bilgisi kombinasyonları, hash) araması yapan, bulguları SQLite veritabanına kaydeden ve Streamlit tabanlı bir dashboard ile görselleştiren hafif bir istihbarat aracıdır.

## Özellikler
- Tor proxy (`socks5h://127.0.0.1:9050`) üzerinden güvenli istekler
- Ahmia arama motoru ile `.onion` keşfi
- `BeautifulSoup` ile HTML’den metin ayıklama ve Regex ile veri çıkarımı
- SQLite veritabanına kalıcı kayıt (tekillik kısıtlarıyla yinelenen kayıtlara önlem)
- Streamlit dashboard ile metrikler, akış ve dağılım grafikleri

## Gereksinimler
- Linux (Tor servis entegrasyonu nedeniyle önerilir)
- Tor kurulu ve servis olarak çalıştırılabilir olmalı (`sudo service tor start`)
- Python 3.10+ (önerilir)

Python bağımlılıkları `requirements.txt` içinde listelenmiştir:
- requests[socks]
- beautifulsoup4
- streamlit
- pandas
- pysocks (requests'in socks desteği için güvence amaçlı)

## Kurulum
1) Sanal ortam (önerilir):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Bağımlılıkları kurun:
```bash
pip install -r requirements.txt
```

3) Tor servisinizin çalıştığını doğrulayın:
```bash
sudo service tor start
pgrep -x tor && echo "Tor aktif" || echo "Tor bulunamadı"
```

## Çalıştırma
1) Keşif ve tarama (veritabanını oluşturur ve doldurur):
```bash
python main.py
```
Komut sırasında bir anahtar kelime girin (ör. "database leak", "combo list", "admin"). Araç Ahmia üzerinden `.onion` linkleri keşfeder, her birinin sağlık durumunu kontrol eder ve içerikten e-posta/credential/hash bulgularını çıkararak SQLite veritabanına kaydeder.

2) Dashboard (Streamlit arayüzü):
```bash
streamlit run ui/dashboard.py
```
Dashboard, aynı dizindeki `darkweb_intel.db` dosyasını kullanır ve:
- Toplam keşfedilen onion sayısı
- Aktif hedefler
- Toplam sızıntı
- Son sızıntı akışı tablosu
- Sızıntı türü dağılım grafiği
- Site durumları tablosu
gibi görseller sunar.

## Yapı ve Akış
- [core/tor_manager.py](core/tor_manager.py): Tor servis kontrolü (başlat/durdur)
- [core/discovery.py](core/discovery.py): Ahmia üzerinden `.onion` keşfi
- [core/scraper.py](core/scraper.py): İçerik çekme, HTML temizleme ve Regex ile bulgu çıkarımı
- [core/database.py](core/database.py): SQLite şema kurulumu ve bulguların kaydı
- [ui/dashboard.py](ui/dashboard.py): Streamlit arayüzü
- [main.py](main.py): Uçtan uca orkestrasyon

## Konfigürasyon
- Tor proxy adresi varsayılan olarak `socks5h://127.0.0.1:9050` kullanılır. Gerekirse [core/scraper.py](core/scraper.py#L8) içindeki `tor_proxy` parametresini değiştirin.
- Dashboard `darkweb_intel.db` dosyasını proje kökünde bekler. Farklı konum kullanmak istiyorsanız [ui/dashboard.py](ui/dashboard.py#L9) içindeki `DB_NAME` değerini güncelleyin.

## Güvenlik ve Yasal Uyarı
Bu araç yalnızca eğitim ve siber güvenlik araştırmaları için tasarlanmıştır. `.onion` sitelere erişim, bulunduğunuz ülkenin yasalarına ve kurum politikalarına tabi olabilir. Eriştirdiğiniz içeriklerden doğabilecek sonuçlardan kullanıcı sorumludur.

## Sorun Giderme
- Tor çalışmıyor: `sudo service tor start` ile başlatın ve `pgrep -x tor` ile doğrulayın.
- Bağlantı hataları: Proxy adresini ve ağ çıkışınızı kontrol edin.
- Boş veriler: Anahtar kelimeyi değiştirin veya daha genel bir arama yapın.

## Lisans
Bu repo kökünde yer alan lisans dosyasına bakınız.
