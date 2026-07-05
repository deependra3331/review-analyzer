from sqlalchemy.orm import Session
from datetime import datetime
import models
from pipeline.embed_cluster import cluster_feedback
from pipeline.llm_synthesis import synthesize_cluster, synthesize_global_run
from ingestion.app_store import fetch_app_store_reviews
from ingestion.play_store import fetch_play_store_reviews

from database import SessionLocal

def run_pipeline(run_id: int):
    db = SessionLocal()
    try:
        run = db.query(models.AnalysisRun).filter(models.AnalysisRun.id == run_id).first()
        if not run:
            return
            
        run.status = "running"
        db.commit()
        
        # 1. Fetch live data for Spotify
        print("Fetching live reviews...")
        app_store_items = fetch_app_store_reviews("spotify-music-and-podcasts", "324684580", 50)
        play_store_items = fetch_play_store_reviews("com.spotify.music", 50)
        
        # 2. Insert into DB if not exists (simple deduplication by text hash/content)
        existing_texts = {item.text for item in db.query(models.FeedbackItem).all()}
        new_items = []
        for item_data in app_store_items + play_store_items:
            if item_data["text"] not in existing_texts:
                new_item = models.FeedbackItem(
                    source=item_data["source"],
                    text=item_data["text"],
                    date_posted=item_data.get("date_posted", datetime.utcnow()),
                    metadata_json=item_data.get("metadata", {})
                )
                db.add(new_item)
                existing_texts.add(new_item.text)
                
        db.commit()
        
        # 3. Get all items (or just the latest ones, but for now we cluster all to get a holistic view)
        items = db.query(models.FeedbackItem).all()
        if not items:
            run.status = "failed: no data"
            db.commit()
            return
            
        print("Clustering items...")
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
                
        # 5. Global Synthesis
        print("Running global synthesis...")
        # Prepare list of clusters for global synthesis
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
        
    except Exception as e:
        print(f"Pipeline error: {e}")
        db.rollback()
        run = db.query(models.AnalysisRun).filter(models.AnalysisRun.id == run_id).first()
        if run:
            run.status = "failed"
            db.commit()
    finally:
        db.close()
