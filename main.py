from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import json

client = Groq(api_key="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")

app = FastAPI()

# Fixes the connection errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class IdeaRequest(BaseModel):
    idea: str
    domain: str
    audience: str = "Broad"
    monetization: str = "Subscription"
    experience: str = "Beginner"
    budget: str = "Low"
    timeline: str = "Medium"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-roadmap")
async def generate_roadmap(data: IdeaRequest):
    try:
        prompt = f"""Analyze startup idea: {data.idea}. Domain: {data.domain}. Audience: {data.audience}. Monetization: {data.monetization}. Experience: {data.experience}. Budget: {data.budget}. Timeline: {data.timeline}.
Return JSON only. Strict requirements:
1. FEASIBILITY CALCULATION (Weighted Logic): Include "feasibility": {{"base": 40, "tech_complexity": int 1-5, "market_demand": int 1-5, "resource_match": int 1-5, "legal_barriers": int 1-5, "tech_complexity_points": float, "market_demand_points": float, "resource_match_points": float, "legal_barriers_points": float, "final_percentage": float}}. Calculate points: tech(30%), market(30%), resource(20%), legal(20%). final = 40 + ((total_points/5) * 60).
2. SWOT ANALYSIS: Include "swot": {{"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}}. Strengths must fuel Opportunities; Weaknesses must create Threats. Use quantified domain metrics.
3. COMPETITOR LANDSCAPE: Include "competitors": [{{"name": "real company 2025/2026", "competitor_wins": "string", "competitor_vulnerable": "string"}}] (list of 3). 
4. MARKET SENTIMENT: Include "market_sentiment": {{"trends": [], "critical_failure_point": "string"}}. Use 2024-2026 trends. Cite [Basis: source]. If unknown, state "Insufficient real-world data to verify".
5. EXECUTION PLAN: Include "validation_plan": [list of 5 highly specific steps to validate MVP before coding].
6. EXPERT MATCHES: Include "matched_mentors": [{{"name": "string", "role": "string", "fee": "string", "bio": "string"}}] (list of 2 specific mentors needed).
7. MVP FEATURES: Include "core_features": [{{"name": "string", "desc": "string"}}] (list of 3 features) and "avoid_feature": "string".
8. FUNDING STRATEGY: Include "funding_plan": {{"phase1_bootstrapped": "string", "phase2_preseed": "string"}}.
"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        
        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}