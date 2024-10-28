import requests
from graphviz import Digraph

class WikimediaCrawler:
    def __init__(self, base_uri="https://ru.wikipedia.org/w/api.php", max_articles=30):
        self.base_uri = base_uri
        self.visited_articles = set()
        self.graph_data = Digraph(comment="Граф статей Wikimedia", format="svg")
        self.graph_data.attr('node', shape='ellipse')
        self.max_articles = max_articles

    def fetch_article_data(self, article_name, language="ru"):
        params = {
            "action": "parse",
            "page": article_name,
            "format": "json",
            "prop": "text|images|links",
            "redirects": 1
        }
        response = requests.get(self.base_uri, params=params)
        data = response.json()
        
        if "error" in data:
            return None
        
        links = [link["*"] for link in data["parse"]["links"] if link["ns"] == 0]
        
        return {
            "title": data["parse"]["title"],
            "links": links
        }

    def crawl_articles(self, start_article):
        current_level = [(start_article, 0)]
        self.visited_articles.add(start_article)

        while current_level and len(self.visited_articles) < self.max_articles:
            next_level = []

            for current_article, depth in current_level:
                if len(self.visited_articles) >= self.max_articles:
                    break

                article_data = self.fetch_article_data(current_article)
                if not article_data or not article_data["links"]:
                    continue
                
                title = article_data["title"]
                self.graph_data.node(title, label=f"{title}")
                self.visited_articles.add(current_article)

                links_to_add = article_data["links"][:4]
                
                for link in links_to_add:
                    if len(self.visited_articles) >= self.max_articles:
                        break
                    if link not in self.visited_articles:
                        self.visited_articles.add(link)
                        self.graph_data.edge(title, link)
                        next_level.append((link, depth + 1))

            current_level = next_level

    def save_graph(self, file_path="wikimedia_graph"):
        self.graph_data.render(file_path, view=True)
        print(f"Граф сохранен как {file_path}.svg")

crawler = WikimediaCrawler(max_articles=30)
start_article = "Черная металлургия"
crawler.crawl_articles(start_article)
crawler.save_graph("wikimedia_graph")
