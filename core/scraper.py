import requests
import re
from bs4 import BeautifulSoup
from core.logger import setup_custom_logger

# Logger kurulumu
logger = setup_custom_logger(__name__)

class DarkWebScraper:
    def __init__(self, tor_proxy="socks5h://127.0.0.1:9050"):
        self.session = requests.Session()
        # DNS sızıntısını önlemek için socks5h protokolü kullanılır
        self.session.proxies = {
            'http': tor_proxy,
            'https': tor_proxy
        }
        
        # Sızdırılmış veri formatları için Regex tanımları
        self.patterns = {
            'emails': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'creds': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:[^\s]+',
            'hashes': r'\b[a-fA-F0-9]{32}\b' # MD5 hash örneği
        }

    def check_health(self, url):
        """Sitenin erişilebilir olup olmadığını kontrol eder."""
        try:
            # Sadece header çekerek bant genişliği tasarrufu sağlarız
            response = self.session.get(url, timeout=20, stream=True)
            is_up = response.status_code == 200
            if is_up:
                logger.info(f"Site canlı: {url}")
            else:
                logger.warning(f"Site yanıt vermiyor (HTTP {response.status_code}): {url}")
            return is_up
        except Exception as e:
            logger.error(f"Bağlantı başarısız: {url} - Hata: {str(e)}")
            return False

    def scrape_and_parse(self, url):
        """Sitedeki verileri indirir ve Regex ile ayıklar."""
        logger.info(f"Veri ayıklama işlemi başlatıldı: {url}")
        try:
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # HTML etiketlerini temizleyip saf metne odaklanalım
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()
            
            clean_text = soup.get_text(separator=' ')
            
            findings = {
                'emails': list(set(re.findall(self.patterns['emails'], clean_text))),
                'creds': list(set(re.findall(self.patterns['creds'], clean_text))),
                'hashes': list(set(re.findall(self.patterns['hashes'], clean_text)))
            }
            
            found_count = sum(len(v) for v in findings.values())
            logger.info(f"Tarama tamamlandı: {url}. Toplam {found_count} bulgu elde edildi.")
            return findings
            
        except Exception as e:
            logger.error(f"Veri çekme sırasında hata: {url} - Hata: {str(e)}")
            return None