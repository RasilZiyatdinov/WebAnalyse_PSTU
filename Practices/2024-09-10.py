import requests
import json
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from urllib.parse import quote_plus, unquote_plus

from warcio.archiveiterator import ArchiveIterator

def search_cc_index(url, index_name):
    encoded_url = quote_plus(url)
    index_url = f'http://index.commoncrawl.org/{index_name}-index?url={encoded_url}&output=json'
    response = requests.get(index_url)
 
    if response.status_code == 200:
        records = response.text.strip().split('\n')
        return [json.loads(record) for record in records]
    else:
        print(f"Ошибка при запросе индекса {index_name}: {response.status_code}")
        return None

def fetch_single_record(warc_record_filename, offset, length):
    s3_url = f'https://data.commoncrawl.org/{warc_record_filename}'
 
    byte_range = f'bytes={offset}-{offset + length - 1}'
 
    response = requests.get(
        s3_url,
        headers={'Range': byte_range},
        stream=True
    )
 
    if response.status_code == 206:
        stream = ArchiveIterator(response.raw)
        for warc_record in stream:
            if warc_record.rec_type == 'response':
                return warc_record.content_stream().read()
    else:
        print(f"Failed to fetch data: {response.status_code}")
     
    return None

def main():    
    keywords = ['Перм', 'Пастернак', 'ПНИПУ', 'ИТАС', 'МФТИ', 'МГУ', 'Московский государственный университет', 'МГУ имени М.В. Ломоносова']
    indexes = ['CC-MAIN-2024-42', 'CC-MAIN-2024-38', 'CC-MAIN-2024-33']
    
    for index_name in indexes:
        print(f'Поиск в индексе: {index_name}')
        url = 'ru.wikipedia.org/*'
        records = search_cc_index(url, index_name)

        if (records):
            key_results = []
            for record in records:
                if any(requote_uri(keyword) in record['url'] for keyword in keywords):
                    key_results.append(record)

            html_results = {}

            for result in key_results:
                record = fetch_single_record(result['filename'], int(result['offset']), int(result['length']))
                if record:
                    html_results[result['url']] = (record, result['timestamp'])
            for url, (html, timestamp) in html_results.items():
                beautiful_soup = BeautifulSoup(html, 'html.parser')
                for keyword in keywords:
                    if keyword.casefold() in beautiful_soup.get_text().casefold():
                        print(f"Ключевое слово: {keyword}")
                        print(f"URL: {unquote_plus(url)}")
                        print(f"Timestamp: {timestamp}")
                print("\n")

if __name__ == '__main__':
    main()
