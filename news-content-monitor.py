import requests
import csv
import os
import nltk
from datetime import datetime, timezone
from readability import Readability
from bs4 import BeautifulSoup  # Added to clean HTML from the body text

# Ensure necessary NLP data is present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def get_reading_score(text):
    """
    Calculates Flesch Reading Ease.
    Readability library strictly requires 100+ words for accuracy.
    """
    if not text:
        return "No text"
    
    word_count = len(text.split())
    if word_count < 100:
        return f"Insufficient text ({word_count} words)"
    
    try:
        r = Readability(text)
        return round(r.flesch_reading_ease().score, 2)
    except Exception:
        return "Error calculating score"

def fetch_full_article_text(news_id):
    """
    Fetches the full article detail and strips HTML to get clean text.
    """
    url = f"https://www.parliament.uk/api/content/news/{news_id}/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json().get('value', {})
        
        # Combine intro and body HTML
        raw_html = f"{data.get('intro', '')} {data.get('body', '')}"
        
        # Use BeautifulSoup to get clean text without HTML tags
        soup = BeautifulSoup(raw_html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"  Error fetching details for ID {news_id}: {e}")
        return ""

def fetch_committee_news(committee_map, cutoff_date):
    if cutoff_date.tzinfo is None:
        cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)

    file_path = 'committee_news.csv'
    
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
                'Teaser', 'Full Text Word Count', 'Full Text Readability', 'Date Published'
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
                    
                    if not news_id:
                        continue
                    if news_id in existing_ids:
                        print(f"  -> Caught up on {cttee_name} (ID {news_id}).")
                        break
                    
                    pub_date_str = val.get('datePublished', '')
                    pub_date = datetime.fromisoformat(pub_date_str)
                    
                    if pub_date < cutoff_date:
                        continue

                    # 1. Get the basics from the feed
                    heading = val.get('heading', '').strip()
                    teaser = val.get('teaser', '').strip()

                    # 2. Fetch the FULL article text from the specific endpoint
                    print(f"    Fetching full content for news ID: {news_id}...")
                    full_text = fetch_full_article_text(news_id)
                    
                    # 3. Process the full text
                    word_count = len(full_text.split())
                    readability_score = get_reading_score(full_text)
                    
                    writer.writerow([
                        news_id,
                        cttee_id,
                        cttee_name,
                        heading,
                        teaser,
                        word_count,
                        readability_score,
                        pub_date_str
                    ])
                    
            except Exception as e:
                print(f"  Skipping {cttee_name} due to error: {e}")

if __name__ == "__main__":
    # Example usage: Look for news from the start of 2024 onwards
    committees = {24: "Defence Committee", 62: "Justice Committee"}
    fetch_committee_news(committees, datetime(2024, 1, 1))