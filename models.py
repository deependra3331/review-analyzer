from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    date_run = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending") # 'pending', 'completed', 'failed'
    
    clusters = relationship("Cluster", back_populates="analysis_run")
    global_insight = relationship("GlobalInsight", back_populates="analysis_run", uselist=False)

class GlobalInsight(Base):
    __tablename__ = "global_insights"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"), unique=True)
    
    struggle_reason = Column(Text, nullable=True)
    common_frustrations = Column(Text, nullable=True)
    listening_behaviors = Column(Text, nullable=True)
    repeat_causes = Column(Text, nullable=True)
    segment_challenges = Column(Text, nullable=True)
    unmet_needs_summary = Column(Text, nullable=True)
    
    analysis_run = relationship("AnalysisRun", back_populates="global_insight")

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    
    # LLM Synthesized details
    theme_label = Column(String, nullable=True)
    description = Column(String, nullable=True)
    share_of_corpus = Column(Float, nullable=True) # 0.0 to 1.0
    root_cause = Column(Text, nullable=True)
    user_segment = Column(String, nullable=True)
    unmet_needs = Column(Text, nullable=True) # Comma separated or JSON string
    jtbd_statement = Column(Text, nullable=True)
    
    analysis_run = relationship("AnalysisRun", back_populates="clusters")
    feedback_items = relationship("FeedbackItem", back_populates="cluster")

class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True) # e.g., 'app_store', 'play_store', 'reddit', 'csv'
    author = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    rating = Column(Integer, nullable=True)
    text = Column(Text)
    url = Column(String, nullable=True)
    
    # After clustering, we assign a cluster_id
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    cluster = relationship("Cluster", back_populates="feedback_items")
