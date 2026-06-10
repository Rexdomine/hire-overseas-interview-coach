function fallbackSolution(problem, techStack) {
  const p = String(problem || '').toLowerCase();
  const isAi = ['ai', 'chatbot', 'llm', 'summar', 'document', 'recommendation'].some(w => p.includes(w));
  const isWebhook = ['webhook', 'event', 'callback', 'payment', 'stripe', 'third-party'].some(w => p.includes(w));
  let main = 'request';
  if (p.includes('ticket')) main = 'ticket';
  else if (p.includes('task')) main = 'task';
  else if (p.includes('course') || p.includes('student')) main = 'student/course record';
  else if (p.includes('order')) main = 'order';
  else if (p.includes('document')) main = 'document job';
  const slug = `${main.replace(/\//g, '-').replace(/\s+/g, '-')}s`;
  const endpoints = [
    `POST /${slug} - create a new ${main} with validation`,
    `GET /${slug} - list records for demo/testing`,
    `GET /${slug}/{id} - fetch one record or return 404`,
    `PATCH /${slug}/{id} - update allowed fields/status`
  ];
  if (isWebhook) endpoints.unshift('POST /webhooks/events - receive external event, validate event_id, process idempotently');
  if (isAi) endpoints.push('POST /ai/respond - run provider interface/stub and store response');
  return {
    source: 'Vercel Safety Fallback Engine',
    problem_understanding: `We need to build an API-first MVP for this problem: ${String(problem || '').slice(0, 600)}`,
    opening_script: 'Let me confirm the core workflow first, then I’ll build the smallest working API end to end and verify it through Swagger/tests.',
    clarifying_questions: ['Who are the main users of this workflow?', 'What is the single most important happy path to finish during this assessment?', 'Is in-memory storage acceptable for the demo, or should I use SQLite?', 'Should authentication/roles be implemented now or discussed as production hardening?'],
    assumptions_to_state: ['I’ll build an API-first MVP.', 'I’ll use in-memory storage for speed unless persistence is required.', 'I’ll keep auth/RBAC as production hardening unless requested.'],
    mvp_scope: [`Create and store a ${main}.`, `List and retrieve ${main}s.`, 'Validate required fields.', 'Handle not-found and invalid input.', 'Demo the flow in Swagger.'],
    recommended_entities: [`${main} - id, title/name, description, status, created_at, updated_at`, 'AuditLog - id, action, record_id, created_at'],
    api_endpoints: endpoints,
    implementation_steps: ['Define Pydantic request/response schemas in app/schemas.py.', 'Create repository methods for create/list/get/update.', 'Create service methods for business rules and validation.', 'Wire FastAPI routes in app/main.py.', 'Run uvicorn and test in /docs.', 'Add focused pytest tests or manual Swagger steps.'],
    codex_start_prompt: `Build a minimal FastAPI MVP for this exact problem: ${problem}\nUse schemas.py, service.py, repository.py, and main.py. Keep it simple, in-memory, testable, and explainable. Add Swagger-testable endpoints and clear 404/validation behavior.`,
    test_plan: ['Create valid record and confirm ID is returned.', 'List records and confirm created item appears.', 'Fetch missing ID and expect 404.', 'Submit invalid payload and expect 422/400.', 'Update status/fields and confirm response changes.'],
    codex_test_prompt: 'Generate 5 focused pytest/FastAPI TestClient tests for the implemented core workflow: happy path, list/get, missing record, invalid input, and update behavior. Keep tests short and runnable with pytest -q.',
    review_prompt: 'Review this implementation for correctness, API validation, not-found handling, security basics, and production-readiness. Suggest only small fixes suitable for a live interview MVP.',
    what_to_say_while_building: ['I’m keeping HTTP, business logic, and storage separate so the code is easy to test.', 'For the live demo, in-memory storage keeps us focused on the workflow.', 'I’m testing the happy path first, then the important edge cases.'],
    production_readiness: ['Add authentication and RBAC.', 'Replace in-memory storage with PostgreSQL and migrations.', 'Add structured logging, request IDs, CI tests, monitoring, and rate limiting.', 'Add secrets management and deployment hardening.'],
    final_summary_script: 'The core flow is working end to end. I kept the design simple with routes, schemas, service logic, and repository storage. I verified the happy path and key edge cases. For production, I would add auth/RBAC, PostgreSQL migrations, structured logs, CI, monitoring, rate limiting, and deployment hardening.',
    time_box_plan: ['0-5 min: clarify and define MVP.', '5-25 min: implement core endpoints.', '25-40 min: run Swagger/manual tests.', '40-55 min: add focused tests/review and final summary.'],
    danger_zones: ['Do not overbuild microservices.', 'Do not spend too long on auth unless requested.', 'Do not blindly paste AI code you cannot explain.', 'Do not finish without testing the core flow.']
  };
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }
  const brainUrl = process.env.HERMES_BRAIN_URL;
  const brainToken = process.env.HERMES_BRAIN_TOKEN;
  if (!brainUrl) return res.status(200).json(fallbackSolution(req.body?.problem, req.body?.tech_stack));
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    const upstream = await fetch(`${brainUrl.replace(/\/$/, '')}/coach`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Hermes-Brain-Token': brainToken || '' },
      body: JSON.stringify(req.body || {}),
      signal: controller.signal
    });
    clearTimeout(timer);
    if (!upstream.ok) return res.status(200).json(fallbackSolution(req.body?.problem, req.body?.tech_stack));
    const text = await upstream.text();
    res.status(200);
    res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json');
    return res.send(text);
  } catch (error) {
    return res.status(200).json(fallbackSolution(req.body?.problem, req.body?.tech_stack));
  }
};
