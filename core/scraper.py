import requests
import re
import random
import time
from bs4 import BeautifulSoup
from core.logger import setup_custom_logger

# Logger kurulumu
logger = setup_custom_logger(__name__)

class DarkWebScraper:
    def __init__(self, tor_proxy="socks5h://127.0.0.1:9050", webhook_url=None, request_timeout=(12, 35), delay_range=(1.2, 4.0)):
        self.session = requests.Session()
        # DNS sızıntısını önlemek için socks5h protokolü kullanılır
        self.session.proxies = {
            'http': tor_proxy,
            'https': tor_proxy
        }

        # Bot tespitini zorlaştırmak için gerçekçi User-Agent havuzu.
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ]
        self.request_timeout = request_timeout
        self.delay_range = delay_range
        self.webhook_url = webhook_url
        self.alert_keywords = ["api_key"]
        
        # Sızdırılmış veri formatları için Regex tanımları
        self.patterns = {
            'emails': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'creds': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:[^\s]+',
            'hashes': r'\b[a-fA-F0-9]{32}\b',  # MD5 hash örneği
            # Base58 doğrulama: 1/3 ile başlar, I/O/l/0 içermez, tipik 26-35 uzunluk.
            'btc_wallet': r'\b(?:bc1[ac-hj-np-z02-9]{25,62}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b',
            # 0x + 40 hex karakter.
            'eth_wallet': r'\b0x[a-fA-F0-9]{40}\b',
            # AWS, Stripe, GitHub token, OpenAI key ve genel yüksek-entropy key desenleri.
            'api_key': (
                r'\b(?:'
                r'AKIA[0-9A-Z]{16}'
                r'|sk_live_[0-9a-zA-Z]{24,}'
                r'|ghp_[0-9A-Za-z]{36}'
                r'|sk-[A-Za-z0-9]{20,}'
                r'|AIza[0-9A-Za-z\-_]{35}'
                r'|(?:(?:api|secret|access|private)[_-]?key)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{20,}["\']?'
                r')\b'
            )
        }

    def _randomized_headers(self):
        """Her istek için rastgele ama tutarlı görünen header seti üretir."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "DNT": "1",
        }

    def _human_delay(self):
        """Sabit aralık yerine jitter ile bekleme yaparak istek kalıbını doğal gösterir."""
        time.sleep(random.uniform(*self.delay_range))

    def _send_webhook_alert(self, url, finding_type, value):
        """Yüksek değerli bulgu tespit edildiğinde opsiyonel webhook bildirimi gönderir."""
        if not self.webhook_url:
            return

        payload = {
            "text": f"[DarkDrill Alert] type={finding_type} target={url} value={value[:120]}"
        }

        try:
            requests.post(self.webhook_url, json=payload, timeout=8)
        except requests.RequestException as exc:
            logger.warning(f"Webhook gönderimi başarısız: {exc}")

    def _trigger_alerts(self, url, findings):
        for finding_type in self.alert_keywords:
            for value in findings.get(finding_type, []):
                self._send_webhook_alert(url, finding_type, value)

    def check_health(self, url):
        """Sitenin erişilebilir olup olmadığını kontrol eder."""
        try:
            self._human_delay()
            # Sadece header çekerek bant genişliği tasarrufu sağlarız
            response = self.session.get(
                url,
                timeout=self.request_timeout,
                stream=True,
                headers=self._randomized_headers()
            )
            is_up = response.status_code == 200
            if is_up:
                logger.info(f"Site canlı: {url}")
            else:
                logger.warning(f"Site yanıt vermiyor (HTTP {response.status_code}): {url}")
            response.close()
            return is_up
        except requests.RequestException as e:
            logger.error(f"Bağlantı başarısız: {url} - Hata: {str(e)}")
            return False

    def scrape_and_parse(self, url):
        """Sitedeki verileri indirir ve Regex ile ayıklar."""
        logger.info(f"Veri ayıklama işlemi başlatıldı: {url}")
        try:
            self._human_delay()
            response = self.session.get(
                url,
                timeout=self.request_timeout,
                headers=self._randomized_headers()
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # HTML etiketlerini temizleyip saf metne odaklanalım
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()
            
            clean_text = soup.get_text(separator=' ')
            
            findings = {
                'emails': list(set(re.findall(self.patterns['emails'], clean_text))),
                'creds': list(set(re.findall(self.patterns['creds'], clean_text))),
                'hashes': list(set(re.findall(self.patterns['hashes'], clean_text))),
                'btc_wallet': list(set(re.findall(self.patterns['btc_wallet'], clean_text))),
                'eth_wallet': list(set(re.findall(self.patterns['eth_wallet'], clean_text))),
                'api_key': list(set(re.findall(self.patterns['api_key'], clean_text)))
            }

            self._trigger_alerts(url, findings)
            
            found_count = sum(len(v) for v in findings.values())
            logger.info(f"Tarama tamamlandı: {url}. Toplam {found_count} bulgu elde edildi.")
            return findings
            
        except requests.RequestException as e:
            logger.error(f"Veri çekme sırasında hata: {url} - Hata: {str(e)}")
            return None