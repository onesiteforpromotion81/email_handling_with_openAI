# Strata enquiry triage (prototype)

Small prototype for **Strata Management Consultants**: paste a client enquiry, get **classification**, **confidence**, **draft reply**, and **recommended internal actions**. Built to show AI integration in a realistic admin workflow.

## Tools

- **Python 3.10+**
- **OpenAI API** (default model `gpt-4o-mini`, JSON mode)
- **Flask** for a small web UI; optional **CLI** for scripts and CI
- **Pydantic** / **pydantic-settings** for typed config and triage output

## Layout (refactor)

Code lives under **`strata_triage/`**: domain models and errors, **`LLMClient`** protocol, OpenAI adapter, **`EnquiryTriageService`** (orchestration), **`process_enquiry()`** facade, and **`create_app()`** Flask factory. HTTP maps **401 / 429** from OpenAI to clearer operator messages instead of a single generic “API error” string.

## Setup

```bash
cd /home/dev/assessment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set OPENAI_API_KEY
```

## Run

**Web UI**

```bash
cd /home/dev/assessment
flask --app app run
```

Open http://127.0.0.1:5000 (or use `python app.py`).

If your system blocks `pip install` without a venv (PEP 668), either install `python3-venv` and use a venv, or install into a local folder:

```bash
python3 -m pip install -r requirements.txt -t vendor
PYTHONPATH=vendor flask --app app run
```

**CLI** (JSON to stdout)

```bash
echo "Our levies are wrong on the last notice." | python cli.py
python cli.py --file sample_enquiry.txt
```

**JSON API** (for integrations)

```bash
curl -s -X POST http://127.0.0.1:5000/api/triage \
  -H "Content-Type: application/json" \
  -d '{"enquiry":"We need a quote for strata management."}'
```

## What it does

| Output | Meaning |
|--------|---------|
| `classification` | `new_client`, `support_request`, `complaint`, `general_question`, or `unclear` |
| `confidence` | 0.0–1.0; how sure the model is about the classification |
| `confidence_rationale` | Short explanation (useful when confidence is low) |
| `suggested_staff_reply` | Editable email draft in Australian professional tone |
| `recommended_actions` | Bullet-style internal next steps |
| `urgency` / `flags` | triage hints (e.g. safety, tribunal mentions) |

Empty input is handled **without** calling the API. Vague or nonsensical text is steered by the system prompt toward `unclear` with a low confidence and a clarifying draft reply. If the model returns non-JSON, a **one-shot repair** prompt runs; if that still fails, the app returns a safe **unclear** fallback with a `parse_error` flag.

## Prompt engineering (design choices)

Prompts are in **`strata_triage/prompts.py`** so they are easy to review.

- **Role and domain** — Strata / body corporate in Australia, so tone and examples match the scenario.
- **Fixed JSON schema** — Staff get consistent fields for UI or downstream automation; `response_format=json_object` reduces stray prose.
- **Explicit `unclear`** — Reduces forced wrong labels on gibberish or empty noise; paired with **low confidence** and a **polite request for details** in the draft.
- **No legal advice** — Instructs the model to flag legal/tribunal matters for humans.
- **Low temperature (0.2)** — More stable classification and drafting for ops use.

## Automation potential

- **Web form / email** — On submit, POST body to the same logic as `process_enquiry()`; store JSON on a **ticket** (Zendesk, Freshdesk, Jira Service Management).
- **CRM** — Map `classification` to pipeline stage or owner queue; attach `suggested_staff_reply` as an internal note or draft.
- **Task queue** — Worker consumes `recommended_actions` and creates tasks (e.g. “Check levy account” → finance queue).
- **Human in the loop** — Always keep staff approval before send; this tool is **assistive**, not autonomous client-facing.

## Files

| Path | Role |
|------|------|
| `strata_triage/config.py` | `Settings` from env / `.env` |
| `strata_triage/models.py` | `EnquiryTriageResult`, enums |
| `strata_triage/errors.py` | `TriageError`, `LLMProviderError`, `MissingApiKeyError` |
| `strata_triage/prompts.py` | System / user / repair prompts |
| `strata_triage/ports.py` | `LLMClient` protocol |
| `strata_triage/adapters/openai_llm.py` | OpenAI implementation + error mapping |
| `strata_triage/services/triage.py` | `EnquiryTriageService` — parse, repair, coerce |
| `strata_triage/facade.py` | `process_enquiry()` for CLI/UI |
| `strata_triage/web/app.py` | `create_app()`, routes |
| `app.py` | Exposes `app` for `flask --app app run` |
| `templates/index.html` | Dashboard template |
| `cli.py` | stdin/file → JSON |
| `.env.example` | Environment template |

## Licence

Prototype for assessment / demonstration purposes.
