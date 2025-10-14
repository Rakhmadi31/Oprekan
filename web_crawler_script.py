import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database Setup
Base = declarative_base()

class SDGsContent(Base):
    """Model database untuk menyimpan konten SDGs"""
    __tablename__ = 'sdgs_content'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    meta_description = Column(Text)
    keywords = Column(String(500))
    scraped_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<SDGsContent(url='{self.url}', title='{self.title}')>"


class WebCrawler:
    """
    Web Crawler untuk mengekstrak konten website SDGs
    """
    
    def __init__(self, base_url, db_connection_string='sqlite:///sdgs_crawler.db'):
        """
        Inisialisasi Web Crawler
        
        Args:
            base_url: URL dasar untuk crawling
            db_connection_string: String koneksi database
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.urls_to_visit = [base_url]
        
        # Setup Database
        self.engine = create_engine(db_connection_string)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Inisialisasi Selenium Driver
        self.driver = None
        self._init_driver()
        
    def _init_driver(self):
        """Inisialisasi Selenium WebDriver dengan opsi headless"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=options)
            logger.info("✓ Driver Selenium berhasil diinisialisasi")
        except Exception as e:
            logger.error(f"✗ Gagal menginisialisasi driver: {e}")
            raise
    
    def _is_valid_url(self, url):
        """
        Validasi URL untuk memastikan URL internal dan belum dikunjungi
        
        Args:
            url: URL yang akan divalidasi
            
        Returns:
            bool: True jika URL valid
        """
        parsed = urlparse(url)
        return (
            bool(parsed.netloc) and
            parsed.netloc == self.domain and
            url not in self.visited_urls and
            not url.endswith(('.pdf', '.jpg', '.png', '.gif', '.zip', '.doc', '.docx'))
        )
    
    def _extract_links(self, soup, current_url):
        """
        Ekstraksi semua link internal dari halaman
        
        Args:
            soup: BeautifulSoup object
            current_url: URL halaman saat ini
            
        Returns:
            list: Daftar URL internal yang ditemukan
        """
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            
            if self._is_valid_url(full_url):
                links.append(full_url)
        
        return links
    
    def _extract_metadata(self, soup, url):
        """
        Ekstraksi metadata dari halaman web
        
        Args:
            soup: BeautifulSoup object
            url: URL halaman
            
        Returns:
            dict: Dictionary berisi metadata halaman
        """
        metadata = {
            'url': url,
            'title': '',
            'content': '',
            'meta_description': '',
            'keywords': ''
        }
        
        # Ekstrak Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Ekstrak Meta Description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['meta_description'] = meta_desc['content'].strip()
        
        # Ekstrak Keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            metadata['keywords'] = meta_keywords['content'].strip()
        
        # Ekstrak Konten Paragraf
        paragraphs = soup.find_all('p')
        content_text = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        metadata['content'] = content_text[:5000]  # Batasi 5000 karakter
        
        return metadata
    
    def _save_to_database(self, metadata):
        """
        Simpan metadata ke database
        
        Args:
            metadata: Dictionary berisi metadata halaman
        """
        try:
            # Cek apakah URL sudah ada di database
            existing = self.session.query(SDGsContent).filter_by(url=metadata['url']).first()
            
            if existing:
                logger.info(f"  URL sudah ada di database: {metadata['url']}")
                return
            
            # Simpan data baru
            content = SDGsContent(
                url=metadata['url'],
                title=metadata['title'],
                content=metadata['content'],
                meta_description=metadata['meta_description'],
                keywords=metadata['keywords']
            )
            
            self.session.add(content)
            self.session.commit()
            logger.info(f"  ✓ Data berhasil disimpan: {metadata['title'][:50]}...")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"  ✗ Gagal menyimpan ke database: {e}")
    
    def crawl_page(self, url):
        """
        Crawl satu halaman web
        
        Args:
            url: URL yang akan di-crawl
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Crawling: {url}")
            logger.info(f"{'='*60}")
            
            # Buka halaman web
            self.driver.get(url)
            logger.info("  ✓ Halaman berhasil dibuka")
            
            # Tunggu elemen dimuat (WebDriverWait)
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info("  ✓ Elemen halaman berhasil dimuat")
            
            # Scroll untuk memuat konten dinamis
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Parsing konten dengan BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            logger.info("  ✓ Parsing HTML selesai")
            
            # Ekstraksi metadata
            metadata = self._extract_metadata(soup, url)
            logger.info(f"  ✓ Metadata diekstrak - Title: {metadata['title'][:50]}...")
            
            # Simpan ke database
            self._save_to_database(metadata)
            
            # Cari semua tautan internal
            internal_links = self._extract_links(soup, url)
            logger.info(f"  ✓ Ditemukan {len(internal_links)} link internal")
            
            # Tambahkan ke daftar URL belum dikunjungi
            for link in internal_links:
                if link not in self.urls_to_visit and link not in self.visited_urls:
                    self.urls_to_visit.append(link)
            
            # Tandai URL sebagai sudah dikunjungi
            self.visited_urls.add(url)
            
        except TimeoutException:
            logger.error(f"  ✗ Timeout saat memuat halaman: {url}")
        except WebDriverException as e:
            logger.error(f"  ✗ Error WebDriver: {e}")
        except Exception as e:
            logger.error(f"  ✗ Error tidak terduga: {e}")
    
    def start_crawling(self, max_pages=50):
        """
        Mulai proses crawling
        
        Args:
            max_pages: Maksimal halaman yang akan di-crawl
        """
        logger.info("\n" + "="*60)
        logger.info("MEMULAI WEB CRAWLING")
        logger.info("="*60)
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Maksimal halaman: {max_pages}")
        logger.info("="*60 + "\n")
        
        pages_crawled = 0
        
        try:
            # Ulangi proses hingga semua halaman telusuri
            while self.urls_to_visit and pages_crawled < max_pages:
                url = self.urls_to_visit.pop(0)
                
                if url not in self.visited_urls:
                    self.crawl_page(url)
                    pages_crawled += 1
                    
                    # Delay untuk menghindari overload server
                    time.sleep(1)
            
            logger.info("\n" + "="*60)
            logger.info("CRAWLING SELESAI")
            logger.info("="*60)
            logger.info(f"Total halaman di-crawl: {pages_crawled}")
            logger.info(f"Total halaman dikunjungi: {len(self.visited_urls)}")
            logger.info(f"URL tersisa: {len(self.urls_to_visit)}")
            logger.info("="*60 + "\n")
            
        except KeyboardInterrupt:
            logger.info("\n\nCrawling dihentikan oleh user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
            logger.info("✓ Driver Selenium ditutup")
        
        if self.session:
            self.session.close()
            logger.info("✓ Koneksi database ditutup")


# Contoh penggunaan
if __name__ == "__main__":
    # Ganti dengan URL target Anda
    BASE_URL = "https://example.com"  # Ubah sesuai kebutuhan
    
    # Inisialisasi crawler
    crawler = WebCrawler(
        base_url=BASE_URL,
        db_connection_string='sqlite:///sdgs_crawler.db'
    )
    
    # Mulai crawling (maksimal 50 halaman)
    crawler.start_crawling(max_pages=50)
    
    # Query contoh untuk melihat hasil
    print("\n" + "="*60)
    print("CONTOH DATA YANG TERSIMPAN")
    print("="*60)
    
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=crawler.engine)
    session = Session()
    
    results = session.query(SDGsContent).limit(5).all()
    for idx, content in enumerate(results, 1):
        print(f"\n{idx}. {content.title}")
        print(f"   URL: {content.url}")
        print(f"   Content: {content.content[:100]}...")
        print(f"   Scraped: {content.scraped_at}")
    
    session.close()
