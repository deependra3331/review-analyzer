from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import models
from pipeline.embed_cluster import cluster_feedback
from pipeline.llm_synthesis import synthesize_cluster, synthesize_global_run
from database import SessionLocal

# Rich fallback demo data used when live scraping is blocked/unavailable
DEMO_REVIEWS = [
    {"source": "app_store",  "author": "user_1021", "rating": 2, "text": "I just want to listen to music, but my home screen is full of podcasts I don't care about."},
    {"source": "play_store", "author": "user_2345", "rating": 1, "text": "Stop forcing podcasts down my throat! Let me disable the podcast tab completely."},
    {"source": "app_store",  "author": "user_3812", "rating": 3, "text": "The UI is so cluttered now. It used to be a great music app, now it's a messy audio app."},
    {"source": "reddit",     "author": "user_4901", "rating": 2, "text": "Why do podcasts autoplay after my music playlist finishes? So annoying."},
    {"source": "app_store",  "author": "user_5543", "rating": 1, "text": "Removed the ability to sort playlists by title. I have 300 songs and now I can't find anything."},
    {"source": "play_store", "author": "user_6234", "rating": 2, "text": "The shuffle button plays the same 20 songs from my 500 song playlist every time."},
    {"source": "app_store",  "author": "user_7112", "rating": 1, "text": "Is shuffle broken? It just loops my recently played songs instead of actually shuffling."},
    {"source": "reddit",     "author": "user_8903", "rating": 2, "text": "I miss true random shuffle. This 'smart shuffle' is terrible and just plays what it thinks I want."},
    {"source": "play_store", "author": "user_9021", "rating": 2, "text": "Another price increase? It's getting too expensive for just music."},
    {"source": "app_store",  "author": "user_1134", "rating": 1, "text": "Can't afford premium anymore. The free version has too many ads to be usable."},
    {"source": "play_store", "author": "user_2278", "rating": 2, "text": "Raised the price again with zero new features. Time to cancel."},
    {"source": "app_store",  "author": "user_3391", "rating": 5, "text": "I actually really like the AI DJ feature, it finds great new tracks for me."},
    {"source": "play_store", "author": "user_4512", "rating": 4, "text": "Discover Weekly is the only reason I stay. It knows my taste perfectly."},
    {"source": "app_store",  "author": "user_5623", "rating": 5, "text": "Daily Mix playlists are incredible, feels like it reads my mind."},
    {"source": "reddit",     "author": "user_6734", "rating": 4, "text": "Wrapped is fun every year but I wish the personalization carried through the whole year better."},
    {"source": "app_store",  "author": "user_7845", "rating": 1, "text": "Downloaded songs disappear randomly when I'm offline. Ruins my commute."},
    {"source": "play_store", "author": "user_8956", "rating": 2, "text": "Offline mode simply doesn't work half the time."},
    {"source": "app_store",  "author": "user_9067", "rating": 1, "text": "My downloaded playlists vanished after the latest update. 10GB of music gone."},
    {"source": "play_store", "author": "user_1178", "rating": 2, "text": "Battery drain is insane with the latest update. Drains 30% just streaming for an hour."},
    {"source": "app_store",  "author": "user_2289", "rating": 1, "text": "App crashes every time I try to open a playlist. Unusable since the last update."},
    {"source": "reddit",     "author": "user_3390", "rating": 2, "text": "The Bluetooth connection keeps dropping since the update. Never had this issue before."},
    {"source": "play_store", "author": "user_4401", "rating": 3, "text": "Recommendations have gotten worse lately. It keeps suggesting the same artists I already follow."},
    {"source": "app_store",  "author": "user_5512", "rating": 2, "text": "I want to explore new genres but it only shows me what I've already heard. The algorithm is stuck."},
    {"source": "reddit",     "author": "user_6623", "rating": 1, "text": "Discovery is broken. I've been listening to jazz for a year and it still recommends pop to me."},
    {"source": "play_store", "author": "user_7734", "rating": 4, "text": "Love the app overall but crossfade between songs is broken, there's always an awkward gap."},
    {"source": "app_store",  "author": "user_8845", "rating": 3, "text": "Car mode is great but it doesn't remember my last position in a podcast episode."},
    {"source": "reddit",     "author": "user_9956", "rating": 2, "text": "Sleep timer used to work perfectly. Now it cuts off mid-song instead of at the end."},
]


def get_fallback_items(db):
    """Insert and return demo feedback items if no data exists."""
    existing_texts = {item.text for item in db.query(models.FeedbackItem).all()}
    new_count = 0
    for item in DEMO_REVIEWS:
        if item["text"] not in existing_texts:
            days_ago = random.randint(1, 60)
            db.add(models.FeedbackItem(
                source=item["source"],
                author=item["author"],
                date=datetime.utcnow() - timedelta(days=days_ago),
                rating=item["rating"],
                text=item["text"],
            ))
            existing_texts.add(item["text"])
            new_count += 1
    if new_count:
        db.commit()
        print(f"Loaded {new_count} demo feedback items (live scraping unavailable).")
    return db.query(models.FeedbackItem).all()


def run_pipeline(run_id: int):
    db = SessionLocal()
    try:
        run = db.query(models.AnalysisRun).filter(models.AnalysisRun.id == run_id).first()
        if not run:
            return

        run.status = "running"
        db.commit()

        # 1. Attempt to fetch live reviews
        print("Fetching live reviews...")
        app_store_items = []
        play_store_items = []

        try:
            from ingestion.app_store import fetch_app_store_reviews
            app_store_items = fetch_app_store_reviews("spotify-music-and-podcasts", "324684580", 50)
            print(f"App Store: fetched {len(app_store_items)} reviews")
        except Exception as e:
            print(f"App Store scraping failed (will use demo data): {e}")

        try:
            from ingestion.play_store import fetch_play_store_reviews
            play_store_items = fetch_play_store_reviews("com.spotify.music", 50)
            print(f"Play Store: fetched {len(play_store_items)} reviews")
        except Exception as e:
            print(f"Play Store scraping failed (will use demo data): {e}")

        # 2. Insert live reviews into DB (deduplicate by text)
        existing_texts = {item.text for item in db.query(models.FeedbackItem).all()}
        for item_data in app_store_items + play_store_items:
            text = item_data.get("text") or ""
            if text and text not in existing_texts:
                db.add(models.FeedbackItem(
                    source=item_data.get("source", "unknown"),
                    author=item_data.get("author", "unknown"),
                    date=item_data.get("date", datetime.utcnow()),
                    rating=item_data.get("rating"),
                    text=text,
                    url=item_data.get("url"),
                ))
                existing_texts.add(text)
        db.commit()

        # 3. Get all feedback — fall back to demo data if none available
        items = db.query(models.FeedbackItem).all()
        if not items:
            print("No live data available — loading demo data...")
            items = get_fallback_items(db)

        if not items:
            run.status = "failed: no data"
            db.commit()
            return

        # 4. Cluster the feedback
        print(f"Clustering {len(items)} feedback items...")
        clusters_map = cluster_feedback(items)
        total_items = len(items)

        for label, cluster_items in clusters_map.items():
            synthesis = synthesize_cluster(cluster_items)

            cluster_record = models.Cluster(
                run_id=run.id,
                theme_label=synthesis.get("theme_label", "Unknown Theme"),
                description=synthesis.get("description", ""),
                share_of_corpus=len(cluster_items) / total_items,
                root_cause=synthesis.get("root_cause", ""),
                user_segment=synthesis.get("user_segment", ""),
                unmet_needs=synthesis.get("unmet_needs", ""),
                jtbd_statement=synthesis.get("jtbd_statement", "")
            )
            db.add(cluster_record)
            db.flush()

            for item in cluster_items:
                item.cluster_id = cluster_record.id

        # 5. Global synthesis
        print("Running global synthesis...")
        clusters_for_global = [
            {
                "theme_label": c.theme_label,
                "description": c.description,
                "root_cause": c.root_cause,
                "user_segment": c.user_segment
            } for c in db.query(models.Cluster).filter(models.Cluster.run_id == run.id).all()
        ]

        global_answers = synthesize_global_run(clusters_for_global)
        global_record = models.GlobalInsight(
            run_id=run.id,
            struggle_reason=global_answers.get("struggle_reason"),
            common_frustrations=global_answers.get("common_frustrations"),
            listening_behaviors=global_answers.get("listening_behaviors"),
            repeat_causes=global_answers.get("repeat_causes"),
            segment_challenges=global_answers.get("segment_challenges"),
            unmet_needs_summary=global_answers.get("unmet_needs_summary")
        )
        db.add(global_record)

        run.status = "completed"
        db.commit()
        print(f"Pipeline completed successfully for run {run_id}.")

    except Exception as e:
        print(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        run = db.query(models.AnalysisRun).filter(models.AnalysisRun.id == run_id).first()
        if run:
            run.status = "failed"
            db.commit()
    finally:
        db.close()
