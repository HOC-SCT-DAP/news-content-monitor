import requests
import csv
import os
import nltk
from datetime import datetime, timezone
from readability import Readability
from bs4 import BeautifulSoup

# Ensure ALL necessary NLP data is present
# Added 'punkt_tab' which is required by newer NLTK versions
for resource in ['tokenizers/punkt', 'tokenizers/punkt_tab']:
    try:
        nltk.data.find(resource)
    except LookupError:
        nltk.download(resource.split('/')[-1])

def get_reading_score(text):
    """
    Calculates Flesch Reading Ease with safety checks.
    """
    if not text:
        return "No text"
    
    # Clean text slightly to help the tokenizer
    text = text.replace('“', '"').replace('”', '"').strip()
    
    word_count = len(text.split())
    if word_count < 100:
        return f"Under 100 words ({word_count})"
    
    try:
        r = Readability(text)
        return round(r.flesch_kincaid().score, 2)
    except Exception as e:
        # We print the error to the console so you can see exactly why it failed
        print(f"DEBUG: Readability error: {e}")
        return "Score Error"

def fetch_full_article_text(news_id):
    """
    Fetches the full article detail and strips HTML.
    """
    url = f"https://www.parliament.uk/api/content/news/{news_id}/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json().get('value', {})
        
        # Parliament API often uses 'intro' and 'body'
        raw_html = f"{data.get('intro', '')} {data.get('body', '')}"
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"  Error fetching details for ID {news_id}: {e}")
        return ""

def fetch_committee_news(committee_map, cutoff_date):
    if cutoff_date.tzinfo is None:
        cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)

    file_path = 'committee_news.csv'
    
    # Load existing IDs to avoid duplicates
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

                    heading = val.get('heading', '').strip()

                    # Fetch the FULL article text
                    full_text = fetch_full_article_text(news_id)
                    word_count = len(full_text.split())
                    
                    # Calculate score
                    readability_score = get_reading_score(full_text)
                    
                    writer.writerow([
                        news_id, cttee_id, cttee_name, heading,
                        word_count, readability_score, pub_date_str
                    ])
                    print(f"    Processed ID {news_id}: Score {readability_score}")
                    
            except Exception as e:
                print(f"  Skipping {cttee_name} due to error: {e}")

if __name__ == "__main__":
    # Example committees
    committees = {24: "Defence Committee", 62: "Justice Committee"}
    # Run for everything in 2025/2026
    fetch_committee_news(committees, datetime(2025, 1, 1))