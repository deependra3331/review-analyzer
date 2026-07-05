import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Ensure GROQ_API_KEY is set in environment
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "mock_key_for_testing"))

PROMPT_TEMPLATE = """
You are an expert Product Manager analyzing user feedback for a music streaming app.
Analyze the following cluster of user feedback reviews.

Reviews:
{reviews}

Synthesize the feedback into the following JSON format ONLY. Do not include markdown formatting or extra text outside the JSON.
{{
    "theme_label": "Short, catchy label (max 5 words)",
    "description": "A one-sentence description of what users are experiencing.",
    "root_cause": "Hypothesis on why this is happening.",
    "user_segment": "Likely user segment driving this (e.g., 'Power Users', 'Free Tier Listeners', 'Podcast Haters').",
    "unmet_needs": "What need is not being met? (Comma separated string).",
    "jtbd_statement": "When [situation], I want [motivation], so I can [outcome]."
}}
"""

def synthesize_cluster(cluster_items):
    """
    Calls Groq to summarize a cluster of reviews.
    """
    reviews_text = "\n".join([f"- {item.text}" for item in cluster_items])
    prompt = PROMPT_TEMPLATE.format(reviews=reviews_text)
    
    if not client.api_key or client.api_key in ["mock_key_for_testing", "your_api_key_here", ""]:
        # Return mock data if no key is provided
        # We try to create a semi-realistic mock based on the first item's text
        sample_text = cluster_items[0].text if cluster_items else "No text"
        return {
            "theme_label": f"Theme: {sample_text[:15]}...",
            "description": "This is a mocked description because no Groq API key was found.",
            "root_cause": "Mocked root cause analysis.",
            "user_segment": "General Audience",
            "unmet_needs": "Mocked unmet needs",
            "jtbd_statement": "When using the app, I want it to work, so I can be happy."
        }
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        response_json = completion.choices[0].message.content
        return json.loads(response_json)
    except Exception as e:
        print(f"Groq API Error: {e}")
        return {
            "theme_label": "Error processing cluster",
            "description": str(e),
            "root_cause": "API Error",
            "user_segment": "Unknown",
            "unmet_needs": "N/A",
            "jtbd_statement": "N/A"
        }

GLOBAL_PROMPT_TEMPLATE = """
You are an expert Product Manager analyzing user feedback for Spotify.
Based on the following clustered themes extracted from recent feedback, answer these specific questions:
1. Why do users struggle to discover new music?
2. What are the most common frustrations with recommendations?
3. What listening behaviors are users trying to achieve?
4. What causes users to repeatedly listen to the same content?
5. Which user segments experience different discovery challenges?
6. What unmet needs emerge consistently across reviews?

Clusters:
{clusters}

Output ONLY valid JSON in this exact format:
{{
    "struggle_reason": "Answer to Q1",
    "common_frustrations": "Answer to Q2",
    "listening_behaviors": "Answer to Q3",
    "repeat_causes": "Answer to Q4",
    "segment_challenges": "Answer to Q5",
    "unmet_needs_summary": "Answer to Q6"
}}
"""

def synthesize_global_run(clusters_data):
    """
    Synthesize answers to overarching product questions from the clustered themes.
    """
    if not clusters_data:
        return {}

    cluster_summaries = []
    for c in clusters_data:
        cluster_summaries.append(f"Theme: {c.get('theme_label')}\nDesc: {c.get('description')}\nRoot Cause: {c.get('root_cause')}\nSegment: {c.get('user_segment')}")
    
    prompt = GLOBAL_PROMPT_TEMPLATE.format(clusters="\n\n".join(cluster_summaries))
    
    if not client.api_key or client.api_key in ["mock_key_for_testing", "your_api_key_here", ""]:
        return {
            "struggle_reason": "Mocked: Users find discovery playlists repetitive.",
            "common_frustrations": "Mocked: Recommendations don't match current mood.",
            "listening_behaviors": "Mocked: Passive listening while working.",
            "repeat_causes": "Mocked: Familiarity and low cognitive load.",
            "segment_challenges": "Mocked: Power users want more control; casual users want better auto-curation.",
            "unmet_needs_summary": "Mocked: Better mood-based filtering."
        }
        
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Global Synthesis Error: {e}")
        return {
            "struggle_reason": "Error",
            "common_frustrations": "Error",
            "listening_behaviors": "Error",
            "repeat_causes": "Error",
            "segment_challenges": "Error",
            "unmet_needs_summary": "Error"
        }
