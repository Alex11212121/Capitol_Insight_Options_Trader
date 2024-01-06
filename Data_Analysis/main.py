#This is where we combine everything, calling the LDA model, the data from the database

import sqlite3
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy
from Optional.keyword_module import keywords_module
from lda_module import update_lda_model, load_lda_model_and_dictionary

# Download necessary nltk packages
"""nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')"""
nlp = spacy.load("en_core_web_sm")

KEYWORD_TO_STOCK = {
    "oil": ["XOM", "CVX", "BP", "RDS.A", "TOT"],
    "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "FB", "TSLA", "NVDA", "ADBE", "CRM", "INTC"],
    "automobile": ["TSLA", "F", "GM", "TM", "HMC", "NSANY", "VWAGY"],
    "finance": ["JPM", "GS", "BAC", "WFC", "C", "MA", "V"],
    "health": ["JNJ", "PFE", "MRNA", "ABBV", "GILD", "UNH", "AMGN"],
    "energy": ["NEE", "DUK", "D", "SO", "EXC"],
    "telecom": ["VZ", "T", "TMUS"],
    "entertainment": ["DIS", "NFLX", "CMCSA", "CHTR", "FOXA"],
    "consumer": ["PG", "KO", "PEP", "MCD", "PM", "BTI", "UL", "CL", "EL"],
    "pharma": ["ROG.VX", "NVS", "MRK", "PFE", "ABT"],
    "retail": ["WMT", "COST", "TGT", "DG", "HD", "LOW"],
    "aerospace": ["BA", "LMT", "RTX", "NOC", "GD"],
    "semiconductor": ["TSM", "INTC", "NVDA", "QCOM", "AVGO"],
    "biotech": ["GILD", "BIIB", "REGN", "VRTX", "ILMN"],
    "transport": ["UPS", "FDX", "DAL", "UAL", "LUV", "CSX"],
    "metals": ["RIO", "BHP", "FCX", "NEM", "AA"],
    "agriculture": ["DE", "ADM", "MON", "BG", "POT"],
    "defense": ["LMT", "RTX", "BA", "GD", "NOC"],
    "real estate": ["AMT", "PLD", "SPG", "AVB", "EQR"],
    "beverage": ["KO", "PEP", "TAP", "STZ", "SAM"],
    "defense": ["LMT", "RTX", "BA", "NOC", "GD"],
    "aerospace": ["BA", "LMT", "RTX", "NOC", "SPCE"],
    "missiles": ["LMT", "RTX", "BA", "NOC"],
    "jets": ["BA", "LMT", "RTX"],
    "tanks": ["GD", "BAE.L"],
    "submarines": ["GD", "BAE.L"],
    "ships": ["HII", "GD", "BAE.L"],
    "drones": ["AVAV", "LMT", "BA"],
    "ammunition": ["OLN"],
    "firearms": ["SWBI", "RGR"],
    "radar": ["RTX", "LMT", "BA", "NOC"],
    "cybersecurity": ["RTX", "LMT", "BA", "NOC", "CSCO", "PANW", "FTNT"],
    "military": ["LMT", "RTX", "BA", "NOC", "GD", "HII", "BAE.L", "SWBI", "RGR"],
    "war": ["LMT", "RTX", "BA", "NOC", "GD", "HII", "BAE.L", "SWBI", "RGR", "AVAV", "OLN"],
    "israel": ["ESLT", "TEVA", "CHKP", "NICE"],
    "palestine": [],  # There aren't notable Palestinian stocks on major exchanges as of my last training cut-off in 2022
    "middle east": ["XOM", "CVX", "BP", "TOT", "RDS.A"], # Oil companies that might be affected by Middle East tensions
    "russia": ["GAZP.ME", "LKOH.ME", "ROSN.ME", "SBER.ME", "YNDX"],
    "ukraine": ["CEENF", "ASTVY"],
    "china": ["BABA", "JD", "TCEHY", "BIDU", "NIO"],
    "north korea": [],  # The impact would mostly be indirect through geopolitical tensions
    "south korea": ["SSNLF", "HYMTF", "POSCO", "KRX", "KRW="], # Samsung, Hyundai, POSCO, Korean Exchange, Korean Won
    "iran": [], # Limited direct investment opportunities due to sanctions as of 2022
    "saudi arabia": ["2222.SR"], # Saudi Aramco
    "venezuela": [], # Venezuela's stock market is not readily accessible to most international investors as of 2022
    "israel-palestine conflict": ["ESLT", "TEVA", "XOM", "CVX", "BP", "TOT", "RDS.A"],
    "russia-ukraine tension": ["GAZP.ME", "LKOH.ME", "ROSN.ME", "SBER.ME", "CEENF", "ASTVY"],
    "china-taiwan tension": ["BABA", "JD", "TCEHY", "BIDU", "NIO", "TSM", "ACNFF", "UMC", "FXI"],
    "north-south korea tension": ["SSNLF", "HYMTF", "POSCO", "KRX", "KRW="],
    "us-china trade war": ["BABA", "JD", "TCEHY", "BIDU", "NIO", "AAPL", "MSFT", "GOOGL", "AMZN", "FB"]
}


def fetch_articles_from_db():
    conn = sqlite3.connect('articles.db')

    # Get a list of all tables in the database
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables in the database:")
    for table in tables:
        print(table[0])

    cursor.close()

    query = "SELECT * FROM important_articles"
    df = pd.read_sql_query(query, conn)
    return df



if __name__ == "__main__":
    # Update or train the LDA model with any new articles
    update_lda_model()

    # Optionally, load the LDA model and dictionary for use (in case they are needed elsewhere)
    lda_model, dictionary = load_lda_model_and_dictionary()

    articles_df = fetch_articles_from_db()

    for index, row in articles_df.iterrows():
        print(f"\nAnalyzing article: {row['title']}")

        # Analyze based on keywords
        recommendations = keywords_module(row['content'])
        print(f"Recommended stocks based on keyword analysis: {', '.join(recommendations)}")

        # Analyze based on LDA topics
        # Tokenize and process the article content
        tokenized_content = word_tokenize(row['content'].lower())
        stop_words = set(stopwords.words('english'))
        filtered_content = [word for word in tokenized_content if word not in stop_words]
        bow_content = dictionary.doc2bow(filtered_content)

        # Get the topics for the article
        topics = lda_model.get_document_topics(bow_content)
        print("Identified topics for this article:")
        for topic_id, prob in topics:
            print(f"Topic {topic_id}: {lda_model.print_topic(topic_id)} (Probability: {prob:.2f})")

        # NOTE: You can then use these topics to make further stock recommendations if needed
