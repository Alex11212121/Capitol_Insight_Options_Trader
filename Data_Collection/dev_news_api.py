import requests
import sqlite3
from datetime import datetime

# NewsAPI.org details
NEWS_API_ENDPOINT = "http://newsapi.org/v2/everything"
NEWS_API_KEY = "f65678ce99cc4c12baa233f70ee161df"

def create_connection():
    """Creates and returns a connection to the database."""
    return sqlite3.connect('articles.db')

def article_exists_in_db(url):
    """Checks if the article with the given URL is already present in the database."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT COUNT(*) FROM important_articles WHERE url = ?
        ''', (url,))
        count = cursor.fetchone()[0]
    return count > 0

def store_article_in_db(article):
    """Stores the given article in the database."""
    title = article['title']
    url = article['url']
    content = article.get('content', '')  # or 'description', depending on what you want to store

    # Assuming 'LDA_trained' is a boolean or some sort of flag you set later, defaulting it to 0 (or False)
    LDA_trained = 0

    if article_exists_in_db(url):
        print(f"Article '{title}' already exists in the database. Skipping...")
        return False

    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO important_articles (title, url, content, LDA_trained)
        VALUES (?, ?, ?, ?)
        ''', (title, url, content, LDA_trained))
        conn.commit()

    print(f"Article '{title}' stored in the database.")
    return True

def fetch_news_from_newsapi(query, from_date, to_date):
    """Fetches news from NewsAPI."""
    params = {
        'q': query,
        'from': from_date,
        'to': to_date,
        'apiKey': NEWS_API_KEY
    }
    response = requests.get(NEWS_API_ENDPOINT, params=params)
    if response.status_code == 200:
        return response.json()['articles']
    else:
        print(f"Error fetching news: {response.status_code}")
        return []

def main():
    """Main function to fetch and store news."""
    query = "finance"  # or any other topic of interest
    from_date = "2023-12-01"
    to_date = "2023-12-29"
    articles = fetch_news_from_newsapi(query, from_date, to_date)

    for article in articles:
        if store_article_in_db(article):
            print(f"Stored '{article['title']}' to SQLite database.")
        else:
            print(f"'{article['title']}' was not stored as it already exists in the database.")

if __name__ == "__main__":
    main()
