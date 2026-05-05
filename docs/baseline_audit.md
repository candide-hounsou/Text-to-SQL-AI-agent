# Baseline Audit — Olist Text-to-SQL Agent

## Overview

The Olist Text-to-SQL Agent is a conversational data assistant that accepts natural-language questions, converts them into SQLite queries, executes them against the Olist e-commerce database, and returns both a human-readable summary and a suggested visualisation type.

---

## What the Agent Does

1. **Accepts a natural-language question** from the user via a Streamlit chat interface.
2. **Reformulates** the question into a standalone form using conversation history (context management).
3. **Classifies** the query complexity (`simple`, `complex`, `out_of_scope`) against the database schema.
4. **Plans** the SQL execution for complex queries (Chain-of-Thought planner).
5. **Generates** a valid SQLite `SELECT` query.
6. **Executes** the query with a 5-second timeout and a security guardrail (only `SELECT` allowed).
7. **Self-corrects** up to 3 times if the query fails.
8. **Summarises** the results in natural language and recommends a chart type (`bar`, `line`, `pie`, `none`).

---

## LangGraph Nodes

| Node | Description |
|------|-------------|
| `reformulate_query` | Rewrites the latest user question into a fully standalone question using conversation history. |
| `classify_query` | Uses structured LLM output (`QueryClassification`) to label the query as `simple`, `complex`, or `out_of_scope`. |
| `plan_sql_query` | Generates a step-by-step SQL execution plan for complex queries (CoT planner). Only invoked for `complex` queries when `use_cot_planner=True`. |
| `generate_sql` | Produces a raw SQLite `SELECT` query. Supports few-shot examples and self-correction prompting. |
| `execute_sql` | Runs the query via `sqlite3`. Enforces a SELECT-only security guardrail and a 5-second execution timeout. |
| `summarize_results` | Converts raw query results into a natural-language answer with a suggested chart type. |

## Routing Logic

```
START → reformulate_query → classify_query
  ├── out_of_scope → END
  ├── complex + CoT → plan_sql_query → generate_sql
  └── simple (or complex without CoT) → generate_sql
generate_sql → execute_sql
  ├── error + retries < 3 → generate_sql  (self-correction loop)
  └── success or max retries → summarize_results → END
```

---

## Current State (Agent State Keys)

| Key | Type | Description |
|-----|------|-------------|
| `query` | `str` | Original user question |
| `standalone_query` | `str` | Reformulated standalone question |
| `query_complexity` | `Literal` | Classification result |
| `classification_reason` | `str` | Reasoning for classification |
| `sql_plan` | `str` | CoT execution plan (complex only) |
| `sql_query` | `str` | Generated SQL |
| `db_results` | `str` | Formatted query results string |
| `raw_data` | `list` | List of row dicts |
| `error` | `str` | Last SQL error (if any) |
| `retry_count` | `int` | Number of self-correction retries |
| `summary` | `str` | Natural language answer |
| `chart_type` | `str` | Recommended chart type |
| `messages` | `List[BaseMessage]` | Full conversation history (LangChain) |

---

## Configuration Options (via `RunnableConfig.configurable`)

| Key | Default | Description |
|-----|---------|-------------|
| `model_name` | `"gpt-4o-mini"` | OpenAI model to use |
| `use_few_shot` | `True` | Include few-shot SQL examples in `generate_sql` prompt |
| `use_cot_planner` | `True` | Enable Chain-of-Thought SQL planner for complex queries |
| `use_self_correction` | `True` | Enable the SQL self-correction retry loop |

---

## Current Limitations

1. **Single LLM provider** — only OpenAI is supported. There is no abstraction for other providers (Anthropic, Gemini, local models).
2. **Hardcoded database path** — `execute_sql` directly opens `"data/olist.db"`. No abstraction layer for swapping databases.
3. **Monolithic `agent.py`** — all node logic, state definitions, routing, and graph assembly are in a single 570-line file, making it hard to test individual components.
4. **No unit tests** — there is no test suite; the only way to validate the agent is to run the full Streamlit app.
5. **No CI pipeline** — no automated linting, testing, or quality gates on pull requests.
6. **Schema loading is tightly coupled** — `get_schema()` reads from a hardcoded `"data/schema.txt"` path.
7. **Prompt strings are inline** — system prompts are defined directly inside node functions; there is no centralised prompt registry.
8. **Few-shot examples are inline** — hardcoded inside `generate_sql`, making them hard to update or extend.
9. **No connector abstraction** — the SQLite connection is opened directly in `execute_sql`; swapping to PostgreSQL or another database would require modifying node code.
10. **Memory is ephemeral** — `MemorySaver` stores conversation history only in-process; there is no persistent storage.

---

## Files at Baseline

```
agent.py           — monolithic agent (nodes + state + routing + graph)
app.py             — Streamlit UI
eval/eval_app.py   — evaluation dashboard
eval/benchmark.json
eval/runs_history.json
scripts/build_db.py
scripts/build_schema.py
scripts/extract_schema.py
requirements.txt
pyproject.toml
```
