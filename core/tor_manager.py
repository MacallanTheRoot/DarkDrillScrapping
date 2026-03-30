import subprocess
import sys
import time
import socket
from core.logger import setup_custom_logger

# Logger kurulumu
logger = setup_custom_logger(__name__)

class TorManager:
    def __init__(self, host="127.0.0.1", port=9050):
        self.is_linux = sys.platform.startswith('linux')
        self.is_windows = sys.platform.startswith('win')
        self.host = host
        self.port = port

    def _is_tor_ready(self):
        """Tor SOCKS portu erişilebilir mi kontrol eder."""
        try:
            with socket.create_connection((self.host, self.port), timeout=1.5):
                return True
        except OSError:
            return False

    def _wait_until_ready(self, timeout_seconds=20):
        """Tor servisinin SOCKS portundan hazır olmasını bekler."""
        for i in range(1, timeout_seconds + 1):
            if self._is_tor_ready():
                logger.info(f"Tor başarıyla hazır ({i}. saniyede).")
                return True
            time.sleep(1)
        return False

    def _run_command(self, cmd):
        """Komutu güvenli şekilde çalıştırır; hata durumunda False döner."""
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception:
            return False

    def _start_linux(self):
        # sudo olmayan ortamlarda önce doğrudan service, sonra sudo deneriz.
        return self._run_command(['service', 'tor', 'start']) or self._run_command(['sudo', 'service', 'tor', 'start'])

    def _stop_linux(self):
        return self._run_command(['service', 'tor', 'stop']) or self._run_command(['sudo', 'service', 'tor', 'stop'])

    def _start_windows(self):
        # Farklı kurulumlarda servis adları değişebildiği için aday isimlerle denenir.
        candidates = [
            ['sc', 'start', 'tor'],
            ['sc', 'start', 'Tor'],
            ['sc', 'start', '"Tor Win32 Service"'],
            ['net', 'start', 'tor'],
            ['net', 'start', 'Tor'],
        ]
        for cmd in candidates:
            if self._run_command(cmd):
                return True
        return False

    def _stop_windows(self):
        candidates = [
            ['sc', 'stop', 'tor'],
            ['sc', 'stop', 'Tor'],
            ['sc', 'stop', '"Tor Win32 Service"'],
            ['net', 'stop', 'tor'],
            ['net', 'stop', 'Tor'],
        ]
        for cmd in candidates:
            if self._run_command(cmd):
                return True
        return False

    def start_tor(self):
        """Tor servisini başlatır ve bağlantının kurulmasını bekler."""
        if self._is_tor_ready():
            logger.info("Tor servisi zaten aktif (SOCKS portu erişilebilir).")
            return True

        logger.info("Tor ağı başlatılıyor...")
        if self.is_linux:
            self._start_linux()
        elif self.is_windows:
            self._start_windows()
        else:
            logger.warning("Bu işletim sistemi için otomatik servis başlatma sınırlı olabilir, sadece port kontrolü yapılacak.")

        if self._wait_until_ready(timeout_seconds=20):
            return True

        logger.error("Tor başlatılamadı veya SOCKS portu yanıt vermiyor (127.0.0.1:9050).")
        return False

    def stop_tor(self):
        """Tor servisini güvenli bir şekilde kapatır."""
        logger.info("Tor ağı yavaşça kapatılıyor (Graceful Shutdown)...")

        if self.is_linux:
            self._stop_linux()
        elif self.is_windows:
            self._stop_windows()
        else:
            logger.warning("Bu işletim sistemi için otomatik servis durdurma sınırlı olabilir.")

        # Durdurma denemesinden sonra port kapanışını kontrol eder.
        for _ in range(10):
            if not self._is_tor_ready():
                logger.info("Tor servisi durduruldu veya SOCKS portu kapandı.")
                return True
            time.sleep(1)

        # Servis dışardan yönetiliyorsa port açık kalabilir; bunu hata yerine bilgi olarak bırakıyoruz.
        logger.warning("Tor portu hala açık görünüyor. Servis dış bir süreç tarafından yönetiliyor olabilir.")
        return False