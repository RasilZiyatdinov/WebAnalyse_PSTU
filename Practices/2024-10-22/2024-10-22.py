import os
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import zipfile
from pathlib import Path
from urllib.parse import urlparse, unquote
import random

def download_images_to_zip(url, output_zip="images.zip", min_resolution=(100, 100), max_resolution=(4000, 4000)):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Не удалось получить страницу: {url}, статус: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    img_urls = set() 
    for img_tag in soup.find_all('img'):
        img_url = img_tag.get('data-src') or img_tag.get('src')
        if not img_url and 'data-srcset' in img_tag.attrs:
            srcset = img_tag['data-srcset']
            img_url = max(
                [url.split(' ')[0] for url in srcset.split(',')],
                key=lambda u: int(u.split(' ')[1].replace('w', '')) if ' ' in u else 0
            )
        if img_url:
            img_urls.add(urljoin(url, img_url))

    for picture_tag in soup.find_all('picture'):
        for source_tag in picture_tag.find_all('source'):
            source_url = source_tag.get('data-srcset') or source_tag.get('srcset') or source_tag.get('src')
            if source_url:
                if ',' in source_url:
                    source_url = max(
                        [url.split(' ')[0] for url in source_url.split(',')],
                        key=lambda u: int(u.split(' ')[1].replace('w', '')) if ' ' in u else 0
                    )
                img_urls.add(urljoin(url, source_url))

    with zipfile.ZipFile(output_zip, 'w') as zip_file:
        for img_url in img_urls:
            try:
                img_response = requests.get(img_url, stream=True, timeout=10)
                img_response.raise_for_status()

                img = Image.open(BytesIO(img_response.content))
                if min_resolution[0] <= img.width <= max_resolution[0] and min_resolution[1] <= img.height <= max_resolution[1]:
                    img_format = img.format.lower()
                    if img_format == 'webp':
                        img = img.convert("RGB")
                        img_format = 'jpg'

                    parsed_url = urlparse(img_url)
                    original_name = os.path.basename(parsed_url.path)
                    original_name = unquote(original_name)
                    file_name = Path(original_name).stem
                    archive_name = f"{file_name}.{img_format}"

                    img_bytes = BytesIO()
                    img.save(img_bytes, format=img_format.upper())
                    img_bytes.seek(0)
                    zip_file.writestr(archive_name, img_bytes.read())
                    # print(f"Сохранено в архив: {archive_name}")
            except Exception as e:
                print(f"Ошибка загрузки {img_url}: {e}")

    print(f"Архив сохранен: {output_zip}")
    return output_zip




def create_yolo_dataset(zip_path, output_dir, proportions=(0.8, 0.2)):
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        image_names = zipf.namelist()
        random.shuffle(image_names)
        
        train_split = int(len(image_names) * proportions[0])
        train_images = image_names[:train_split]
        val_images = image_names[train_split:]
        
        train_dir = os.path.join(output_dir, 'train')
        val_dir = os.path.join(output_dir, 'val')
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)

        for image_name in train_images:
            zipf.extract(image_name, train_dir)
        for image_name in val_images:
            zipf.extract(image_name, val_dir)
    
    print(f"Датасет создан в {output_dir} с пропорцией train/val: {proportions}")

# dir_name = 'drom'
# zip_path = download_images_to_zip("https://drom.ru/", output_zip=f"{dir_name}_images.zip")
# create_yolo_dataset(zip_path, output_dir=f"./{dir_name}_yolo_dataset", proportions=(0.8, 0.2))

dir_name = 'louvre'
zip_path = download_images_to_zip("https://collections.louvre.fr/en/recherche?limit=100&typology%5B0%5D=9", output_zip=f"{dir_name}_images.zip")
create_yolo_dataset(zip_path, output_dir=f"./{dir_name}_yolo_dataset", proportions=(0.8, 0.2))

# dir_name = 'scryfall'
# zip_path = download_images_to_zip("https://scryfall.com/search?q=(e%3Altr+cn%3E%3D452)+or+(e%3Altc+cn%3E%3D411)&order=set&as=grid&unique=prints", output_zip=f"{dir_name}_images.zip")
# create_yolo_dataset(zip_path, output_dir=f"./{dir_name}_yolo_dataset", proportions=(0.8, 0.2))
