import requests
import csv
import os
import nltk
from datetime import datetime, timezone
from readability import Readability
from bs4 import BeautifulSoup

# Ensure necessary NLP data is present
for resource in ['tokenizers/punkt', 'tokenizers/punkt_tab']:
    try:
        nltk.data.find(resource)
    except LookupError:
        nltk.download(resource.split('/')[-1])

def get_reading_score(text):
    """
    Calculates Flesch Reading Ease for the full text.
    Returns 0.00 if text is too short (<100 words) or if an error occurs.
    """
    if not text:
        return 0.00
    
    word_count = len(text.split())
    if word_count < 100:
        return 0.00
    
    try:
        # Standardize quotes to help the tokenizer
        clean_text = text.replace('“', '"').replace('”', '"').strip()
        r = Readability(clean_text)
        return round(r.flesch_kincaid().score, 2)
    except Exception:
        # Fallback to 0.00 on any library error
        return 0.00

def fetch_full_article_text(news_id):
    """
    Pulls full article details and strips HTML tags.
    """
    url = f"https://www.parliament.uk/api/content/news/{news_id}/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json().get('value', {})
        
        # Combine intro and body for the full text analysis
        raw_html = f"{data.get('intro', '')} {data.get('body', '')}"
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        return soup.get_text(separator=' ', strip=True)
    except Exception:
        return ""

def fetch_committee_news(committee_map, cutoff_date):
    if cutoff_date.tzinfo is None:
        cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)

    file_path = 'docs/committee_news.csv'
    
    existing_ids = set()
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) 
            existing_ids = {row[0].strip() for row in reader if row}

    file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 0

    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        if not file_exists:
            writer.writerow([
                'News ID', 'Committee ID', 'Committee Name', 'Heading', 
                'Heading Word Count', 'Teaser Word Count', 
                'Full Text Word Count', 'Full Text Readability', 'Date Published'
            ])

        for cttee_id, cttee_name in committee_map.items():
            print(f"Syncing: {cttee_name}...")
            url = f"https://www.parliament.uk/api/content/committee/{cttee_id}/news/"
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    val = item.get('value', {})
                    news_id = str(val.get('id', ''))
                    
                    if not news_id or news_id in existing_ids:
                        continue
                    
                    pub_date_str = val.get('datePublished', '')
                    pub_date = datetime.fromisoformat(pub_date_str)
                    
                    if pub_date < cutoff_date:
                        continue

                    # 1. Gather heading and teaser metadata
                    heading = val.get('heading', '').strip()
                    teaser = val.get('teaser', '').strip()
                    
                    h_word_count = len(heading.split())
                    t_word_count = len(teaser.split())

                    # 2. Fetch full article for readability scoring
                    full_text = fetch_full_article_text(news_id)
                    ft_word_count = len(full_text.split())
                    readability_score = get_reading_score(full_text)
                    
                    writer.writerow([
                        news_id,
                        cttee_id,
                        cttee_name,
                        heading,
                        h_word_count,
                        t_word_count,
                        ft_word_count,
                        readability_score,
                        pub_date_str
                    ])
                    
            except Exception as e:
                print(f"  Skipping {news_id} due to error: {e}")

if __name__ == "__main__":
    committees = {
        365: "Business and Trade Committee",
        378: "Culture, Media and Sport Committee",
        24: "Defence Committee",
        203: "Education Committee",
        664: "Energy Security and Net Zero Committee",
        52: "Environment, Food and Rural Affairs Committee",
        78: "Foreign Affairs Committee",
        81: "Health and Social Care Committee",
        83: "Home Affairs Committee",
        17: "Housing, Communities and Local Government Committee",
        98: "International Development Committee",
        102: "Justice Committee",
        120: "Northern Ireland Affairs Committee",
        135: "Science, Innovation and Technology Committee",
        136: "Scottish Affairs Committee",
        153: "Transport Committee",
        158: "Treasury Committee",
        162: "Welsh Affairs Committee",
        328: "Women and Equalities Committee",
        164: "Work and Pensions Committee"
    }
    
    # Adjust date as needed
    fetch_committee_news(committees, datetime(2025, 1, 1))