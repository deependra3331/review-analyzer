from app_store_scraper import AppStore
from datetime import datetime

def fetch_app_store_reviews(app_name: str, app_id: int, max_reviews: int = 100):
    app = AppStore(country='us', app_name=app_name, app_id=app_id)
    app.review(how_many=max_reviews)
    
    results = []
    for review in app.reviews:
        results.append({
            "source": "app_store",
            "author": review.get("userName", "unknown"),
            "date": review.get("date", datetime.utcnow()),
            "rating": review.get("rating"),
            "text": review.get("review"),
            "url": None
        })
    return results
