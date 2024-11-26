import time
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

def parse_movies(url):
    driver = webdriver.Chrome()
    driver.get(url) 

    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    movies = []

    movie_blocks = soup.find_all("div", class_="styles_root__ti07r")
    for block in movie_blocks:
        title_tag = block.find("span", class_="styles_mainTitle__IFQyZ styles_activeMovieTittle__kJdJj")
        title = title_tag.text if title_tag else "Unknown"

        info_tags = block.find_all("span", class_="desktop-list-main-info_truncatedText__IMQRP")
        if len(info_tags) > 0:
            country_genre_director = info_tags[0].text.split("•")
            country = country_genre_director[0].strip() if len(country_genre_director) > 0 else "Unknown"
            genre_director = country_genre_director[1].split("\xa0\xa0")
            genre = genre_director[0]

            director = genre_director[1].replace("Режиссёр: ", "").strip()
        else:
            genre = "Unknown"
            country = "Unknown"
            director = "Unknown"
            
        actors = (
            info_tags[1].text.replace("В ролях:", "").strip()
            if len(info_tags) > 1
            else "Unknown"
        )

        movies.append({
            "title": title,
            "country": country,
            "genre": genre,
            "director": director,
            "actors": actors,
        })
    return movies

def parse_multiple_pages(base_url, pages):
    all_movies = []
    for page in range(1, 6):
        url = f"{base_url}?page={page}"
        print(f"Парсим страницу: {url}")
        movies = parse_movies(url)
        all_movies.extend(movies)
    return all_movies

base_url = "https://www.kinopoisk.ru/lists/movies/top250/"
# movies = parse_multiple_pages(base_url, pages=5)

# df = pd.DataFrame(movies)
# df.to_csv("movies.csv", index=False, encoding="utf-8")
# print("Данные сохранены в movies.csv")

# Векторизация текста
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
one_hot_encoder = OneHotEncoder()

preprocessor = ColumnTransformer(
    transformers=[
        ('genre', tfidf_vectorizer, 'genre'),
        ('actors', tfidf_vectorizer, 'actors'),
        ('country', one_hot_encoder, ['country'])
    ])

data = pd.read_csv("movies.csv")
# Применяем к данным
X = preprocessor.fit_transform(data)
X = preprocessor.fit_transform(data) 
X = X.toarray()

knn = NearestNeighbors(n_neighbors=5, metric='cosine')
knn.fit(X)

def get_recommendations(user_movies, X, knn):
    user_vector = X[user_movies].mean(axis=0)  # Усредняем векторы
    user_vector = np.asarray(user_vector).reshape(1, -1)  # Преобразуем в массив
    
    distances, indices = knn.kneighbors(user_vector)
    recommended_indices = [idx for idx in indices[0] if idx not in user_movies]
    
    return recommended_indices

# Фильмы пользователя
user_movies = [34, 41] # 34: Гарри Поттер и философский камень,Великобритания, фэнтези,Крис Коламбус,"Дэниэл Рэдклифф, Руперт Гринт"
                        # 41: Гарри Поттер и узник Азкабана,Великобритания, фэнтези,Альфонсо Куарон,"Дэниэл Рэдклифф, Руперт Гринт"

recommended_indices = get_recommendations(user_movies, X, knn)

recommended_movies = data.iloc[recommended_indices]
print("Рекомендованные фильмы:")
print(recommended_movies[['title']])
