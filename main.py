import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# Set up logging so you can see errors in your terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. API Client Setup
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "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"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = os.path.join(base_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

class IdeaRequest(BaseModel):
    idea: str
    domain: str
    audience: str
    monetization: str
    experience: str
    budget: str
    timeline: str

@app.post("/generate-roadmap")
async def generate_roadmap(data: IdeaRequest):
    if len(data.idea.strip()) < 5:
        raise HTTPException(status_code=400, detail="Idea is too short.")

    # Split into two smaller calls to avoid token limits
    try:
        # --- Call 1: Core analysis ---
        prompt1 = f"""You are a startup consultant. Analyze this startup idea and return ONLY valid JSON, no markdown.

Idea: {data.idea}
Industry: {data.domain}
Target Audience: {data.audience}
Monetization: {data.monetization}
Founder Experience: {data.experience}
Budget: {data.budget}
Timeline: {data.timeline}

Return this exact JSON structure:
{{
  "roadmap": ["step 1", "step 2", "step 3", "step 4", "step 5"],
  "swot": {{
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "opportunities": ["opportunity 1", "opportunity 2"],
    "threats": ["threat 1", "threat 2"]
  }},
  "funding_plan": {{
    "phase1_bootstrapped": "description of bootstrapping phase",
    "phase2_preseed": "description of pre-seed phase"
  }},
  "core_features": [
    {{"name": "Feature Name", "desc": "Feature description"}},
    {{"name": "Feature Name", "desc": "Feature description"}},
    {{"name": "Feature Name", "desc": "Feature description"}}
  ],
  "avoid_feature": "description of what to avoid building in V1",
  "feasibility": {{
    "tech_complexity": 3,
    "market_demand": 4,
    "resource_match": 3,
    "legal_barriers": 2,
    "final_percentage": 65
  }},
  "idea_analysis": {{
    "market_potential": "Brief market potential summary"
  }}
}}"""

        # --- Call 2: Competitors, mentors, validation ---
        prompt2 = f"""You are a startup consultant. For this startup idea, return ONLY valid JSON, no markdown.

Idea: {data.idea}
Industry: {data.domain}
Target Audience: {data.audience}

Return this exact JSON structure:
{{
  "competitors": [
    {{"name": "Competitor Name", "strength": "their main strength", "weakness": "their main weakness"}},
    {{"name": "Competitor Name", "strength": "their main strength", "weakness": "their main weakness"}},
    {{"name": "Competitor Name", "strength": "their main strength", "weakness": "their main weakness"}}
  ],
  "validation_plan": ["step 1", "step 2", "step 3", "step 4"],
  "matched_mentors": [
    {{"name": "Mentor Name", "role": "Mentor Title", "bio": "Short bio", "fee": "$X/hr"}},
    {{"name": "Mentor Name", "role": "Mentor Title", "bio": "Short bio", "fee": "$X/hr"}}
  ]
}}"""

        logger.info(f"Calling Groq API for idea: {data.idea[:50]}...")

        resp1 = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt1}],
            response_format={"type": "json_object"},
            max_tokens=2000,
        )

        resp2 = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt2}],
            response_format={"type": "json_object"},
            max_tokens=1500,
        )

        result1 = json.loads(resp1.choices[0].message.content)
        result2 = json.loads(resp2.choices[0].message.content)

        # Merge both responses
        combined = {**result1, **result2}
        logger.info("Successfully generated roadmap.")
        return combined

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Groq API error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
