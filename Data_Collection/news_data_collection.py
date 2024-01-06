#Collecting news from RSS feeds

from xml.etree import ElementTree
import requests
from collections import defaultdict, Counter
from time import sleep
from bs4 import BeautifulSoup
import email.utils
import pandas as pd
from requests.exceptions import SSLError, RequestException
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
import sqlite3
from datetime import datetime, timedelta, timezone

only_important_articles = "no"


# Google News RSS URL
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss"

CURRENTS_API_ENDPOINT = "https://api.currentsapi.services/v1/latest-news"
CURRENTS_API_KEY = "pwJbzYsI1WeDVax8-XsywIFnipq_roq99H42W-o1pTANVv48"

# Define a list of important keywords that might be related to significant events.



GOOGLE_NEWS_RSS_ENDPOINT = "https://news.google.com/rss"

# List of important keywords
IMPORTANT_KEYWORDS = [
    "war", "election", "earthquake", "crisis", "outbreak", "attack", "peace", "treaty", "sanction", "merger",
    "bankruptcy", "protest", "riot", "tsunami", "hurricane", "typhoon", "flood", "wildfire", "shooting",
    "explosion", "kidnap", "hostage", "terror", "summit", "resignation", "strike", "lockdown", "pandemic",
    "epidemic", "cyberattack", "hack", "leak", "whistleblower", "trade war", "tariff", "embargo", "coup",
    "assassination", "drought", "famine", "recession", "depression", "stock crash", "default", "sanction",
    "tension", "diplomacy", "talks", "meeting", "conference", "convention", "deal", "agreement", "pact",
    "alliance", "partnership", "collaboration", "breakthrough", "discovery", "research", "study", "finding",
    "vaccine", "cure", "treatment", "symposium", "award", "honor", "recognition", "launch", "mission",
    "space", "rocket", "satellite", "probe", "lander", "rover", "acquisition", "takeover", "IPO", "bankrupt",
    "deficit", "surplus", "growth", "decline", "profit", "loss", "revenue", "sales", "forecast", "prediction",
    "outlook", "projection", "anticipation", "expectation", "announcement", "innovation", "revolution",
    "revelation", "scandal", "controversy", "allegation", "investigation", "arrest", "charge", "conviction","sentence", "verdict", "lawsuit", "litigation", "settlement", "fine", "penalty", "reform", "policy",
"regulation", "legislation", "bill", "act", "law", "order", "decree", "mandate", "directive", "ruling",
"judgment", "decision", "opinion", "view", "stance", "position", "strategy", "plan", "initiative", "program",
"campaign", "movement", "cause", "issue", "matter", "topic", "subject", "debate", "discussion", "dialogue",
"talk", "conversation", "negotiation", "mediation", "intervention", "involvement", "participation",
"engagement", "commitment", "dedication", "devotion", "allegiance", "loyalty", "fidelity", "faithfulness",
"adherence", "conformity", "compliance", "observance", "respect", "honor", "esteem", "value", "worth",
"importance", "significance", "relevance", "pertinence", "applicability", "suitability", "fitness",
"appropriateness", "rightness", "correctness", "accuracy", "precision", "exactness", "closeness",
"proximity", "vicinity", "nearness", "imminence", "approach", "onset", "commencement", "beginning",
"start", "inception", "origin", "source", "root", "cause", "motive", "reason", "purpose", "aim",
"objective", "goal", "target", "end", "conclusion", "finish", "completion", "termination", "cessation",
"halt", "stop", "pause", "break", "interval", "gap", "interlude", "lapse", "period", "phase", "stage",
"step", "point", "moment", "instant", "juncture", "circumstance", "situation", "condition", "state",
"status", "position", "place", "site", "location", "setting", "scene", "background", "context", "framework",
"reference", "benchmark", "standard", "criterion", "norm", "rule", "principle", "maxim", "precept",
"command", "order", "instruction", "guideline", "recommendation", "suggestion", "advice", "counsel",
"guidance", "direction", "orientation", "perspective", "outlook", "viewpoint", "stance", "attitude",
"approach", "method", "technique", "mode", "manner", "style", "way", "means", "medium", "instrument",
"agent", "vehicle", "channel", "route", "path", "road", "track", "course", "direction", "trend", "current",
"stream", "flow", "movement", "motion", "action", "activity", "operation", "performance", "functioning",
]

RSS_FEEDS = [
    "https://news.google.com/rss",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://www.aljazeera.com/xml/rss/all.xml",
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "https://www.theguardian.com/international/rss",
    "https://reuters.com/world",
]


def create_connection():
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

def store_article_in_db(title, url, content):
    if article_exists_in_db(url):
        print(f"Article '{title}' already exists in the database. Skipping...")
        return False

    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO important_articles (title, url, content)
        VALUES (?, ?, ?)
        ''', (title, url, content))
        conn.commit()

    print(f"Article '{title}' stored to SQLite database.")
    return True

def fetch_news_data_from_feeds():
    all_news_data = []

    DATE_FORMATS = [
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
        # Add more date formats here as needed
    ]

    for feed in RSS_FEEDS:
        print(f"Fetching latest news from {feed}...")
        try:
            response = requests.get(feed)

            if response.status_code == 200:
                try:
                    # Parse the XML response
                    root = ElementTree.fromstring(response.content)

                    # Extract the title, link, and publication date of each item in the feed
                    feed_news_data = []
                    for item in root.findall(".//item"):
                        title = item.find("title").text
                        url = item.find("link").text
                        pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else None

                        if pub_date_str:
                            pub_date = None

                            # Try each date format
                            for fmt in DATE_FORMATS:
                                try:
                                    pub_date = datetime.strptime(pub_date_str, fmt)
                                    break  # Successfully parsed the date, so exit the loop
                                except ValueError:
                                    pass  # Date didn't match this format, try the next one

                            if pub_date:
                                # Make pub_date offset-naive by converting it to UTC and removing the timezone information
                                pub_date = pub_date.astimezone(timezone.utc).replace(tzinfo=None)

                                time_diff = datetime.utcnow() - pub_date
                                if time_diff <= timedelta(minutes=120):
                                    feed_news_data.append({"title": title, "url": url, "pubDate": pub_date_str})
                            else:
                                print(f"Unknown date format for {title}: {pub_date_str}")

                    # Print the number of articles retrieved from this feed
                    print(f"Retrieved {len(feed_news_data)} news articles from {feed}")

                    all_news_data.extend(feed_news_data)
                except ElementTree.ParseError as e:
                    print(f"Failed to parse XML from {feed}. Error: {e}")
            else:
                print(f"Error {response.status_code}: {response.text}")
        except requests.RequestException as e:
            print(f"Failed to fetch from {feed}. Error: {e}")

    return all_news_data

def keyword_extraction(news_data):
    article_keywords = defaultdict(list)

    print("Extracting keywords from news titles...")
    for article in news_data:
        title = article.get('title', '').lower()  # Convert to lowercase for easier keyword matching
        found_keywords = [keyword for keyword in IMPORTANT_KEYWORDS if keyword in title]
        if found_keywords:
            article_keywords[article['title']] = found_keywords
    print("Keyword extraction complete.")

    return article_keywords

def scrape_news_content(url):
    USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    headers = {
        "User-Agent": USER_AGENT,
    }

    session = requests.Session()
    retries = 3
    for i in range(retries):
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ' '.join(p.text for p in paragraphs)
            return content
        except SSLError as e:
            print(f"SSL Error on attempt {i + 1}/{retries} for {url}. Error: {e}")
            if i < retries - 1:  # i is 0 indexed
                print("Retrying...")
            else:
                print("Giving up after maximum retries.")
        except RequestException as e:
            print(f"Error scraping {url}. Error: {e}")
            return None

    return None


def identify_important_news():
    SLEEP_DURATION = 300  # Time to wait between fetches in seconds

    while True:
        print("\nFetching news data from feeds...")
        news_data = fetch_news_data_from_feeds()

        if only_important_articles == "yes":
            print("Extracting keyword frequencies from titles...")
            keyword_freq = keyword_extraction(news_data)

            # Identify news articles that have important keywords
            important_news = [article for article in news_data if
                              any(keyword in article['title'].lower() for keyword in keyword_freq)]
        else:
            # If only_important_articles is set to "no", then treat all fetched news as important
            important_news = news_data

        if important_news:
            print("\nNews identified:")
            for news in important_news:
                print(f"- {news['title']} ({news['url']})")

                print(f"Scraping content for: {news['title']}...")
                content = scrape_news_content(news['url'])

                # Use the returned value from `store_article_in_db` to decide whether the article was stored
                if store_article_in_db(news['title'], news['url'], content):
                    print(f"Stored '{news['title']}' to SQLite database.")
                else:
                    print(f"'{news['title']}' was not stored as it already exists in the database.")
        else:
            print("No news identified in this cycle.")

        print(f"\nSleeping for {SLEEP_DURATION / 60} minutes before the next fetch...")
        sleep(SLEEP_DURATION)

if __name__ == "__main__":
    identify_important_news()
