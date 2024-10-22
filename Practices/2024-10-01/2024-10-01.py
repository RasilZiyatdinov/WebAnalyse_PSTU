import requests
import json
from datetime import date
import os
import bs4
from hashlib import md5


def get_wikimedia_data(query):
    base_urls = {
        'wikipedia': 'https://en.wikipedia.org/w/api.php',
        'wikidata': 'https://www.wikidata.org/w/api.php',
        'wiktionary': 'https://en.wiktionary.org/w/api.php',
        'commons': 'https://commons.wikimedia.org/w/api.php'
    }
    
    data = {}
    
    wiki_params = {
        'action': 'query',
        'format': 'json',
        'titles': query,
        'prop': 'extracts|images|links',
        'exintro': True
    }
    response = requests.get(base_urls['wikipedia'], params=wiki_params)
    data['wikipedia'] = response.json()

    wikidata_params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': query,
        'language': 'en'
    }
    response = requests.get(base_urls['wikidata'], params=wikidata_params)
    data['wikidata'] = response.json()

    wiktionary_params = {
        'action': 'query',
        'format': 'json',
        'titles': query,
        'prop': 'extracts',
        'exintro': True
    }
    response = requests.get(base_urls['wiktionary'], params=wiktionary_params)
    data['wiktionary'] = response.json()

    commons_params = {
        'action': 'query',
        'format': 'json',
        'titles': query,
        'prop': 'imageinfo',
        'iiprop': 'url'
    }
    response = requests.get(base_urls['commons'], params=commons_params)
    data['commons'] = response.json()

    return data


def get_picture_of_the_day():
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "format": "json",
        "formatversion": "2", 
        "prop": "text",
        "page": f"Template:POTD_protected/{date.today().isoformat()}"
    }

    response = requests.get(api_url, params=params).json()['parse']['text']
    potd_soup = bs4.BeautifulSoup(response, 'html.parser')
    description = potd_soup.find('div', attrs={'class':'mw-content-ltr mw-parser-output'}).find('img', alt = True)['alt']
    image_query_params = {
        "action": "query", "format": "json",
        "formatversion": "2", "prop": "images",
        "titles": f"Template:POTD_protected/{date.today().isoformat()}"
        }
    potd_image_data = requests.get(api_url, image_query_params).json()
    filename = str(potd_image_data["query"]["pages"][0]["images"][0]["title"]).replace(' ', '_')

    md5_hash = md5(filename[5:].encode('utf-8')).hexdigest()
    image_src = f'https://upload.wikimedia.org/wikipedia/commons/{md5_hash[0]}/{md5_hash[0:2]}/{filename[5:]}'

    today_folder = date.today().isoformat()
    os.makedirs(today_folder, exist_ok=True)

    image_filename = os.path.join(today_folder, filename[5:])
    image_response = requests.get(image_src)
    with open(image_filename, 'wb') as file:
        file.write(image_response.content)

    description_filename = os.path.join(today_folder, f'{os.path.splitext(os.path.basename(f"{filename[5:]}"))[0]}.txt')
    with open(description_filename, 'w') as file:
        file.write(description)

query = input()
data = get_wikimedia_data(query)
with open('data.json', 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=4, ensure_ascii=False)

get_picture_of_the_day()
