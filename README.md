# ⬡ Mnemosyne — Smart To-Do App

> AI-powered task management with ML-predicted priorities.

---

## 📁 Folder Structure

```
smart-todo/
├── app.py                  ← Flask entry point (run this)
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── database.py         ← SQLite init & helpers
│   ├── auth.py             ← /signup /login /logout /me
│   └── tasks.py            ← CRUD routes for tasks
├── ml/
│   ├── __init__.py
│   ├── train_model.py      ← ML training script
│   ├── predictor.py        ← predict_priority() function
│   └── priority_model.pkl  ← Trained model (auto-generated)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the ML model (first time only)
```bash
python -m ml.train_model
# Or it auto-trains on first server start
```

### 3. Run the server
```bash
python app.py
```

### 4. Open the app
Visit: **http://localhost:5000**

---

## 🔌 API Reference

### Auth
| Method | Endpoint   | Body                         | Description        |
|--------|-----------|------------------------------|--------------------|
| POST   | /signup   | `{username, password}`       | Create account     |
| POST   | /login    | `{username, password}`       | Login              |
| POST   | /logout   | —                            | Logout             |
| GET    | /me       | —                            | Current user info  |

### Tasks
| Method | Endpoint          | Description            |
|--------|-------------------|------------------------|
| GET    | /tasks            | Get all user tasks     |
| POST   | /tasks            | Create task            |
| PUT    | /tasks/:id        | Update task            |
| DELETE | /tasks/:id        | Delete task            |
| PATCH  | /tasks/:id/toggle | Toggle complete status |

### ML
| Method | Endpoint           | Body                                    | Returns                     |
|--------|--------------------|-----------------------------------------|-----------------------------|
| POST   | /predict-priority  | `{title, description, due_date, category}` | `{priority, confidence}` |

### Stats
| Method | Endpoint | Description                    |
|--------|----------|--------------------------------|
| GET    | /stats   | Productivity score + breakdown |

---

## 🤖 ML System

**Model:** Gradient Boosting Classifier (scikit-learn)

**Features used:**
- Keyword scores (urgent, critical, exam, meeting, deadline...)
- Title/description length and word count
- Days until due (negative = overdue)
- Due date urgency level (0–5 scale)
- Task category encoding

**Outputs:** `HIGH 🔴` / `MEDIUM 🟡` / `LOW 🟢` with confidence scores

**Training data:** 3,000 synthetic samples with realistic task distributions

---

## 🗄️ Database Schema

```sql
CREATE TABLE users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  title       TEXT NOT NULL,
  description TEXT DEFAULT '',
  category    TEXT DEFAULT 'other',
  due_date    TEXT,
  status      TEXT DEFAULT 'pending',
  priority    TEXT DEFAULT 'MEDIUM',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## ✨ Features

- ✅ User auth (signup/login/logout) with session management
- ✅ Full task CRUD — create, read, update, delete
- ✅ Mark tasks complete / reopen
- ✅ ML-predicted priority with confidence scores
- ✅ Filter by: All / Pending / Completed / Overdue / Due Today
- ✅ Filter by priority: High / Medium / Low
- ✅ Live search
- ✅ Productivity score (completed / total × 100%)
- ✅ Overdue detection
- ✅ Task categories (Work, Study, Personal, Health, Finance, Home)
- ✅ Real-time stats dashboard
- ✅ Dark industrial UI with smooth animations
