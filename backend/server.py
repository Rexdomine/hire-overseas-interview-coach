import os, json, re
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name('.env'))
load_dotenv('/opt/data/.env')

APP_NAME = 'Hire Overseas Interview Coach — Hermes Brain'
PORT = int(os.getenv('PORT', '8791'))
BRAIN_TOKEN = os.getenv('HERMES_BRAIN_TOKEN', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
MODEL = os.getenv('INTERVIEW_COACH_MODEL', 'openai/gpt-oss-20b:free')

app = FastAPI(title=APP_NAME, version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['GET','POST','OPTIONS'], allow_headers=['*'])

class CoachRequest(BaseModel):
    problem: str = Field(..., min_length=10)
    tech_stack: str = 'FastAPI + Pydantic + pytest + Swagger'
    interview_stage: str = 'real-world implementation assessment'
    include_codex_prompts: bool = True

SYSTEM_PROMPT = """You are Groot, Rex's practical AI interview coach for a live real-world implementation assessment.
The interviewer allows and recommends GenAI. Rex will paste a problem statement. Your job is to produce a tailored, end-to-end guide for building that exact problem, not generic advice.

Return ONLY valid JSON with these exact keys. All values must be strings or arrays of strings, no nested objects:
{
  "source": "Hermes/Groot AI Brain",
  "problem_understanding": "specific restatement of the pasted problem",
  "opening_script": "natural first-person words Rex should say before coding",
  "clarifying_questions": ["3-5 precise questions tailored to the problem"],
  "assumptions_to_state": ["assumptions Rex can state if interviewer does not answer"],
  "mvp_scope": ["smallest end-to-end features to implement live"],
  "recommended_entities": ["entities/tables/classes with key fields, tailored to the problem"],
  "api_endpoints": ["HTTP method path - exact purpose and request/response notes"],
  "implementation_steps": ["ordered coding steps with files to edit"],
  "codex_start_prompt": "a ready-to-paste Codex prompt tailored to the problem",
  "test_plan": ["happy path and edge cases with concrete sample values where possible"],
  "codex_test_prompt": "ready-to-paste test-generation prompt tailored to the problem",
  "review_prompt": "ready-to-paste review prompt tailored to the problem",
  "what_to_say_while_building": ["short natural lines Rex can say at each stage"],
  "production_readiness": ["specific production improvements relevant to the problem"],
  "final_summary_script": "confident closing script Rex can say",
  "time_box_plan": ["what to do at 10, 25, 40, 55 minutes"],
  "danger_zones": ["mistakes to avoid for this exact problem"]
}

Rules:
- Tailor everything to the pasted problem, including entities, endpoints, tests, and scripts.
- Use FastAPI unless the user requests another stack.
- Keep it interview-realistic: build a small working MVP first.
- Assume Rex is using VS Code + Codex visibly, not hidden autonomous agents.
- Add exact words Rex can say to sound confident.
- If the problem involves AI, include provider interface, guardrails, logging, and human fallback.
- If the problem involves webhook/automation, include idempotency, signature verification, retries, and event logs.
- If the problem involves CRUD/workflow, include statuses, validation, and not-found handling.
"""

def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    return text.strip()

def fallback_solution(problem: str, tech_stack: str) -> Dict[str, Any]:
    p = problem.lower()
    is_ai = any(w in p for w in ['ai','chatbot','llm','summar','document','recommendation'])
    is_webhook = any(w in p for w in ['webhook','event','callback','payment','stripe','third-party'])
    main = 'request'
    if 'ticket' in p: main='ticket'
    elif 'task' in p: main='task'
    elif 'course' in p or 'student' in p: main='student/course record'
    elif 'order' in p: main='order'
    elif 'document' in p: main='document job'
    slug = main.replace('/', '-').replace(' ', '-') + 's'
    endpoints = [f'POST /{slug} - create a new {main} with validation', f'GET /{slug} - list records for demo/testing', f'GET /{slug}/{{id}} - fetch one record or return 404', f'PATCH /{slug}/{{id}} - update allowed fields/status']
    if is_webhook: endpoints.insert(0, 'POST /webhooks/events - receive external event, validate event_id, process idempotently')
    if is_ai: endpoints.append('POST /ai/respond - run provider interface/stub and store response')
    return {
        'source':'Instant Fallback Engine',
        'problem_understanding':f'We need to build an API-first MVP for this problem: {problem[:500]}',
        'opening_script':'Let me confirm the core workflow first, then I’ll build the smallest working API end to end and verify it through Swagger/tests.',
        'clarifying_questions':['Who are the main users of this workflow?','What is the single most important happy path to finish during this assessment?','Is in-memory storage acceptable for the demo, or should I use SQLite?','Should authentication/roles be implemented now or discussed as production hardening?'],
        'assumptions_to_state':['I’ll build an API-first MVP.','I’ll use in-memory storage for speed unless persistence is required.','I’ll keep auth/RBAC as production hardening unless requested.'],
        'mvp_scope':[f'Create and store a {main}.',f'List and retrieve {main}s.','Validate required fields.','Handle not-found and invalid input.','Demo the flow in Swagger.'],
        'recommended_entities':[f'{main.title()} - id, title/name, description, status, created_at, updated_at','AuditLog - id, action, record_id, created_at'],
        'api_endpoints':endpoints,
        'implementation_steps':['Define Pydantic request/response schemas in app/schemas.py.','Create repository methods for create/list/get/update.','Create service methods for business rules and validation.','Wire FastAPI routes in app/main.py.','Run uvicorn and test in /docs.','Add focused pytest tests or manual Swagger steps.'],
        'codex_start_prompt':f'Build a minimal FastAPI MVP for this exact problem: {problem}\nUse schemas.py, service.py, repository.py, and main.py. Keep it simple, in-memory, testable, and explainable. Add Swagger-testable endpoints and clear 404/validation behavior.',
        'test_plan':['Create valid record and confirm ID is returned.','List records and confirm created item appears.','Fetch missing ID and expect 404.','Submit invalid payload and expect 422/400.','Update status/fields and confirm response changes.'],
        'codex_test_prompt':'Generate 5 focused pytest/FastAPI TestClient tests for the implemented core workflow: happy path, list/get, missing record, invalid input, and update behavior. Keep tests short and runnable with pytest -q.',
        'review_prompt':'Review this implementation for correctness, API validation, not-found handling, security basics, and production-readiness. Suggest only small fixes suitable for a live interview MVP.',
        'what_to_say_while_building':['I’m keeping HTTP, business logic, and storage separate so the code is easy to test.','For the live demo, in-memory storage keeps us focused on the workflow.','I’m testing the happy path first, then the important edge cases.'],
        'production_readiness':['Add authentication and RBAC.','Replace in-memory storage with PostgreSQL and migrations.','Add structured logging, request IDs, CI tests, monitoring, and rate limiting.','Add secrets management and deployment hardening.'],
        'final_summary_script':'The core flow is working end to end. I kept the design simple with routes, schemas, service logic, and repository storage. I verified the happy path and key edge cases. For production, I would add auth/RBAC, PostgreSQL migrations, structured logs, CI, monitoring, rate limiting, and deployment hardening.',
        'time_box_plan':['0-5 min: clarify and define MVP.','5-25 min: implement core endpoints.','25-40 min: run Swagger/manual tests.','40-55 min: add focused tests/review and final summary.'],
        'danger_zones':['Do not overbuild microservices.','Do not spend too long on auth unless requested.','Do not blindly paste AI code you cannot explain.','Do not finish without testing the core flow.']
    }

def normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    required=['source','problem_understanding','opening_script','clarifying_questions','assumptions_to_state','mvp_scope','recommended_entities','api_endpoints','implementation_steps','codex_start_prompt','test_plan','codex_test_prompt','review_prompt','what_to_say_while_building','production_readiness','final_summary_script','time_box_plan','danger_zones']
    out={}
    for k in required:
        default='' if ('prompt' in k or 'script' in k or k in ['source','problem_understanding','opening_script','final_summary_script']) else []
        v=data.get(k, default)
        if isinstance(v, dict): v=[f'{a}: {b}' for a,b in v.items()]
        out[k]=[str(x) for x in v] if isinstance(v,list) else str(v)
    return out

async def call_openrouter(problem: str, tech_stack: str) -> Optional[Dict[str, Any]]:
    if not OPENROUTER_API_KEY: return None
    async with httpx.AsyncClient(timeout=45) as client:
        res=await client.post('https://openrouter.ai/api/v1/chat/completions', headers={'Authorization':f'Bearer {OPENROUTER_API_KEY}','Content-Type':'application/json','HTTP-Referer':'https://hire-overseas-interview-coach.vercel.app','X-Title':'Hire Overseas Interview Coach'}, json={'model':MODEL,'messages':[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':f'Tech stack: {tech_stack}\nInterview problem/request:\n{problem}'}],'temperature':0.25,'response_format':{'type':'json_object'}})
        res.raise_for_status()
        txt=res.json()['choices'][0]['message']['content']
        return normalize_payload(json.loads(clean_json_text(txt)))

@app.get('/health')
def health():
    return {'ok':True,'app':APP_NAME,'model_configured':bool(OPENROUTER_API_KEY),'source':'VPS Hermes/Groot brain'}

@app.post('/coach')
async def coach(req: CoachRequest, x_hermes_brain_token: str = Header(default='')):
    if BRAIN_TOKEN and x_hermes_brain_token != BRAIN_TOKEN:
        raise HTTPException(status_code=401, detail='Invalid brain token')
    try:
        ai=await call_openrouter(req.problem, req.tech_stack)
        if ai:
            ai['source']='Hermes/Groot AI Brain on VPS'
            return ai
    except Exception as e:
        fb=fallback_solution(req.problem, req.tech_stack)
        fb['source']=f'Fallback Engine (AI unavailable: {type(e).__name__})'
        return fb
    return fallback_solution(req.problem, req.tech_stack)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('server:app', host='0.0.0.0', port=PORT, reload=False)
