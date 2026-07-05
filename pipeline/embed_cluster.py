from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np

# Load model once
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print("Failed to load sentence-transformers. Will mock embeddings if needed.", e)
    model = None

def get_embeddings(texts):
    if not model:
        # Mock embeddings for demo if model fails to load
        return np.random.rand(len(texts), 384)
    return model.encode(texts)

def cluster_feedback(feedback_items):
    """
    Takes a list of models.FeedbackItem objects, embeds their text,
    and assigns a cluster ID to each.
    """
    if not feedback_items:
        return {}
        
    texts = [item.text for item in feedback_items]
    embeddings = get_embeddings(texts)
    
    # Estimate number of clusters (e.g., 1 cluster per 5-10 items, max 20, min 2)
    n_clusters = max(2, min(len(feedback_items) // 3, 10))
    if len(feedback_items) < n_clusters:
        n_clusters = len(feedback_items)
        
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(embeddings)
    
    # Map cluster_label to list of feedback items
    clusters_map = {}
    for i, label in enumerate(labels):
        if label not in clusters_map:
            clusters_map[label] = []
        clusters_map[label].append(feedback_items[i])
        
    return clusters_map
