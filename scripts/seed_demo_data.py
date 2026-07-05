import sys
import os
from datetime import datetime, timedelta
import random

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import SessionLocal, engine
import models

# Spotify-like sample reviews with clear themes
SAMPLE_REVIEWS = [
    {"text": "I just want to listen to music, but my home screen is full of podcasts I don't care about.", "rating": 2, "source": "app_store"},
    {"text": "Stop forcing podcasts down my throat! Let me disable the podcast tab completely.", "rating": 1, "source": "play_store"},
    {"text": "The UI is so cluttered now. It used to be a great music app, now it's a messy audio app.", "rating": 3, "source": "app_store"},
    {"text": "Why do podcasts autoplay after my music playlist finishes? So annoying.", "rating": 2, "source": "reddit"},
    
    {"text": "The shuffle button plays the same 20 songs from my 500 song playlist every time.", "rating": 2, "source": "play_store"},
    {"text": "Is shuffle broken? It just loops my recently played songs instead of actually shuffling.", "rating": 1, "source": "app_store"},
    {"text": "I miss true random shuffle. This 'smart shuffle' is terrible and just plays what it thinks I want.", "rating": 2, "source": "reddit"},
    
    {"text": "Another price increase? It's getting too expensive for just music.", "rating": 2, "source": "play_store"},
    {"text": "Can't afford premium anymore. The free version has too many ads to be usable.", "rating": 1, "source": "app_store"},
    
    {"text": "I actually really like the AI DJ feature, it finds great new tracks for me.", "rating": 5, "source": "app_store"},
    {"text": "Discover Weekly is the only reason I stay. It knows my taste perfectly.", "rating": 4, "source": "play_store"},
    
    {"text": "Downloaded songs disappear randomly when I'm offline. Ruins my commute.", "rating": 1, "source": "app_store"},
    {"text": "Offline mode simply doesn't work half the time.", "rating": 2, "source": "play_store"},
]

def seed_data():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    if db.query(models.FeedbackItem).count() > 0:
        print("Database already contains data. Skipping seed.")
        return

    print("Seeding demo data...")
    for item in SAMPLE_REVIEWS:
        days_ago = random.randint(1, 30)
        feedback = models.FeedbackItem(
            source=item["source"],
            author=f"user_{random.randint(1000, 9999)}",
            date=datetime.utcnow() - timedelta(days=days_ago),
            rating=item["rating"],
            text=item["text"]
        )
        db.add(feedback)
    
    db.commit()
    print(f"Seeded {len(SAMPLE_REVIEWS)} feedback items successfully!")
    db.close()

if __name__ == "__main__":
    seed_data()
