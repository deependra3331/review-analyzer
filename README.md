# Review Analyzer — Listener Feedback Discovery Engine

A full-stack AI-powered tool that scrapes Spotify user reviews from the App Store and Google Play Store, clusters them semantically using sentence-transformers + scikit-learn, and synthesizes actionable product insights using Groq LLaMA-3 — all displayed in a beautiful real-time dashboard.

---

## Features

- Multi-source ingestion — Fetches reviews from Apple App Store and Google Play Store automatically
- Semantic clustering — Embeds reviews with sentence-transformers and clusters with scikit-learn KMeans
- LLM synthesis — Uses Groq llama-3.1-8b-instant to generate theme labels, root causes, user segments, unmet needs, and JTBD statements per cluster
- Global insights — Synthesizes cross-cluster executive summaries answering key PM questions
- Live dashboard — Dark-themed, Spotify-styled frontend with animated cards, evidence drawers, and a run trigger button
- SQLite persistence — All runs, clusters, and feedback items stored locally

---

## Project Structure

```
review-analyzer/
├── main.py                  # FastAPI app entry point
├── models.py                # SQLAlchemy ORM models
├── schemas.py               # Pydantic response schemas
├── database.py              # DB engine & session setup
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── frontend/
│   ├── index.html           # Dashboard UI (Tailwind CSS)
│   └── app.js               # Frontend JS — API calls & rendering
├── ingestion/
│   ├── app_store.py         # Apple App Store scraper
│   └── play_store.py        # Google Play Store scraper
└── pipeline/
    ├── runner.py             # Orchestrates the full analysis pipeline
    ├── embed_cluster.py      # Sentence embedding + KMeans clustering
    └── llm_synthesis.py      # Groq LLM prompt engineering & synthesis
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/deependra3331/review-analyzer.git
cd review-analyzer
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your Groq API key (free at https://console.groq.com):

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Note: If no Groq API key is provided, the pipeline will still run using mocked LLM responses so you can see the UI working.

### 5. Run the server

```bash
uvicorn main:app --reload --port 8000
```

### 6. Open the dashboard

Navigate to: http://localhost:8000/dashboard

> The root URL http://localhost:8000/ returns an API status message. The dashboard lives at /dashboard.

---

## API Endpoints

| Method | Endpoint          | Description                             |
|--------|-------------------|-----------------------------------------|
| GET    | /                 | API health check                        |
| GET    | /dashboard        | Serves the frontend dashboard           |
| GET    | /runs             | List all analysis runs                  |
| GET    | /runs/{run_id}    | Get full details for a specific run     |
| POST   | /runs             | Trigger a new analysis pipeline run     |
| GET    | /feedback         | List raw feedback items (limit: 100)    |

---

## Tech Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Backend    | FastAPI + Uvicorn                               |
| Database   | SQLite via SQLAlchemy                           |
| Scraping   | app-store-scraper, google-play-scraper          |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2)        |
| Clustering | scikit-learn KMeans                             |
| LLM        | Groq Cloud — LLaMA 3.1 8B Instant              |
| Frontend   | Vanilla HTML/JS + Tailwind CSS                  |

---

## Environment Variables

| Variable      | Required | Description                                                               |
|---------------|----------|---------------------------------------------------------------------------|
| GROQ_API_KEY  | Optional | Groq Cloud API key for LLM synthesis. Falls back to mock data if not set. |
| DATABASE_URL  | Optional | SQLAlchemy DB URL. Defaults to sqlite:///./feedback.db                    |

---

## License

MIT License — feel free to fork, modify, and build on it.
