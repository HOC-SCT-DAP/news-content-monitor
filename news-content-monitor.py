import requests
import csv
import os
import nltk
from datetime import datetime, timezone
from readability import Readability

# Ensure necessary NLP data is present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def get_reading_score(text):
    """
    Calculates Flesch Reading Ease.
    Requires at least 100 words for full accuracy, but we 
    provide a fallback for short titles/teasers.
    """
    word_count = len(text.split())
    if not text or word_count < 5:
        return 0.0
    try:
        r = Readability(text)
        # Flesch Reading Ease is the standard for UK 'Plain English'
        return round(r.flesch_reading_ease().score, 2)
    except:
        return 0.0

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

    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            writer.writerow([
                'News ID', 'Committee ID', 'Committee Name', 'Heading', 
                'Heading Word Count', 'Heading Readability', 'Teaser', 
                'Teaser Word Count', 'Teaser Readability', 'Date Published'
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

                    heading = val.get('heading', '').strip()
                    teaser = val.get('teaser', '').strip()
                    
                    h_words = len(heading.split())
                    t_words = len(teaser.split())
                    
                    writer.writerow([
                        news_id,
                        cttee_id,
                        cttee_name,
                        heading,
                        h_words,
                        get_reading_score(heading),
                        teaser,
                        t_words,
                        get_reading_score(teaser),
                        pub_date_str
                    ])
                    
            except Exception as e:
                print(f"  Skipping {cttee_name} due to error: {e}")

if __name__ == "__main__":
    # Example usage
    committees = {24: "Defence Committee", 62: "Justice Committee"}
    fetch_committee_news(committees, datetime(2026, 1, 1))