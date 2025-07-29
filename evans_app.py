import streamlit as st
import nltk
import gdown
import csv
from newspaper import Article
from urllib.parse import urlparse
from IPython.display import display, HTML
import re
import datetime
import nltk
import ipywidgets as widgets
import streamlit.components.v1 as components

nltk.download('punkt')

from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

csv_path = "source_map.csv"

# Load source map
def load_source_map(csv_path):
    source_map = {}
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            domain = row['domain'].strip().lower()
            name = row['source_name'].strip()
            source_map[domain] = name
    return source_map

SOURCE_NAME_MAP = load_source_map(csv_path)

punkt_params = PunktParameters()
punkt_params.abbrev_types = set(['dr', 'mr', 'mrs', 'ms', 'sen', 'rep', 'gen', 'prof', 'inc', 'u.s', 'd.c', 'gov'])
tokenizer = PunktSentenceTokenizer(punkt_params)

def truncate_to_first_sentence_after_100_words(text):
    try:
        sentences = tokenizer.tokenize(text)
        word_count = 0
        final_sentences = []

        for i, sentence in enumerate(sentences):
            word_count += len(sentence.split())
            final_sentences.append(sentence.strip())
            if word_count >= 100:
                break

        combined = " ".join(final_sentences)

        # Preserve trailing quotation mark if present immediately after period
        original_index = text.find(combined) + len(combined)
        if original_index < len(text) and text[original_index] in ['"', '”']:
            combined += text[original_index]

        return combined
    except Exception as e:
        return f"[Error truncating text: {e}]"

# Clean leading dateline from article body
def clean_clip_body(text):
    return re.sub(
        r"^(?:[A-Z\s\.,\-]+(?:\([^)]+\))?\s*)?[—\-]\s*",
        "",
        text.strip()
    )

# Format the clip for display
def format_clip(title, url, author, source, date, body):
    title_html = f'<a href="{url}" style="color:#1155cc; text-decoration:underline;">{title}</a>'

    source_base = re.sub(r'\.(com|org|net|gov|edu|co|io|us|biz|info|tv)$', '', source, flags=re.IGNORECASE).lower()
    source_cleaned = SOURCE_NAME_MAP.get(source_base, source_base.title())

    if author and author.lower() != "unknown":
        author_list = [a.strip() for a in author.split(",")]
        if len(author_list) > 1:
            author = ", ".join(author_list[:-1]) + " and " + author_list[-1]
        else:
            author = author_list[0]
        byline_html = f'<b>{source_cleaned}, {author}, {date}</b>'
    else:
        byline_html = f'<b>{source_cleaned}, {date}</b>'

    body_html = f"""
    <div style='font-family:Calibri, sans-serif; font-size:11pt; color:#000000;'>
        {title_html}<br>
        {byline_html}<br>
        {body}<br><br>
    </div>
    """
    return HTML(body_html)

# Clean author list
def clean_author_list(raw_authors, domain):
    if not raw_authors:
        return ""

    domain_base = domain.lower().replace("www.", "").split(".")[0]

    # Bad tokens (junk, outlets, domains, etc.)
    exclusion_tokens = set([
        "http", "facebook.com", "product developer", domain_base,
        "news4", "abc7", "nbcnews", "wusa9", "kktv", "fox5", "cbs",
        "cnn", "nbc", "abc", "koaa", "wjla", "ap", "associated press",
        "reuters", "bloomberg", "apnews", "for the associated press", "d.c"
    ])

    seen = set()
    cleaned_authors = []

    for raw_author in raw_authors:
        author = raw_author.strip()
        lower_author = author.lower()

        # Skip if any exclusion token is present
        if any(token in lower_author for token in exclusion_tokens):
            continue

        # Normalize: convert dashed names like 'ashraf-khalil' → 'Ashraf Khalil'
        normalized = re.sub(r'[-_]', ' ', lower_author).title().strip()

        # Skip duplicates (case-insensitive)
        if normalized.lower() in seen:
            continue

        seen.add(normalized.lower())
        cleaned_authors.append(normalized)

    return ", ".join(cleaned_authors)

# Extract, process, display article
def generate_and_display_clip(url):
    try:
        article = Article(url)
        article.browser_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
        article.download()
        article.parse()

        title = article.title.strip()
        domain = urlparse(url).netloc.replace("www.", "")
        authors = clean_author_list(article.authors, domain)
        date = article.publish_date.strftime("%-m/%-d/%y") if article.publish_date else datetime.datetime.now().strftime("%-m/%-d/%y")
        body = truncate_to_first_sentence_after_100_words(article.text)
        body = clean_clip_body(body)

        return format_clip(title, url, authors, domain, date, body.strip())

    except Exception as e:
        print(f"Error processing {url}: {e}\n")
        return HTML("<div style='color:red;'>Failed to process article. Please check the URL.</div>")

# UI: Input box + button
user_url = st.text_input("Place URL here")

st.button("Run script")

if st.button:
    #clean_url = user_url.value.strip()
    output = generate_and_display_clip(user_url)
    my_ipython_html_object = output
    if my_ipython_html_object and hasattr(my_ipython_html_object, '_repr_html_'):
        raw_html_content = my_ipython_html_object._repr_html_()
        components.html(raw_html_content, height=300, scrolling=True)
    else:
        st.error("Unable to generate HTML preview for the given article.")
    
    
    components.html(raw_html_content, height=300, scrolling=True) # Adjust height and scrolling as needed



