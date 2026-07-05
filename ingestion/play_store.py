from google_play_scraper import Sort, reviews
from datetime import datetime

def fetch_play_store_reviews(app_id: str, max_reviews: int = 100):
    result, continuation_token = reviews(
        app_id,
        lang='en',
        country='us',
        sort=Sort.NEWEST,
        count=max_reviews
    )
    
    results = []
    for review in result:
        results.append({
            "source": "play_store",
            "author": review.get("userName", "unknown"),
            "date": review.get("at", datetime.utcnow()),
            "rating": review.get("score"),
            "text": review.get("content"),
            "url": review.get("reviewCreatedVersion")
        })
    return results
