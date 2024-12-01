import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import yt_dlp
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("C:\\Users\\ziyat\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe")  # Замените на путь к chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fetch_page_source(url):
    driver = setup_driver()
    try:
        print(f"Открываю страницу: {url}")
        driver.get(url)
        time.sleep(5)

        page_source = driver.page_source
        return page_source
    finally:
        driver.quit()

def find_video_links_selenium(page_source, base_url):
    soup = BeautifulSoup(page_source, 'html.parser')
    video_links = set()

    for tag in soup.find_all('a', href=True):
        href = tag['href']
        if any(href.endswith(ext) for ext in ['.mp4', '.webm', '.m3u8', '.mpd']):
            video_links.add(urljoin(base_url, href))

    for video_tag in soup.find_all('video'):
        src = video_tag.get('src')
        if src:
            video_links.add(urljoin(base_url, src))

    return list(video_links)

def download_video_with_metadata(video_url, folder_name, idx):
    print(f"Загружаю видео {idx}: {video_url}")

    ydl_opts = {
        'outtmpl': os.path.join(folder_name, f'video_{idx}_%(title)s.%(ext)s'),
        'writeinfojson': True,
        'writethumbnail': True,
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    print(f"Видео {idx} успешно сохранено: {video_url}")

def fetch_video_and_metadata_selenium(url):
    try:
        page_source = fetch_page_source(url)
        
        parsed_url = url.replace("://", "_").replace("/", "_")
        folder_name = f"results_{parsed_url}"
        os.makedirs(folder_name, exist_ok=True)

        video_links = find_video_links_selenium(page_source, url)
        if not video_links:
            print(f"Видео не найдено на странице: {url}")
            return

        print(f"Найдено {len(video_links)} ссылок на видео: {video_links}")

        for idx, video_url in enumerate(video_links, start=1):
            try:
                download_video_with_metadata(video_url, folder_name, idx)
            except Exception as e:
                print(f"Ошибка при загрузке видео {video_url}: {e}")

    except Exception as e:
        print(f"Ошибка при обработке страницы {url}: {e}")

page_url = "https://rutube.ru"
fetch_video_and_metadata_selenium(page_url)
