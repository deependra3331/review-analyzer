from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FeedbackItemBase(BaseModel):
    source: str
    author: str
    text: str
    rating: Optional[int] = None
    url: Optional[str] = None
    date: datetime

class FeedbackItemResponse(FeedbackItemBase):
    id: int
    cluster_id: Optional[int] = None

    class Config:
        from_attributes = True # updated from orm_mode for Pydantic V2

class ClusterBase(BaseModel):
    theme_label: Optional[str] = None
    description: Optional[str] = None
    share_of_corpus: Optional[float] = None
    root_cause: Optional[str] = None
    user_segment: Optional[str] = None
    unmet_needs: Optional[str] = None
    jtbd_statement: Optional[str] = None

class ClusterResponse(ClusterBase):
    id: int
    run_id: int
    feedback_items: List[FeedbackItemResponse] = []

    class Config:
        from_attributes = True

class GlobalInsightResponse(BaseModel):
    id: int
    struggle_reason: Optional[str] = None
    common_frustrations: Optional[str] = None
    listening_behaviors: Optional[str] = None
    repeat_causes: Optional[str] = None
    segment_challenges: Optional[str] = None
    unmet_needs_summary: Optional[str] = None

    class Config:
        from_attributes = True

class AnalysisRunResponse(BaseModel):
    id: int
    date_run: datetime
    status: str
    clusters: List[ClusterResponse] = []
    global_insight: Optional[GlobalInsightResponse] = None

    class Config:
        from_attributes = True
