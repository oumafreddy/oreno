# Oreno GRC – Context-Aware AI Agent (Design & Implementation Guide)

Version: 1.0
Status: Implementation-ready
Owner: Engineering / Platform

## Objectives
Build a secure, tenant-aware AI agent that:
- Understands user identity, role, tenant, and current app context (e.g., Audit, Risk)
- Converts natural language into validated, structured intents (CRUD, workflows)
- Auto-populates and validates form/serializer fields using existing business logic
- Executes only through Django Forms/DRF Serializers/Service layer (no raw DB writes)
- Enforces tenancy isolation, RBAC, throttling, and audit logging
- Supports multi-step workflows (e.g., Audit cycle → Workplan → Engagement → Issues → Report)

---

## Architecture Overview

### Components
- Agent API (Django app or service):
  - `POST /api/agent/parse` → parse & plan (dry-run)
  - `POST /api/agent/execute` → execute approved plan
- Context Provider (middleware/util): bundles `request.user`, `request.tenant`, `active_app`
- Schema Indexer: builds an index of models/forms/serializers/choices/relations
- Prompt-to-Intent Layer: LLM-guided mapping from natural text → structured intent
- Validation/Execution Layer: Uses serializers/forms/services to validate and commit
- Audit/Logging: tenant-aware `SecurityAuditLog` for every action
- Orchestrator: supports chained tasks (e.g., create workplan → create engagements → generate report)

### Request Flow
1. User is authenticated; middleware sets `request.tenant`, `request.organization`, `request.user`.
2. Agent receives prompt + context (tenant/app/user, optional UI selection).
3. Agent generates an Intent (dry-run) and validates via serializers/forms.
4. Agent responds with a preview; user confirms.
5. Agent executes: calls serializers/forms/services → save → logs event → returns result.

---

## Security & Compliance
- Tenancy: resolve with `django_tenants`; all queries/creates in tenant context only
- RBAC: check roles/permissions before intent execution
- Input sanitization: always through existing forms/serializers; never raw writes
- Rate-limiting: DRF throttles on agent endpoints
- CSRF/session/headers: inherit existing middleware and settings
- Audit: log `intent`, `tenant`, `user`, `result`, `errors` to `SecurityAuditLog`

---

## Endpoints (Agent)

### 1) Parse & Plan (Dry-run)
```
POST /api/agent/parse
Auth: JWT/Session
Body:
{
  "prompt": "Create workplan titled 2020 Approved annual workplan...",
  "active_app": "audit",          // optional, infer if omitted
  "mode": "plan"                  // plan | execute (plan only here)
}

Response:
{
  "intent": {
    "action": "create",
    "model": "audit.AuditWorkplan",
    "fields": {
      "title": "2020 Approved annual workplan",
      "year": 2020,
      "code": "2020",
      "origin": "board_approval",
      "status": "approved"
    }
  },
  "validation": {
    "valid": true,
    "errors": {}
  },
  "preview": {
    "summary": "Create AuditWorkplan in tenant 'krcs' with fields ..."
  }
}
```

### 2) Execute (Commit)
```
POST /api/agent/execute
Auth: JWT/Session
Body:
{
  "intent": { ... },             // result from /parse
  "confirm": true
}

Response:
{
  "result": {
    "model": "audit.AuditWorkplan",
    "id": 123,
    "url": "/audit/workplans/123/"
  },
  "log_id": 98765
}
```

---

## Context Provider

- Middleware already sets `request.tenant` & `request.user`.
- Add a small helper to determine `active_app` from request path or explicit param.

```python
# apps/core/utils_context.py
from urllib.parse import urlparse

def get_active_app_from_request(request):
    path = urlparse(request.get_full_path()).path
    for name in ["audit", "risk", "compliance", "contracts", "legal", "document_management", "ai_governance"]:
        if path.startswith(f"/{name}/") or request.GET.get("active_app") == name:
            return name
    return request.GET.get("active_app") or "core"
```

---

## Schema Indexer

- Introspect models, serializers, and forms to build a searchable index with field names, types, choices, help text, relations.
- Cache per app; rebuild on demand or during deploy.

```python
# services/agent/schema_index.py
from django.apps import apps
from django.forms import ModelForm
from rest_framework.serializers import ModelSerializer

class SchemaIndex:
    def __init__(self):
        self.models = {}
        self.serializers = {}
        self.forms = {}

    def build(self):
        for app_config in apps.get_app_configs():
            if app_config.name.split('.')[-1] in ("audit", "risk", "compliance", "contracts", "legal"):
                for model in app_config.get_models():
                    key = f"{model._meta.app_label}.{model.__name__}"
                    self.models[key] = self._model_fields(model)
        # Optionally import known serializer/form modules per app and introspect
        return self

    def _model_fields(self, model):
        fields = {}
        for f in model._meta.get_fields():
            if hasattr(f, 'attname'):
                fields[f.name] = {
                    'type': f.get_internal_type(),
                    'null': getattr(f, 'null', False),
                    'choices': getattr(f, 'choices', None),
                    'related': getattr(f, 'related_model', None) and str(f.related_model),
                }
        return fields
```

---

## Prompt-to-Intent Mapping

- Use an LLM (local or hosted) with a constrained, system prompt including:
  - Tenant context, user role
  - Active app
  - Indexed model/field hints
- The model returns a normalized intent: `{action, model, fields}`.
- Validate via serializers/forms; return errors for refinement.

```python
# services/agent/intent.py
from rest_framework import serializers

class IntentSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["create","update","delete","read","generate_report"]) 
    model = serializers.CharField()
    fields = serializers.DictField(child=serializers.JSONField(), required=False)
    filters = serializers.DictField(child=serializers.JSONField(), required=False)
    id = serializers.IntegerField(required=False)
```

---

## Validation & Execution Layer

- Only execute via serializers/forms or a service function that enforces RBAC and tenancy.
- Example for Audit Workplan creation (pseudocode):

```python
# services/agent/executor.py
from django_tenants.utils import tenant_context
from audit.serializers import AuditWorkplanSerializer
from users.models import CustomUser

class AgentExecutor:
    def __init__(self, request):
        self.request = request
        self.tenant = getattr(request, 'tenant', None)
        self.user = request.user

    def execute(self, intent):
        action = intent['action']
        model = intent['model']
        with tenant_context(self.tenant):
            if action == 'create' and model == 'audit.AuditWorkplan':
                return self._create_workplan(intent['fields'])
            # TODO: add other models/actions
        raise ValueError("Unsupported intent")

    def _create_workplan(self, fields):
        # Inject organization/user context if required
        if 'organization' not in fields and hasattr(self.user, 'organization'):
            fields['organization'] = self.user.organization_id
        serializer = AuditWorkplanSerializer(data=fields, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return {'model': 'audit.AuditWorkplan', 'id': obj.id, 'url': f"/audit/workplans/{obj.id}/"}
```

---

## Orchestration: Multi-step Flows

- Chain intents: e.g., Create Workplan → Create Engagements → Create Issues → Generate Report.
- Represent as a plan array and execute sequentially; stop on validation error.

```json
{
  "plan": [
    {"action":"create","model":"audit.AuditWorkplan","fields":{...}},
    {"action":"create","model":"audit.Engagement","fields":{...}},
    {"action":"create","model":"audit.Issue","fields":{...}},
    {"action":"generate_report","model":"reports.AuditDetailed","filters":{...}}
  ]
}
```

---

## Example: Workplan Creation (End-to-End)

Prompt:
> Create a workplan titled "2020 Approved annual workplan" for year 2020, code 2020, origin board approval, status approved.

Parse → Intent:
```json
{
  "action": "create",
  "model": "audit.AuditWorkplan",
  "fields": {
    "title": "2020 Approved annual workplan",
    "year": 2020,
    "code": "2020",
    "origin": "board_approval",
    "status": "approved"
  }
}
```
Validate:
- Use `AuditWorkplanSerializer` to validate fields and choices; map synonyms (e.g., "board approval" → "board_approval").

Execute:
- Save via serializer in `tenant_context` and return URL.

Audit log:
- Record tenant, user, intent, result (id), and timestamp in `SecurityAuditLog`.

---

## Permissions & Guardrails
- Permissions check: deny if user lacks create/update rights for the target model
- Confirm step: default to dry-run and require explicit `confirm=true` to commit
- Rate limiting: assign DRF throttles to agent endpoints (e.g., 60/min user)
- PII/cross-tenant protection: rely on serializers, queryset scoping, and tenant schema

---

## Telemetry & Audit
- `SecurityAuditLog.log_event(user, 'agent_execute', ip, ua, {intent, result})`
- Include tenant schema/name and user id/email in logs
- Error logs include serializer errors, permission denials, throttling

---

## Testing Strategy
- Add agent tests under `tests/agent/`:
  - Parse: inputs → expected intents
  - Validate: serializer rejects bad fields/values
  - Execute: creates in correct tenant; RBAC enforced
  - Orchestration: multi-step plan succeeds or aborts
  - Rate limit: 429 after bursts
  - Logging: events include tenant identifiers

---

## Deployment & Configuration
- Settings:
  - Add `services.agent` to INSTALLED_APPS if packaged as an app
  - DRF throttles for `agent` endpoints
- Env:
  - LLM provider credentials (or local model)
- Observability:
  - Log file/handlers for agent actions

---

## Minimal API Sketch (Views)

```python
# services/agent/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .schema_index import SchemaIndex
from .intent import IntentSerializer
from .executor import AgentExecutor

class AgentParseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get('prompt')
        active_app = request.data.get('active_app')
        # 1) Build/Load schema index
        # 2) Call LLM with prompt + schema hints + context → intent
        intent = self._mock_llm(prompt, active_app)
        # 3) Validate intent against serializer
        ser = IntentSerializer(data=intent)
        ser.is_valid(raise_exception=True)
        # Optionally dry-run (validate serializer for create/update)
        return Response({
            'intent': ser.validated_data,
            'validation': {'valid': True, 'errors': {}},
            'preview': {'summary': f"Plan: {ser.validated_data}"}
        })

    def _mock_llm(self, prompt, active_app):
        # Replace with real LLM mapping
        return {
            'action': 'create',
            'model': 'audit.AuditWorkplan',
            'fields': {
                'title': '2020 Approved annual workplan',
                'year': 2020,
                'code': '2020',
                'origin': 'board_approval',
                'status': 'approved'
            }
        }

class AgentExecuteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        intent = request.data.get('intent')
        confirm = request.data.get('confirm', False)
        if not confirm:
            return Response({'detail': 'Confirmation required'}, status=400)
        ser = IntentSerializer(data=intent)
        ser.is_valid(raise_exception=True)
        executor = AgentExecutor(request)
        result = executor.execute(ser.validated_data)
        return Response({'result': result})
```

---

## UX Considerations
- Chat UI with: context chips (Tenant/Org, App), form field suggestions, preview diff, and confirm/commit
- Show validation errors inline; offer clarification prompts
- Provide links to created objects and generated reports

---

## Rollout Plan
1. Pilot with Audit Workplan creation and Audit report generation
2. Add Engagement and Issue flows
3. Expand to Risk/Compliance/Contracts incrementally
4. Establish telemetry dashboards for usage and error rates

---

## Risks & Mitigations
- Hallucinations → Constrain LLM with schema hints and strict intent schema; server-side validation only
- Cross-tenant leakage → Tenant context enforced; queryset scoping; no raw DB
- Overposting/privilege escalation → Use serializers with read_only_fields and permission checks
- Abuse → Throttle agent endpoints and rate-limit prompt processing

---

## Conclusion
This design enables a secure, context-aware AI agent that leverages your existing tenancy, RBAC, forms, serializers, and workflows—allowing users to drive end-to-end processes (like the entire audit cycle) through natural language, while preserving all platform guarantees.
