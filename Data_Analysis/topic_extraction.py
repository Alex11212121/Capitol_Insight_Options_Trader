#Topic extraction code, very simple its the tuning which needs fine adjustment

from gensim import corpora
import gensim
from gensim import corpora
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy
import sqlite3

nlp = spacy.load("en_core_web_sm")


def reset_articles_training_status():
    """
    Reset the LDA_trained column for all articles to 0, meaning they are untrained.
    """
    conn = sqlite3.connect('articles.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE important_articles SET LDA_trained=0')

    conn.commit()
    conn.close()

def preprocess_text(text):
    # Tokenization
    tokens = word_tokenize(text.lower())

    # Removing punctuation and stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token.isalpha() and token not in stop_words]

    # Lemmatization
    lemmatized_tokens = [token.lemma_ for token in nlp(" ".join(tokens))]

    return lemmatized_tokens

def save_lda_model_and_dictionary(lda_model, dictionary):
    lda_model.save("lda_model.gensim")
    dictionary.save("dictionary.gensim")

def load_lda_model_and_dictionary():
    lda_model = gensim.models.LdaModel.load("lda_model.gensim")
    dictionary = gensim.corpora.Dictionary.load("dictionary.gensim")
    return lda_model, dictionary

def get_untrained_articles():
    conn = sqlite3.connect('articles.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, content FROM important_articles WHERE LDA_trained=0')
    articles = cursor.fetchall()

    conn.close()

    return articles

def mark_articles_as_trained(article_ids):
    conn = sqlite3.connect('articles.db')
    cursor = conn.cursor()

    cursor.executemany('UPDATE important_articles SET LDA_trained=1 WHERE id=?', [(id,) for id in article_ids])

    conn.commit()
    conn.close()

def train_lda_model(articles, num_topics=10):
    # Process articles
    processed_articles = [preprocess_text(article) for article in articles]

    # Convert processed articles into a bag-of-words representation
    dictionary = corpora.Dictionary(processed_articles)
    corpus = [dictionary.doc2bow(article) for article in processed_articles]

    # Train the LDA model
    lda_model = gensim.models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=15)
    return lda_model, dictionary
def update_lda_model():
    global dictionary, lda_model

    articles_data = get_untrained_articles()
    if not articles_data:
        print("No new articles to train on.")
        return

    article_ids, article_contents = zip(*articles_data)

    if dictionary is None or lda_model is None:
        lda_model, dictionary = train_lda_model(article_contents)
    else:
        # Tokenize, filter stopwords, and get the bow representation for the new articles
        tokenized_articles = [word_tokenize(article.lower()) for article in article_contents]
        stop_words = set(stopwords.words('english'))
        filtered_articles = [[word for word in article if word not in stop_words] for article in tokenized_articles]
        corpus = [dictionary.doc2bow(article) for article in filtered_articles]

        lda_model.update(corpus)

    # Mark these articles as trained
    mark_articles_as_trained(article_ids)

def print_topics(lda_model, num_words=5):
    """
    Prints the top words for each topic in the LDA model.

    Parameters:
    - lda_model: The trained LDA model.
    - num_words (int): The number of top words to print for each topic.
    """

    topics = lda_model.print_topics(num_words=num_words)
    for topic in topics:
        print(topic)


reset_lda = "yes"  # Change to "yes" to to reset and start afresh
dictionary = None
lda_model = None

if reset_lda == "yes":
    print("Resetting LDA model and starting from scratch.")
    lda_model, dictionary = None, None
    # Reset articles' training status in the database
    reset_articles_training_status()
else:
    # Try to load existing LDA model and dictionary
    try:
        lda_model, dictionary = load_lda_model_and_dictionary()
    except:
        print("Could not load existing model and dictionary. Starting fresh.")
        lda_model, dictionary = None, None








