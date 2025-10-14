# 🚀 Panduan Lengkap: Menjalankan Web Crawler di VSCode MacBook

## 📋 Daftar Isi
1. [Persiapan Awal](#persiapan-awal)
2. [Instalasi Tools](#instalasi-tools)
3. [Setup Project di VSCode](#setup-project-di-vscode)
4. [Instalasi Dependencies](#instalasi-dependencies)
5. [Konfigurasi Script](#konfigurasi-script)
6. [Menjalankan Crawler](#menjalankan-crawler)
7. [Troubleshooting](#troubleshooting)

---

## 1️⃣ Persiapan Awal

### Cek Versi Python
Buka Terminal di MacBook (⌘ + Space, ketik "Terminal"):

```bash
python3 --version
```

**Output yang diharapkan:** Python 3.8 atau lebih tinggi

Jika belum terinstall, install Python dari [python.org](https://www.python.org/downloads/)

---

## 2️⃣ Instalasi Tools

### A. Install Homebrew (Package Manager untuk macOS)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### B. Install Google Chrome (Jika belum ada)
Download dari: https://www.google.com/chrome/

### C. Install ChromeDriver
```bash
brew install --cask chromedriver
```

**Penting:** Izinkan ChromeDriver di System Preferences
```bash
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

### D. Install VSCode (Jika belum ada)
Download dari: https://code.visualstudio.com/

---

## 3️⃣ Setup Project di VSCode

### Langkah 1: Buat Folder Project
```bash
# Buat folder project
mkdir ~/Documents/sdgs-crawler
cd ~/Documents/sdgs-crawler
```

### Langkah 2: Buka di VSCode
```bash
# Buka VSCode di folder ini
code .
```

**Atau:** Buka VSCode → File → Open Folder → Pilih folder `sdgs-crawler`

### Langkah 3: Buat Virtual Environment

Di Terminal VSCode (View → Terminal atau `⌃ + `` `):

```bash
# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate
```

**Tanda berhasil:** Prompt terminal akan menampilkan `(venv)` di awal

### Langkah 4: Install Extension VSCode (Opsional tapi Recommended)

Klik ikon Extensions (⇧ + ⌘ + X) dan install:
- **Python** (by Microsoft)
- **Pylance** (by Microsoft)
- **SQLite Viewer** (by Florian Klampfer)

---

## 4️⃣ Instalasi Dependencies

Pastikan virtual environment aktif (ada `(venv)` di terminal), lalu:

```bash
# Install semua dependencies sekaligus
pip install selenium beautifulsoup4 sqlalchemy webdriver-manager lxml
```

**Verifikasi instalasi:**
```bash
pip list
```

Output harus menampilkan: selenium, beautifulsoup4, sqlalchemy, dll.

---

## 5️⃣ Konfigurasi Script

### Langkah 1: Buat File Script

Di VSCode, buat file baru: `crawler.py`
- Klik File → New File
- Atau: ⌘ + N
- Save As: `crawler.py`

### Langkah 2: Copy Script

Copy script crawler yang telah dibuat ke dalam file `crawler.py`

### Langkah 3: Modifikasi Konfigurasi

**Edit bagian ini di file `crawler.py`:**

```python
if __name__ == "__main__":
    # ===== KONFIGURASI =====
    # Ganti dengan URL target Anda
    BASE_URL = "https://sdgs.un.org/goals"  # ⬅️ UBAH INI
    
    # Database file akan disimpan di folder project
    DB_PATH = 'sqlite:///sdgs_crawler.db'
    
    # Maksimal halaman yang akan di-crawl
    MAX_PAGES = 50  # ⬅️ SESUAIKAN JUMLAH
    
    # Inisialisasi crawler
    crawler = WebCrawler(
        base_url=BASE_URL,
        db_connection_string=DB_PATH
    )
    
    # Mulai crawling
    crawler.start_crawling(max_pages=MAX_PAGES)
```

### Langkah 4: Update ChromeDriver Path (Jika Perlu)

Jika ChromeDriver tidak terdeteksi otomatis, tambahkan path manual di fungsi `_init_driver()`:

```python
def _init_driver(self):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Tambahkan path ChromeDriver jika perlu
        from selenium.webdriver.chrome.service import Service
        service = Service('/opt/homebrew/bin/chromedriver')  # Path macOS
        
        self.driver = webdriver.Chrome(service=service, options=options)
        logger.info("✓ Driver Selenium berhasil diinisialisasi")
    except Exception as e:
        logger.error(f"✗ Gagal menginisialisasi driver: {e}")
        raise
```

---

## 6️⃣ Menjalankan Crawler

### Metode 1: Via Terminal VSCode

```bash
# Pastikan virtual environment aktif
source venv/bin/activate

# Jalankan script
python3 crawler.py
```

### Metode 2: Via VSCode Run Button

1. Buka file `crawler.py`
2. Klik tombol ▶️ di kanan atas
3. Atau tekan: `⌃ + ⌥ + N`

### Metode 3: Via Debug Mode

1. Klik ikon Debug (⇧ + ⌘ + D)
2. Klik "create a launch.json file"
3. Pilih "Python File"
4. Klik tombol hijau "Start Debugging" (F5)

---

## 7️⃣ Monitoring & Results

### Melihat Progress

Output di Terminal akan menampilkan:
```
============================================================
MEMULAI WEB CRAWLING
============================================================
Base URL: https://example.com
Maksimal halaman: 50
============================================================

============================================================
Crawling: https://example.com
============================================================
  ✓ Halaman berhasil dibuka
  ✓ Elemen halaman berhasil dimuat
  ✓ Parsing HTML selesai
  ✓ Metadata diekstrak - Title: Example Domain...
  ✓ Data berhasil disimpan: Example Domain...
  ✓ Ditemukan 5 link internal
```

### Melihat Database Results

**Metode 1: Via Python**
```bash
python3
```

Lalu di Python shell:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from crawler import SDGsContent, Base

engine = create_engine('sqlite:///sdgs_crawler.db')
Session = sessionmaker(bind=engine)
session = Session()

# Lihat semua data
results = session.query(SDGsContent).all()
for r in results:
    print(f"{r.title} - {r.url}")

session.close()
exit()
```

**Metode 2: Via SQLite Viewer Extension**
1. Klik kanan file `sdgs_crawler.db`
2. Pilih "Open Database"
3. Explore data melalui UI

**Metode 3: Via Terminal SQLite**
```bash
sqlite3 sdgs_crawler.db

# Di SQLite shell:
.tables
SELECT title, url FROM sdgs_content LIMIT 5;
.quit
```

---

## 8️⃣ Troubleshooting

### ❌ Error: "chromedriver executable needs to be in PATH"

**Solusi 1:** Install via webdriver-manager
```python
# Di crawler.py, tambahkan:
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Ganti bagian init driver:
service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=options)
```

**Solusi 2:** Manual download
```bash
brew install --cask chromedriver
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

### ❌ Error: "Module not found"

```bash
# Pastikan virtual environment aktif
source venv/bin/activate

# Re-install dependencies
pip install -r requirements.txt
```

Buat file `requirements.txt`:
```
selenium==4.15.0
beautifulsoup4==4.12.2
sqlalchemy==2.0.23
webdriver-manager==4.0.1
lxml==4.9.3
```

### ❌ Error: "Permission denied" untuk ChromeDriver

```bash
chmod +x /opt/homebrew/bin/chromedriver
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

### ❌ Crawler terlalu lambat

Edit di `crawler.py`:
```python
# Kurangi delay
time.sleep(0.5)  # dari 1 detik ke 0.5 detik

# Atau non-headless untuk debugging
# options.add_argument('--headless')  # Comment baris ini
```

### ❌ Database locked error

```bash
# Tutup semua koneksi database
pkill -f python

# Atau hapus file lock
rm sdgs_crawler.db-journal
```

---

## 9️⃣ Tips & Best Practices

### 📌 Gunakan `.gitignore`

Buat file `.gitignore`:
```
venv/
*.db
*.db-journal
__pycache__/
*.pyc
.DS_Store
```

### 📌 Membuat Script Lebih Robust

Tambahkan di `crawler.py`:
```python
# Retry mechanism
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def crawl_page(self, url):
    # existing code...
```

### 📌 Monitoring dengan Progress Bar

Install: `pip install tqdm`

Modifikasi loop:
```python
from tqdm import tqdm

for url in tqdm(self.urls_to_visit, desc="Crawling"):
    self.crawl_page(url)
```

### 📌 Export Data ke CSV

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///sdgs_crawler.db')
df = pd.read_sql_table('sdgs_content', engine)
df.to_csv('hasil_crawling.csv', index=False)
```

---

## 🎓 Keyboard Shortcuts VSCode di MacBook

| Aksi | Shortcut |
|------|----------|
| Open Terminal | ⌃ + ` |
| Command Palette | ⇧ + ⌘ + P |
| Run Python File | ⌃ + ⌥ + N |
| New File | ⌘ + N |
| Save | ⌘ + S |
| Find | ⌘ + F |
| Comment/Uncomment | ⌘ + / |
| Format Document | ⇧ + ⌥ + F |

---

## 📚 Resources Tambahan

- **Selenium Documentation**: https://selenium-python.readthedocs.io/
- **BeautifulSoup Documentation**: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **VSCode Python Tutorial**: https://code.visualstudio.com/docs/python/python-tutorial

---

## ✅ Checklist Setup

- [ ] Python 3.8+ terinstall
- [ ] VSCode terinstall
- [ ] Homebrew terinstall
- [ ] ChromeDriver terinstall dan dapat dijalankan
- [ ] Virtual environment dibuat dan diaktifkan
- [ ] Dependencies terinstall
- [ ] Script crawler.py dibuat
- [ ] BASE_URL dikonfigurasi
- [ ] Script berhasil dijalankan
- [ ] Database berhasil dibuat
- [ ] Data berhasil tersimpan

---

**Selamat mencoba! 🎉**

Jika menemui masalah, cek bagian Troubleshooting atau jalankan dengan mode debug untuk melihat error detail.