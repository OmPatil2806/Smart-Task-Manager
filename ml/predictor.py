"""
Predictor — rule-based with category boost + user-defined custom keywords.
Custom keywords are stored in ml/custom_keywords.json and editable via API.
"""
import re, json, os

# ── Default keyword lists ──────────────────────────────────────────────────────
DEFAULT_HIGH_WORDS = {
    "urgent","asap","immediately","critical","emergency","deadline",
    "overdue","crucial","vital","exam","interview","boss","today",
    "important","must","required","due","final","last","alert","priority"
}
DEFAULT_MEDIUM_WORDS = {
    "meeting","presentation","report","review","submit","call",
    "prepare","follow","update","schedule","client","project",
    "task","work","check","send","reply","finish","complete","plan"
}

# ── Category priority boosts ───────────────────────────────────────────────────
# Each category has a minimum floor priority and a days threshold boost
CATEGORY_RULES = {
    "finance": {"floor": "MEDIUM", "high_if_days_lte": 7},   # bills, taxes → bump up
    "health":  {"floor": "MEDIUM", "high_if_days_lte": 3},   # doctor, meds → bump up
    "work":    {"floor": "LOW",    "high_if_days_lte": 2},   # work tasks stricter
    "study":   {"floor": "LOW",    "high_if_days_lte": 3},   # exams closer = high
    "home":    {"floor": "LOW",    "high_if_days_lte": 14},
    "personal":{"floor": "LOW",    "high_if_days_lte": 30},
    "other":   {"floor": "LOW",    "high_if_days_lte": 30},
}

PRIORITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
RANK_PRIORITY = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}

# ── Custom keywords file ───────────────────────────────────────────────────────
KEYWORDS_FILE = os.path.join(os.path.dirname(__file__), "custom_keywords.json")

def load_custom_keywords() -> dict:
    """Load user-defined keywords from JSON file."""
    if os.path.exists(KEYWORDS_FILE):
        try:
            with open(KEYWORDS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"HIGH": [], "MEDIUM": [], "LOW": []}

def save_custom_keywords(data: dict):
    """Save user-defined keywords to JSON file."""
    with open(KEYWORDS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_all_keywords() -> dict:
    """Merge default + custom keywords."""
    custom = load_custom_keywords()
    return {
        "HIGH":   DEFAULT_HIGH_WORDS   | set(w.lower() for w in custom.get("HIGH",   [])),
        "MEDIUM": DEFAULT_MEDIUM_WORDS | set(w.lower() for w in custom.get("MEDIUM", [])),
        "LOW":    set(w.lower() for w in custom.get("LOW", [])),
    }

# ── Core prediction logic ──────────────────────────────────────────────────────
def _predict(title: str, description: str, days: float, category: str = "other") -> str:
    text      = (title + " " + description).lower()
    words     = set(re.findall(r'\w+', text))
    kw        = get_all_keywords()
    cat_rule  = CATEGORY_RULES.get(category.lower(), CATEGORY_RULES["other"])

    # Step 1: base priority from days
    if   days < 0:   base = "HIGH"
    elif days <= 1:  base = "HIGH"
    elif days <= 5:  base = "MEDIUM"
    else:            base = "LOW"

    # Step 2: keyword override
    # HIGH/MEDIUM keywords can only raise priority, never lower it
    # LOW keywords act as a cap — suppress escalation unless overdue/today
    if words & kw["HIGH"]:
        kw_priority = "HIGH"
    elif words & kw["MEDIUM"]:
        kw_priority = "MEDIUM"
    elif words & kw["LOW"] and days > 1:
        # User said this is low priority — cap at LOW unless actually overdue/today
        return "LOW"
    else:
        kw_priority = "LOW"

    priority = RANK_PRIORITY[max(PRIORITY_RANK[base], PRIORITY_RANK[kw_priority])]

    # Step 3: category boost
    cat_floor = cat_rule["floor"]
    if days <= cat_rule["high_if_days_lte"]:
        cat_boost = "HIGH"
    else:
        cat_boost = cat_floor

    priority = RANK_PRIORITY[max(PRIORITY_RANK[priority], PRIORITY_RANK[cat_boost])]

    return priority


# ── Public API ─────────────────────────────────────────────────────────────────
def predict_priority(title, description, days_until_due, category="other"):
    return _predict(title, description, days_until_due, category)

def predict_priority_with_confidence(title, description, days_until_due, category="other"):
    priority = _predict(title, description, days_until_due, category)
    conf = {"HIGH": 0.1, "MEDIUM": 0.1, "LOW": 0.1}
    conf[priority] = 0.8
    return {"priority": priority, "confidence": conf}
