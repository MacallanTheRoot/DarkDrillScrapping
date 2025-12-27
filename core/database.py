import sqlite3
from datetime import datetime

class DatabaseManager: # <-- İsmin bu olduğundan emin ol (Büyük/Küçük harf duyarlı)
    def __init__(self, db_name="darkweb_intel.db"):
        self.db_name = db_name
        self._setup_tables()

    def _setup_tables(self):
        """Tabloları oluşturur."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Siteler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                last_scanned TIMESTAMP,
                status TEXT
            )
        ''')
        
        # Sızıntılar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                type TEXT,
                content TEXT,
                discovery_date TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites (id),
                UNIQUE(type, content)
            )
        ''')
        conn.commit()
        conn.close()

    def save_site(self, url, status):
        """Siteyi kaydeder veya günceller."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO sites (url, last_scanned, status)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET last_scanned=excluded.last_scanned, status=excluded.status
        ''', (url, now, status))
        
        conn.commit()
        site_id = cursor.execute("SELECT id FROM sites WHERE url=?", (url,)).fetchone()[0]
        conn.close()
        return site_id

    def save_findings(self, site_id, findings_dict):
        """Bulguları kaydeder."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        new_count = 0
        
        for category, items in findings_dict.items():
            for item in items:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO leaks (site_id, type, content, discovery_date)
                        VALUES (?, ?, ?, ?)
                    ''', (site_id, category, item, now))
                    if cursor.rowcount > 0:
                        new_count += 1
                except:
                    continue
        
        conn.commit()
        conn.close()
        return new_count
