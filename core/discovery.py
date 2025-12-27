import requests
from bs4 import BeautifulSoup

class DarkWebDiscovery:
    def __init__(self):
        self.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}

    def search_ahmia(self, query):
        url = f"http://msydruic6ihgh34c.onion/search/?q={query}"
        try:
            response = requests.get(url, proxies=self.proxies, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [cite.text.split(' ')[0] for cite in soup.find_all('cite') if ".onion" in cite.text]
            return list(set(links))
        except Exception as e:
            print(f"Discovery hatası: {e}")
            return []
