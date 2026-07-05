from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, get_db
from pipeline.runner import run_pipeline

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Listener Feedback Discovery Engine")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/dashboard")
def get_dashboard():
    return FileResponse("../frontend/index.html")

@app.get("/")
def read_root():
    return {"message": "Listener Feedback Discovery Engine API"}

@app.get("/runs", response_model=List[schemas.AnalysisRunResponse])
def get_runs(db: Session = Depends(get_db)):
    return db.query(models.AnalysisRun).order_by(models.AnalysisRun.date_run.desc()).all()

@app.get("/runs/{run_id}", response_model=schemas.AnalysisRunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)):
    return db.query(models.AnalysisRun).filter(models.AnalysisRun.id == run_id).first()

@app.post("/runs")
def trigger_run(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Create a new run record
    run = models.AnalysisRun(status="pending")
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Trigger the pipeline
    background_tasks.add_task(run_pipeline, run.id)
    return {"message": "Run triggered", "run_id": run.id}

@app.get("/feedback", response_model=List[schemas.FeedbackItemResponse])
def get_feedback(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.FeedbackItem).limit(limit).all()
