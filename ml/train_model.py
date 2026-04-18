"""
Smart To-Do ML Priority Prediction Model
Trains a Gradient Boosted classifier to predict task priority.
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ─── Feature Engineering ───────────────────────────────────────────────────────

URGENT_KEYWORDS = [
    "urgent", "asap", "immediately", "critical", "emergency",
    "deadline", "overdue", "crucial", "vital", "priority"
]
HIGH_KEYWORDS = [
    "exam", "meeting", "interview", "presentation", "submission",
    "important", "required", "must", "boss", "client", "due"
]
MEDIUM_KEYWORDS = [
    "review", "report", "call", "update", "prepare", "schedule",
    "reminder", "check", "follow", "research"
]

CATEGORIES = ["work", "personal", "health", "finance", "study", "home", "other"]

def extract_features(title: str, description: str, days_until_due: float, category: str = "other") -> np.ndarray:
    """Extract numerical features from task data."""
    text = (title + " " + description).lower()

    # Keyword scores
    urgent_score = sum(1 for kw in URGENT_KEYWORDS if kw in text)
    high_score   = sum(1 for kw in HIGH_KEYWORDS   if kw in text)
    medium_score = sum(1 for kw in MEDIUM_KEYWORDS if kw in text)

    # Text length features
    title_len = len(title)
    desc_len  = len(description)
    word_count = len(text.split())

    # Due date features
    due_urgency = 0
    if   days_until_due < 0:   due_urgency = 5   # overdue
    elif days_until_due == 0:  due_urgency = 4   # today
    elif days_until_due <= 1:  due_urgency = 3   # tomorrow
    elif days_until_due <= 3:  due_urgency = 2   # this week
    elif days_until_due <= 7:  due_urgency = 1   # within a week
    else:                       due_urgency = 0   # future

    # Category encoding
    cat = category.lower() if category else "other"
    cat_idx = CATEGORIES.index(cat) if cat in CATEGORIES else len(CATEGORIES) - 1

    return np.array([
        urgent_score,
        high_score,
        medium_score,
        title_len,
        desc_len,
        word_count,
        days_until_due if days_until_due >= 0 else -1,
        due_urgency,
        cat_idx,
    ], dtype=float)

# ─── Synthetic Training Data ───────────────────────────────────────────────────

def generate_training_data(n_samples: int = 2000):
    """Generate a rich synthetic training dataset with realistic distributions."""
    np.random.seed(42)
    X, y = [], []

    high_tasks = [
        ("Urgent client meeting", "Must prepare slides and demo ASAP", "work"),
        ("Critical exam tomorrow", "Final exam, study all chapters immediately", "study"),
        ("Emergency budget review", "Boss needs report today, deadline tonight", "finance"),
        ("Job interview preparation", "Interview at 9am, must prepare urgent", "work"),
        ("Doctor appointment critical", "Important health checkup, vital visit", "health"),
        ("Project deadline submission", "Final submission due, overdue already", "work"),
        ("Pay rent overdue", "Rent payment is overdue critical penalty", "finance"),
        ("Fix production bug", "Critical system down, emergency fix required", "work"),
        ("Client presentation urgent", "Must finalize deck asap crucial deal", "work"),
        ("Tax filing deadline", "IRS deadline today mandatory filing", "finance"),
    ]
    medium_tasks = [
        ("Weekly team standup", "Prepare agenda for team meeting call", "work"),
        ("Review pull request", "Check and review code changes update", "work"),
        ("Schedule dentist appointment", "Book dentist for regular check", "health"),
        ("Prepare monthly report", "Compile data for monthly progress report", "work"),
        ("Follow up with vendor", "Email vendor about pending order", "work"),
        ("Update project tracker", "Keep project board updated with progress", "work"),
        ("Research new framework", "Explore options for next sprint planning", "work"),
        ("Grocery shopping", "Buy groceries for the week", "personal"),
        ("Team retrospective notes", "Document lessons learned from last sprint", "work"),
        ("Call insurance company", "Follow up on claim status update", "finance"),
    ]
    low_tasks = [
        ("Read industry articles", "Stay updated with tech trends", "personal"),
        ("Organize desktop files", "Clean up old project files", "personal"),
        ("Water the plants", "Remember to water the indoor plants", "home"),
        ("Update LinkedIn profile", "Add recent projects to profile", "personal"),
        ("Watch tutorial video", "Watch design patterns tutorial", "study"),
        ("Back up photos", "Move phone photos to hard drive", "personal"),
        ("Clean home office", "Tidy up workspace and desk", "home"),
        ("Read book chapter", "Continue reading productivity book", "personal"),
        ("Plan weekend activities", "Think about weekend plans", "personal"),
        ("Browse recipe ideas", "Find new recipes to try", "home"),
    ]

    # HIGH priority samples: overdue or very soon
    for _ in range(n_samples // 3):
        task = high_tasks[np.random.randint(len(high_tasks))]
        days = np.random.choice([-5, -3, -1, 0, 0, 1, 1, 2])
        feat = extract_features(task[0], task[1], days, task[2])
        X.append(feat); y.append("HIGH")

    # MEDIUM priority samples: 3–10 days out, moderate keywords
    for _ in range(n_samples // 3):
        task = medium_tasks[np.random.randint(len(medium_tasks))]
        days = np.random.randint(3, 10)
        feat = extract_features(task[0], task[1], days, task[2])
        X.append(feat); y.append("MEDIUM")

    # LOW priority samples: far future, generic keywords
    for _ in range(n_samples // 3):
        task = low_tasks[np.random.randint(len(low_tasks))]
        days = np.random.randint(10, 60)
        feat = extract_features(task[0], task[1], days, task[2])
        X.append(feat); y.append("LOW")

    return np.array(X), np.array(y)

# ─── Training ──────────────────────────────────────────────────────────────────

def train_and_save():
    print("🤖 Generating training data...")
    X, y = generate_training_data(3000)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("🎓 Training Gradient Boosting classifier...")
    model = RandomForestClassifier(
        n_estimators=50,
        max_depth=6,
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred))

    os.makedirs("ml", exist_ok=True)
    joblib.dump(model, "ml/priority_model.pkl")
    print("✅ Model saved to ml/priority_model.pkl")
    return model

if __name__ == "__main__":
    train_and_save()
