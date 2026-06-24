# Chatbot

A full-stack AI chatbot with **LangGraph intelligent routing**, document RAG, live weather, **bug-report triage**, and **Server-Sent Events (SSE)** streaming. Users authenticate via JWT, upload PDFs per conversation, and send all messages through a single `POST /chat` endpoint—the backend graph decides whether to chat generally, search documents, fetch weather, or draft a bug report for admin review.

## Documentation map

| README | Audience |
|--------|----------|
| [backend/README.md](backend/README.md) | FastAPI, LangGraph, RAG, Jira admin queue, migrations, services |
| [frontend/README.md](frontend/README.md) | Next.js UI, SSE client, auth, chat shell, admin dashboard |

## Introduction

This project is a production-style chat application. It demonstrates how to combine a modern web stack with agentic orchestration: instead of exposing separate endpoints for general chat, document Q&A, weather, and support tickets, the backend uses a **LangGraph state machine** to classify each user message and route it to the right capability.

From the user's perspective, the experience is a single chat thread. Upload a PDF, ask about the weather, report a broken feature, or have a casual conversation—the assistant responds in one stream. Behind the scenes, the graph loads conversation memory from Redis, checks which documents are indexed for the thread, classifies intent, runs retrieval or external APIs when needed, and streams tokens back over SSE.

Bug reports follow a human-in-the-loop workflow: the graph drafts a `pending_jira_tickets` row, an administrator approves or rejects it from `/admin`, and approved tickets are created in Jira with email notification to the reporter.

## Features

| Capability | Description |
|------------|-------------|
| **LangGraph orchestrator** | Classifier routes to `chat`, RAG (`researcher` → `writer`), `weather`, or `bug_report` |
| **Streaming SSE** | Token-by-token responses to the Next.js client |
| **Document RAG** | PDF upload, chunking, ONNX BGE embeddings (CPU execution), Pinecone vector store, Cohere reranking |
| **Weather** | Open-Meteo geocoding + forecast, grounded Gemini replies |
| **Bug reports** | Gemini extracts title/description → pending queue → admin approve/reject → Jira + SMTP email |
| **Admin dashboard** | Role-gated UI (`ticket:manage`) to review and action pending tickets |
| **Conversation memory** | Redis for hot history + summarization; Postgres for durable storage |
| **Auth** | JWT access tokens, httpOnly refresh cookies, OAuth2 scopes, RBAC permissions |
| **Marketing landing** | Public homepage with features, pricing, FAQ, and dark-mode support |

## Tech stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | Next.js 16 (App Router), React 19, Tailwind CSS 4, TypeScript, SWR, Sonner |
| **Backend** | FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic Settings |
| **Orchestration** | LangGraph, LangChain Core runnables |
| **AI** | Google Gemini (`gemini-3.1-flash-lite`) — chat, classification, summarization, bug extraction |
| **RAG** | Pinecone vector store, local BGE-small ONNX (direct CPU inference via `onnxruntime` + `tokenizers`), Cohere Rerank v3 |
| **Integrations** | Jira Cloud REST API, SMTP (approval/rejection emails), Open-Meteo |
| **Cache** | Redis (`redis.asyncio`) — conversation history, summaries, rate limits |
| **Database** | PostgreSQL — users, sessions, conversations, messages, documents, pending tickets |
| **Documents** | PyMuPDF extraction, langchain-text-splitters, async background indexing |
| **Auth** | PyJWT, bcrypt, OAuth2 password flow, role/permission tables |
| **Container** | Multi-stage Docker image (`backend/dockerfile`) with uv |

## System architecture

```mermaid
flowchart TB
    subgraph Client["Frontend (Next.js)"]
        Landing["/ marketing page"]
        ChatUI[ChatShell / ChatInput]
        AdminUI["/admin TicketTable"]
        SSE[sseParser + useChat]
    end

    subgraph API["Backend (FastAPI)"]
        ChatRoute["POST /chat"]
        AdminRoute["/admin/*"]
        Runner[graph/runner.py]
        Graph[LangGraph agent]
    end

    subgraph GraphNodes["LangGraph nodes"]
        CLS[classifier]
        CHAT[chat]
        RES[researcher]
        WRI[writer]
        WTH[weather]
        BUG[bug_report]
    end

    subgraph External["External services"]
        Gemini[Google Gemini]
        Cohere[Cohere Rerank]
        Meteo[Open-Meteo API]
        Jira[Jira Cloud]
        SMTP[SMTP server]
    end

    subgraph Data["Data stores"]
        Redis[(Redis)]
        PG[(PostgreSQL)]
        VectorDB["Vector store\n(Pinecone)"]
    end

    Landing --> ChatUI
    ChatUI --> SSE
    AdminUI --> AdminRoute
    SSE -->|SSE stream| ChatRoute
    ChatRoute --> Runner
    Runner --> Graph
    Graph --> CLS
    CLS --> CHAT
    CLS --> RES
    CLS --> WTH
    CLS --> BUG
    RES --> WRI

    CHAT --> Gemini
    WRI --> Gemini
    WTH --> Meteo
    WTH --> Gemini
    BUG --> Gemini
    BUG --> PG
    RES --> VectorDB
    RES --> Cohere

    AdminRoute --> Jira
    AdminRoute --> SMTP
    AdminRoute --> PG

    Runner --> Redis
    Runner --> PG
    ChatRoute --> PG
```

### Component responsibilities

| Component | Role |
|-----------|------|
| **Next.js client** | Auth, landing page, conversation sidebar, document panel, SSE consumption, admin ticket review |
| **`POST /chat`** | Ownership check, then delegates to `run_graph_stream()` |
| **`runner.py`** | Builds `AgentState`, runs `agent_graph.astream()`, maps custom events to SSE |
| **LangGraph** | Conditional routing across four intent paths |
| **`bug_report` node** | Extracts ticket fields via Gemini, inserts `pending_jira_tickets`, rate-limited per user |
| **`/admin/*`** | Lists pending tickets; approve creates Jira issue + email; reject notifies user |
| **Redis** | Hot message list, rolling summary, bug-report rate-limit keys |
| **Postgres** | Durable users, conversations, messages, document metadata, pending tickets |
| **Vector store** | `VectorStoreService` — Pinecone (managed); scoped by user + conversation document IDs |

## LangGraph routing

Every chat message enters the graph at the **classifier** node. The classifier picks one of four routes; the graph then runs the matching node chain and streams output via LangGraph's custom stream writer.

```mermaid
flowchart LR
    START((START)) --> classifier
    classifier -->|chat| chat_node[chat]
    classifier -->|rag| researcher
    classifier -->|weather| weather_node[weather]
    classifier -->|bug_report| bug_node[bug_report]
    researcher --> writer
    chat_node --> END((END))
    writer --> END
    weather_node --> END
    bug_node --> END
```

| Route | When it runs | Node path | Output |
|-------|--------------|-----------|--------|
| **chat** | General conversation, no document/weather/bug intent | `classifier` → `chat` → END | Gemini stream from user message + history |
| **rag** | Document-related intent and indexed PDFs exist | `classifier` → `researcher` → `writer` → END | Retrieve → rerank → grounded Gemini stream + source citations |
| **weather** | Weather keywords or location in message | `classifier` → `weather` → END | Open-Meteo fetch → Gemini conversational summary |
| **bug_report** | User reports errors, broken features, or app issues | `classifier` → `bug_report` → END | Draft Jira ticket in DB; user notified that admin will review |

### Classifier logic

1. **Regex fast-path** — `WEATHER_PATTERNS`, `BUG_PATTERNS`, and `RAG_PATTERNS` in `classifier.py` match common phrases without calling the LLM.
2. **Gemini structured classification** — When no rule matches, `classify_json()` returns a `RouteDecision` (`route` + `reason`).
3. **Hard guards** — RAG is downgraded to `chat` when the conversation has no indexed documents.

The frontend does not choose the route; it always calls `POST /chat`.

## Bug report and admin workflow

```mermaid
sequenceDiagram
    participant U as User
    participant Chat as POST /chat
    participant G as bug_report node
    participant PG as PostgreSQL
    participant A as Admin (/admin)
    participant J as Jira
    participant E as SMTP

    U->>Chat: "The upload button is broken"
    Chat->>G: route = bug_report
    G->>G: Gemini extracts title + description
    G->>PG: INSERT pending_jira_tickets (status: pending)
    G-->>U: SSE confirmation message

    A->>PG: GET /admin/pending-tickets
  alt Approve
        A->>PG: POST /admin/approve-ticket/{id}
        A->>J: create_jira_issue()
        A->>PG: status → approved, jira_key set
        A->>E: send_approval_email()
    else Reject
        A->>PG: POST /admin/reject-ticket/{id}
        A->>E: send_rejection_email()
    end
```

- **Rate limiting** — Redis key `rate_limit:bug_report:{user_id}` prevents spam (`BUG_REPORT_RATE_LIMIT_SECONDS`).
- **Permissions** — Admin endpoints require OAuth2 scope `ticket:manage` (assigned to the `admin` role in seed data).
- **Idempotency** — Row-level locking and `jira_key` checks prevent duplicate Jira issues on re-approval.

## End-to-end chat flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as POST /chat
    participant R as runner.py
    participant G as LangGraph
    participant Redis as Redis
    participant PG as PostgreSQL

    U->>FE: Send message
    FE->>API: POST /chat (JWT + conversationId)
    API->>R: run_graph_stream()
    R->>PG: Load indexed documents for conversation
    R->>Redis: get_conversation_state()
    R->>G: astream(custom)
    G->>G: classifier → route node(s)
    loop Stream tokens
        G-->>R: token / sources / done events
        R-->>FE: SSE data chunks
        FE-->>U: Render streaming text
    end
    R->>Redis: persist_turn (history + summary)
    R->>PG: Save messages
```

### Custom stream events (graph → runner → SSE)

| Event | Payload | SSE mapping |
|-------|---------|-------------|
| `token` | `{ content }` | `{ success: true, data: { content } }` |
| `sources` | `{ sources }` | Buffered until final chunk |
| `done` | `{ prepared_messages, context_summary }` | Used for persistence after stream ends |

Final SSE chunk: `{ content: "", finishReason: "STOP", sources?: [...] }`.

## Document upload and RAG pipeline

Documents are scoped to a **conversation**. Upload triggers async indexing; the classifier only routes to RAG when documents reach `indexed` status.

```mermaid
flowchart LR
    Upload[PDF upload] --> Parse[PyMuPDF extract]
    Parse --> Chunk[Parent/child token split]
    Chunk --> Embed[ONNX BGE embed]
    Embed --> VectorUpsert[Vector store upsert]
    VectorUpsert --> Indexed[status: indexed]
    Indexed --> Classifier[classifier may route rag]
```

Retrieval path (when routed to RAG):

1. **researcher** — embed query → vector store search → Cohere rerank → dedupe parent chunks → build grounded prompt.
2. **writer** — stream Gemini with grounded prompt; emit `sources` before `done`.

## Vector store

RAG indexing and retrieval go through `VectorStoreService` in `services/vector_store.py`. The backend is powered by **Pinecone** for document vector storage:

* **Pinecone** (`VECTOR_STORE_PROVIDER=pinecone`): Uses the native `AsyncPinecone` SDK. It automatically creates a serverless index (384-dimensional, cosine similarity) on startup if not present. Vectors are isolated by **`namespace = user_id`** to ensure tenant isolation.

Operations supported: `add_chunks`, `query`, and `delete_document` (scoped by conversation document IDs).

```env
VECTOR_STORE_PROVIDER=pinecone
PINECONE_API=your-pinecone-api-key
PINECONE_INDEX_NAME=documents
```

See [backend/README.md](backend/README.md) for full configuration and lifecycle details.

## Project structure

```
chatbot/
├── README.md                 # This file — system overview
├── .dockerignore             # Root Docker build exclusions
├── backend/
│   ├── README.md             # Backend guide
│   ├── dockerfile            # Multi-stage Python 3.14 image
│   └── app/                  # Python project root (uv, main.py, .env)
│       ├── api/routes/       # HTTP endpoints (chat, documents, admin)
│       ├── auth/             # JWT, scopes, refresh cookies, RBAC
│       ├── services/graph/   # LangGraph (classifier, nodes, runner)
│       └── services/         # Gemini, RAG, vector_store (Pinecone), Jira, email
└── frontend/
    ├── README.md             # Frontend guide
    └── Chatbot/              # Next.js App Router app
        ├── app/              # Pages (landing, login, register, chat, admin)
        ├── components/       # Chat UI, admin tables, marketing blocks
        └── lib/api/          # API clients + SSE parser
```

## Prerequisites

| Service | Purpose |
|---------|---------|
| **PostgreSQL** | Users, conversations, messages, document metadata, refresh sessions, pending tickets |
| **Redis** | Conversation history cache, rolling summaries, rate limits |
| **Google Gemini API** | Chat, classification, summarization, bug extraction |
| **Cohere API** | Reranking for RAG retrieval |
| **Pinecone** | Managed vector store when `VECTOR_STORE_PROVIDER=pinecone` (`PINECONE_API`, index name) |
| **Jira Cloud** | Issue creation on ticket approval (`JIRA_*` env vars) |
| **SMTP** | Approval/rejection emails (optional but recommended) |

Required: local ONNX embedding model files placed at `backend/app/models/onnx/baai-bge-small` (must contain `model.onnx` and `tokenizer.json`).

## Quick start

### Backend

```bash
cd backend/app
uv sync
# Create .env — see backend/README.md
alembic upgrade head
python seed.py    # Seeds roles and permissions (admin role includes ticket:manage)
uv run fastapi dev main.py
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health/

### Frontend

```bash
cd frontend/Chatbot
npm install
# .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000 (marketing landing). Sign in at `/login`, then use `/chat`.

### Docker (backend)

```bash
cd backend
docker build -f dockerfile -t chatbot-api .
docker run -p 8000:8000 --env-file app/.env chatbot-api
```

### Smoke test

1. Register or log in (`/register`, `/login`)
2. Open `/chat`, start a conversation
3. Plain chat: `Hello`
4. Upload a PDF → wait for **indexed** → `Summarize the document`
5. Weather: `What's the weather in London?`
6. Bug report: `The document upload is broken` → confirm pending-ticket message
7. Assign `admin` role to a user, open `/admin`, approve or reject the ticket

## API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health/` | — | Health check (Redis) |
| `GET` | `/auth/me` | Bearer | Current user + permissions |
| `POST` | `/auth/register` | — | Create account |
| `POST` | `/auth/login` | — | OAuth2 password → JWT + refresh cookie |
| `POST` | `/auth/refresh` | Cookie | Rotate refresh token |
| `POST` | `/auth/logout` | Bearer | Invalidate server session |
| `GET` | `/conversations` | Bearer | List conversations |
| `POST` | `/conversations` | Bearer | Create conversation |
| `GET` | `/conversations/{id}/messages` | Bearer | Message history |
| `POST` | `/chat` | Bearer (`ai:chat`) | **Primary** streaming endpoint (LangGraph) |
| `POST` | `/conversations/{id}/documents/upload` | Bearer | Upload PDF (async indexing) |
| `GET` | `/conversations/{id}/documents` | Bearer | List documents |
| `GET` | `/admin/pending-tickets` | Bearer (`ticket:manage`) | List pending bug reports |
| `POST` | `/admin/approve-ticket/{id}` | Bearer (`ticket:manage`) | Approve → Jira + email |
| `POST` | `/admin/reject-ticket/{id}` | Bearer (`ticket:manage`) | Reject → email |

## Design decisions

- **Single chat endpoint** — Simplifies the client; routing intelligence lives in the graph, not the UI.
- **Human-in-the-loop bug reports** — Prevents automatic Jira spam; admins validate before issue creation.
- **Dual memory** — Redis for fast context + compaction; Postgres for durable history and re-hydration.
- **Conversation-scoped RAG** — Vector queries filter by user and conversation document IDs only.
- **Namespace-isolated Vector Store** — Powered by Pinecone. RAG and document code query/delete items matching the conversation's active document IDs, isolated under the user's namespace (`user_id`) to ensure absolute tenant data segregation.
- **Hybrid auth** — Short-lived access token in `localStorage`; refresh token in httpOnly cookie (`credentials: include`).
- **Disconnect safety** — SSE generators skip `persist_turn` when the client disconnects mid-stream.
- **Source citations** — Returned on the final SSE chunk for RAG responses; not yet persisted on `messages` rows (citations disappear on page reload).

## Further reading

- [Backend setup, LangGraph modules, Jira integration, config, database schema](backend/README.md)
- [Frontend components, hooks, SSE client, auth, admin dashboard](frontend/README.md)
