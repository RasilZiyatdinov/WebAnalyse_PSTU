import os
import re
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from PIL import Image
import pytesseract
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile
from io import BytesIO
from collections import defaultdict
import warnings

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
warnings.simplefilter("ignore", requests.packages.urllib3.exceptions.InsecureRequestWarning)

class PDFScraper:
    def __init__(self, base_url, max_pdf_count=30, max_depth=5, max_pages_per_pdf=5, max_pdfs_per_site=3):
        self.base_url = base_url
        self.visited_urls = set()
        self.pdf_files = {}
        self.pdf_count = 0
        self.max_pdf_count = max_pdf_count
        self.max_depth = max_depth
        self.max_pages_per_pdf = max_pages_per_pdf
        self.max_pdfs_per_site = max_pdfs_per_site
        self.site_pdf_counts = defaultdict(int)

    def fetch_url(self, url):
        try:
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"Ошибка при загрузке {url}: {e}")
            return None

    def parse_page(self, url, current_path="", depth=5):
        if url in self.visited_urls or depth == 0 or self.pdf_count >= self.max_pdf_count:
            return
        
        self.visited_urls.add(url)

        page_content = self.fetch_url(url)
        if page_content is None:
            print(f"Не удалось загрузить страницу {url}, продолжаем")
            return

        soup = BeautifulSoup(page_content, "html.parser")
        pdf_links = soup.find_all("a", href=re.compile(r".*\.pdf$"))

        for link in pdf_links:
            if self.pdf_count >= self.max_pdf_count:
                print("Достигнут общий предел на количество PDF-файлов")
                return
            
            pdf_url = urljoin(url, link['href'])
            if self.site_pdf_counts[url] >= self.max_pdfs_per_site:
                print(f"Достигнут предел на количество PDF-файлов для страницы {url}")
                continue
            
            self.site_pdf_counts[url] += 1
            self.pdf_count += 1
            self.process_pdf(pdf_url, current_path)
            print(f"PDF загружен: {pdf_url}. Всего загружено PDF: {self.pdf_count}")

        subpage_links = soup.find_all("a", href=re.compile(r"^((?!\.).)*$"))
        for link in subpage_links:
            subpage_url = urljoin(url, link['href'])
            sub_path = os.path.join(current_path, urlparse(subpage_url).path.strip("/"))
            self.parse_page(subpage_url, sub_path, depth - 1)

    def process_pdf(self, pdf_url, path):
        pdf_content = self.fetch_url(pdf_url)
        if pdf_content is None:
            return

        pdf_path = os.path.join(path, os.path.basename(urlparse(pdf_url).path))
        pdf_text_path = pdf_path.replace(".pdf", ".txt")

        pdf_text = self.extract_text_from_pdf(BytesIO(pdf_content))
        self.pdf_files[pdf_path] = pdf_content
        self.pdf_files[pdf_text_path] = pdf_text.encode("utf-8")

    def extract_text_from_pdf(self, pdf_stream):
        pdf_reader = PdfReader(pdf_stream)
        full_text = ""
        max_pages = min(self.max_pages_per_pdf, len(pdf_reader.pages))

        for i in range(max_pages):
            page = pdf_reader.pages[i]
            text = page.extract_text()
            if text:
                full_text += text
            else:
                images = page.images
                for image_file in images:
                    image = Image.open(BytesIO(image_file.data))
                    full_text += self.extract_text_with_ocr(image) + "\n"
        
        return full_text

    def extract_text_with_ocr(self, image):
        text = pytesseract.image_to_string(image, lang="rus")
        return text

    def save_to_zip(self, output_filename="output.zip"):
        with ZipFile(output_filename, "w") as zip_file:
            for file_path, content in self.pdf_files.items():
                zip_file.writestr(file_path, content)
        print(f"Архив сохранен как {output_filename}")

    def run(self):
        self.parse_page(self.base_url, depth=self.max_depth)
        self.save_to_zip()

base_url = "https://pstu.ru/sveden/education/"
scraper = PDFScraper(base_url, max_pdf_count=50, max_depth=5, max_pages_per_pdf=5, max_pdfs_per_site=5)
scraper.run()
