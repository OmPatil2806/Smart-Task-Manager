<div align="center">

# ◎ Mnemosyne

### Smart To-Do App with AI Priority Engine

[![Python](https://img.shields.io/badge/Python-3.12+-1a1a18?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-d97706?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-built--in-059669?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-7c3aed?style=flat-square&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-f59e0b?style=flat-square&logo=javascript&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![License](https://img.shields.io/badge/License-MIT-2563eb?style=flat-square)](LICENSE)

**A full-stack task management app where AI predicts task priority automatically.**
Tasks are classified as 🔴 HIGH · 🟡 MEDIUM · 🟢 LOW using due dates, keywords, and category rules — no manual input needed.

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [ML Engine](#-ai-priority-engine)



</div>

---

## ✨ Features

| Category | Feature |
|---|---|
| **Task Management** | Create, edit, delete, complete tasks with real-time updates |
| **AI Priority** | Auto-predict priority on every task save |
| **Custom Keywords** | Define your own HIGH / MEDIUM / LOW trigger words |
| **Category Rules** | Finance & Health tasks auto-elevate based on due date |
| **Dashboard** | Productivity score, doughnut chart, overdue counter |
| **Authentication** | Signup / login / logout with bcrypt password hashing |
| **Data Isolation** | Every user sees only their own tasks |
| **Filtering** | All / Pending / Completed / Overdue / Due Today |
| **Search** | Instant client-side search across title and description |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│                 BROWSER (Frontend)               │
│   index.html  ·  style.css  ·  script.js        │
│              Fetch API  (HTTP/JSON)              │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│            FLASK BACKEND  (app.py)               │
│                                                  │
│  ┌───────────┐  ┌────────────┐  ┌─────────────┐ │
│  │  auth.py  │  │  tasks.py  │  │  /predict   │ │
│  │  /signup  │  │  /tasks    │  │  /stats     │ │
│  │  /login   │  │  CRUD ops  │  │  /keywords  │ │
│  └───────────┘  └────────────┘  └─────────────┘ │
└──────────────┬───────────────────────┬───────────┘
               │                       │
               ▼                       ▼
┌──────────────────────┐   ┌───────────────────────┐
│     SQLite DB        │   │      ML ENGINE        │
│                      │   │                       │
│  ┌────────────────┐  │   │  predictor.py         │
│  │  users table   │  │   │  ├─ Rule-based logic  │
│  └────────────────┘  │   │  ├─ Keyword scoring   │
│  ┌────────────────┐  │   │  ├─ Category boost    │
│  │  tasks table   │  │   │  └─ Custom keywords   │
│  └────────────────┘  │   │                       │
│  database.db (file)  │   │  train_model.py       │
└──────────────────────┘   │  └─ RandomForest (opt)│
                           └───────────────────────┘
```

### Request Flow

```
User saves task
    │
    ├──► POST /tasks ──────────────► tasks.py ──► SQLite INSERT
    │
    └──► POST /predict-priority ──► predictor.py
              │
              ├─ Days until due  (overdue → HIGH)
              ├─ Keyword match   (urgent/exam/deadline → HIGH)
              ├─ Category boost  (Finance ≤7d → HIGH)
              └─ Custom keywords (user-defined overrides)
                        │
                        └──► { priority: "HIGH", confidence: {...} }
```

---

## 📁 Folder Structure

```
smart-todo/
│
├── app.py                    # Flask entry point — routes, ML, stats
├── requirements.txt          # Python dependencies
│
├── backend/
│   ├── database.py           # SQLite schema + get_db() helper
│   ├── auth.py               # /signup /login /logout /me
│   └── tasks.py              # Full CRUD + /toggle endpoint
│
├── ml/
│   ├── predictor.py          # Rule-based priority engine (instant)
│   ├── train_model.py        # Optional RandomForest training
│   └── custom_keywords.json  # User-defined keywords (auto-created)
│
└── frontend/
    ├── index.html            # Auth screen + dashboard layout
    ├── style.css             # Minimal light-mode design system
    └── script.js             # Fetch API + Chart.js integration
```

---

## 🚀 Quick Start

### Prerequisites

- Python **3.10+**
- pip
- Any modern browser

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### 2 — Start the server

```bash
python app.py
```

```
✅ Database initialized.
🌐 http://localhost:5000
```

### 3 — Open the app

Visit **[http://localhost:5000](http://localhost:5000)** · Create an account · Start adding tasks.

### 4 — (Optional) Train the ML model

```bash
python -m ml.train_model
# Trains a RandomForest classifier on 3,000 synthetic samples
# Output: ml/priority_model.pkl
```

> ⚠️ **Important:** Never copy `priority_model.pkl` between machines.
> It is tied to your exact Python + numpy version.
> If it fails to load, delete it and retrain.



---

## 🔌 API Reference

### Authentication

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/signup` | `{ username, password }` | Create account |
| `POST` | `/login` | `{ username, password }` | Authenticate |
| `POST` | `/logout` | — | Clear session |
| `GET` | `/me` | — | Current user info |

### Tasks

| Method | Endpoint | Body / Params | Description |
|--------|----------|---------------|-------------|
| `GET` | `/tasks` | `?status=&priority=` | List all tasks (filtered) |
| `POST` | `/tasks` | `{ title, description, due_date, category, priority }` | Create task |
| `PUT` | `/tasks/:id` | `{ title, description, due_date, category, priority, status }` | Update task |
| `DELETE` | `/tasks/:id` | — | Delete task |
| `PATCH` | `/tasks/:id/toggle` | — | Toggle pending ↔ completed |

### ML & Stats

| Method | Endpoint | Body | Returns |
|--------|----------|------|---------|
| `POST` | `/predict-priority` | `{ title, description, due_date, category }` | `{ priority, confidence }` |
| `GET` | `/stats` | — | `{ total, completed, overdue, due_today, by_priority, productivity_score }` |
| `GET` | `/keywords` | — | `{ custom: {...}, defaults: {...} }` |
| `POST` | `/keywords` | `{ HIGH: [], MEDIUM: [], LOW: [] }` | `{ message, keywords }` |

---

## 🤖 AI Priority Engine

The priority engine is a **hybrid system** — a rule-based predictor runs instantly with zero dependencies, and an optional RandomForest model can be trained locally.

### Prediction Logic

```
1. Compute days_until_due  (negative = overdue)
2. Days rule:
     overdue  → HIGH
     ≤ 1 day  → HIGH
     ≤ 5 days → MEDIUM
     else     → LOW
3. Keyword scan (title + description):
     HIGH words   → escalate to HIGH
     MEDIUM words → escalate to MEDIUM
     LOW words    → cap at LOW (unless overdue)
4. Category boost:
     Finance ≤7d  → HIGH  (floor: MEDIUM)
     Health  ≤3d  → HIGH  (floor: MEDIUM)
     Work    ≤2d  → HIGH
     Study   ≤3d  → HIGH
5. Final = max rank across all signals
```

### Category Boost Rules

| Category | Floor | Becomes HIGH if due within |
|----------|-------|---------------------------|
| 💰 Finance | MEDIUM | 7 days |
| ❤️ Health | MEDIUM | 3 days |
| 💼 Work | LOW | 2 days |
| 📚 Study | LOW | 3 days |
| 🏠 Home | LOW | 14 days |
| 👤 Personal | LOW | 30 days |

### Default Keywords

```
HIGH   →  urgent, asap, immediately, critical, emergency, deadline,
          overdue, crucial, vital, exam, interview, boss, today,
          important, must, required, due, final, last, alert, priority

MEDIUM →  meeting, presentation, report, review, submit, call,
          prepare, follow, update, schedule, client, project,
          task, work, check, send, reply, finish, complete, plan
```

> Custom keywords are saved in `ml/custom_keywords.json` and editable
> directly in the app via the **⚙ AI Settings** panel.

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML5 / CSS3 / JS (ES6+) | UI, routing, DOM updates |
| Frontend | Chart.js 4.4 | Priority doughnut chart |
| Backend | Python 3.12 + Flask 3.0 | REST API |
| Backend | Flask-CORS | Cross-origin requests |
| Backend | Werkzeug | Password hashing |
| Database | SQLite | Persistent storage |
| ML | scikit-learn (RandomForest) | Optional trained model |
| ML | Rule engine (pure Python) | Instant fallback predictor |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">

Built with Flask · SQLite · scikit-learn · Chart.js

**◎ Mnemosyne** — Smart tasks, intelligently prioritized.

</div>
