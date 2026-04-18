import os, sys
from datetime import date, datetime
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, get_db
from backend.auth  import auth_bp
from backend.tasks import tasks_bp

app = Flask(__name__, static_folder="frontend", static_url_path="")
app.secret_key = "smart-todo-dev-secret-2024"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"]   = False

CORS(app, supports_credentials=True,
     origins=["http://localhost:5000", "http://127.0.0.1:5000"])

app.register_blueprint(auth_bp)
app.register_blueprint(tasks_bp)


#  ML Prediction 
@app.route("/predict-priority", methods=["POST"])
def predict_priority_route():
    data        = request.get_json(silent=True) or {}
    title       = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category    = (data.get("category") or "other").strip().lower()
    due_date    = data.get("due_date")

    if not title:
        return jsonify({"error": "Title required."}), 400

    days = 30.0
    if due_date:
        try:
            days = float((datetime.strptime(due_date, "%Y-%m-%d").date() - date.today()).days)
        except ValueError:
            pass

    from ml.predictor import predict_priority_with_confidence
    result = predict_priority_with_confidence(title, description, days, category)
    return jsonify(result), 200


#  Stats 
@app.route("/stats", methods=["GET"])
def stats():
    user_id = session.get("user_id", 1)
    db = get_db()
    try:
        rows      = db.execute(
            "SELECT status, priority, due_date FROM tasks WHERE user_id = ?",
            (user_id,)).fetchall()
        total     = len(rows)
        completed = sum(1 for r in rows if r["status"] == "completed")
        today_str = date.today().isoformat()
        return jsonify({
            "total":      total,
            "completed":  completed,
            "pending":    total - completed,
            "overdue":    sum(1 for r in rows if r["due_date"] and
                              r["due_date"] < today_str and r["status"] == "pending"),
            "due_today":  sum(1 for r in rows if r["due_date"] == today_str
                              and r["status"] == "pending"),
            "by_priority": {
                "HIGH":   sum(1 for r in rows if r["priority"]=="HIGH"   and r["status"]=="pending"),
                "MEDIUM": sum(1 for r in rows if r["priority"]=="MEDIUM" and r["status"]=="pending"),
                "LOW":    sum(1 for r in rows if r["priority"]=="LOW"    and r["status"]=="pending"),
            },
            "productivity_score": round(completed / total * 100 if total else 0, 1)
        }), 200
    finally:
        db.close()


#  Frontend 
@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found."}), 404


# Start 
if __name__ == "__main__":
    init_db()
    print("✅ DB ready")
    print("🌐 http://localhost:5000")
    app.run(debug=False, port=5000, host="0.0.0.0")


#  Custom Keywords API 
@app.route("/keywords", methods=["GET"])
def get_keywords():
    from ml.predictor import load_custom_keywords, DEFAULT_HIGH_WORDS, DEFAULT_MEDIUM_WORDS
    custom = load_custom_keywords()
    return jsonify({
        "custom":   custom,
        "defaults": {
            "HIGH":   sorted(DEFAULT_HIGH_WORDS),
            "MEDIUM": sorted(DEFAULT_MEDIUM_WORDS),
        }
    }), 200

@app.route("/keywords", methods=["POST"])
def save_keywords():
    from ml.predictor import save_custom_keywords
    data = request.get_json(silent=True) or {}
    keywords = {
        "HIGH":   [w.strip().lower() for w in data.get("HIGH",   []) if w.strip()],
        "MEDIUM": [w.strip().lower() for w in data.get("MEDIUM", []) if w.strip()],
        "LOW":    [w.strip().lower() for w in data.get("LOW",    []) if w.strip()],
    }
    save_custom_keywords(keywords)
    return jsonify({"message": "Keywords saved.", "keywords": keywords}), 200
