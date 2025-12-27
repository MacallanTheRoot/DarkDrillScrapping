import subprocess
import sys
import time
from core.logger import setup_custom_logger

# Logger kurulumu
logger = setup_custom_logger(__name__)

class TorManager:
    def __init__(self):
        self.is_linux = sys.platform.startswith('linux')

    def start_tor(self):
        """Tor servisini başlatır ve bağlantının kurulmasını bekler."""
        if not self.is_linux:
            logger.error("Otomatik Tor başlatma sadece Linux sistemlerde desteklenmektedir.")
            return False

        logger.info("Tor ağı başlatılıyor...")
        try:
            # Tor'un zaten çalışıp çalışmadığını kontrol et
            check = subprocess.run(['pgrep', '-x', 'tor'], capture_output=True)
            if check.returncode == 0:
                logger.info("Tor servisi zaten aktif.")
                return True

            # Tor servisini başlat
            subprocess.run(['sudo', 'service', 'tor', 'start'], check=True)
            
            # Servisin ayağa kalkması için kontrol döngüsü
            for i in range(1, 11):
                time.sleep(1)
                check = subprocess.run(['pgrep', '-x', 'tor'], capture_output=True)
                if check.returncode == 0:
                    logger.info(f"Tor başarıyla başlatıldı ({i}. saniyede).")
                    return True
            
            logger.error("Tor başlatıldı ancak servis yanıt vermiyor.")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Tor başlatılamadı! Sudo yetkisi gerekebilir: {str(e)}")
            return False

    def stop_tor(self):
        """Tor servisini güvenli bir şekilde kapatır."""
        logger.info("Tor ağı yavaşça kapatılıyor (Graceful Shutdown)...")
        try:
            subprocess.run(['sudo', 'service', 'tor', 'stop'], check=True)
            logger.info("Tor servisi başarıyla durduruldu.")
        except Exception as e:
            logger.error(f"Tor kapatılırken hata oluştu: {str(e)}")