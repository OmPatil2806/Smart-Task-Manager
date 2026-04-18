"""
Task CRUD — works with or without login.
If logged in: uses session user_id.
If not logged in: uses guest user (id=1), auto-created.
"""

from flask import Blueprint, request, jsonify, session
from backend.database import get_db
from datetime import date, datetime

tasks_bp = Blueprint("tasks", __name__)


def get_user_id():
    """Return logged-in user id, or create/return guest id=1."""
    if "user_id" in session:
        return session["user_id"]
    # Guest mode — ensure guest row exists
    db = get_db()
    try:
        db.execute(
            "INSERT OR IGNORE INTO users (id, username, password_hash) VALUES (1,'guest','guest')"
        )
        db.commit()
    finally:
        db.close()
    return 1


def task_to_dict(row) -> dict:
    d = dict(row)
    if d.get("due_date"):
        try:
            due = datetime.strptime(d["due_date"], "%Y-%m-%d").date()
            d["days_until_due"] = (due - date.today()).days
            d["is_overdue"]     = d["days_until_due"] < 0 and d["status"] != "completed"
        except ValueError:
            d["days_until_due"] = None
            d["is_overdue"]     = False
    else:
        d["days_until_due"] = None
        d["is_overdue"]     = False
    return d


@tasks_bp.route("/tasks", methods=["GET"])
def get_tasks():
    uid    = get_user_id()
    sf     = request.args.get("status")
    pf     = request.args.get("priority")
    query  = "SELECT * FROM tasks WHERE user_id = ?"
    params = [uid]
    if sf in ("pending","completed"):       query += " AND status = ?";   params.append(sf)
    if pf in ("HIGH","MEDIUM","LOW"):       query += " AND priority = ?"; params.append(pf)
    query += (" ORDER BY CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,"
              " due_date ASC, created_at DESC")
    db = get_db()
    try:
        rows = db.execute(query, params).fetchall()
        return jsonify({"tasks": [task_to_dict(r) for r in rows]}), 200
    finally:
        db.close()


@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    uid  = get_user_id()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required."}), 400

    desc     = (data.get("description") or "").strip()
    category = (data.get("category") or "other").strip().lower()
    due_date = data.get("due_date") or None
    priority = data.get("priority", "MEDIUM")

    if due_date:
        try: datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError: return jsonify({"error": "Use YYYY-MM-DD for dates."}), 400
    if priority not in ("HIGH","MEDIUM","LOW"):
        priority = "MEDIUM"

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO tasks (user_id,title,description,category,due_date,priority)"
            " VALUES (?,?,?,?,?,?)",
            (uid, title, desc, category, due_date, priority)
        )
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify({"task": task_to_dict(row), "message": "Task created."}), 201
    finally:
        db.close()


@tasks_bp.route("/tasks/<int:tid>", methods=["PUT"])
def update_task(tid):
    uid = get_user_id()
    db  = get_db()
    try:
        ex = db.execute("SELECT * FROM tasks WHERE id=? AND user_id=?", (tid, uid)).fetchone()
        if not ex: return jsonify({"error": "Task not found."}), 404

        data     = request.get_json(silent=True) or {}
        title    = (data.get("title") or ex["title"]).strip()
        desc     = data.get("description", ex["description"])
        cat      = data.get("category",    ex["category"])
        due_date = data.get("due_date",    ex["due_date"])
        status   = data.get("status",      ex["status"])
        priority = data.get("priority",    ex["priority"])

        if due_date:
            try: datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError: return jsonify({"error": "Use YYYY-MM-DD."}), 400
        if status   not in ("pending","completed"):  status   = ex["status"]
        if priority not in ("HIGH","MEDIUM","LOW"):  priority = ex["priority"]

        db.execute(
            "UPDATE tasks SET title=?,description=?,category=?,due_date=?,status=?,priority=?"
            " WHERE id=? AND user_id=?",
            (title, desc, cat, due_date, status, priority, tid, uid)
        )
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        return jsonify({"task": task_to_dict(row)}), 200
    finally:
        db.close()


@tasks_bp.route("/tasks/<int:tid>", methods=["DELETE"])
def delete_task(tid):
    uid = get_user_id()
    db  = get_db()
    try:
        ex = db.execute("SELECT id FROM tasks WHERE id=? AND user_id=?", (tid, uid)).fetchone()
        if not ex: return jsonify({"error": "Not found."}), 404
        db.execute("DELETE FROM tasks WHERE id=?", (tid,))
        db.commit()
        return jsonify({"message": "Deleted.", "id": tid}), 200
    finally:
        db.close()


@tasks_bp.route("/tasks/<int:tid>/toggle", methods=["PATCH"])
def toggle_task(tid):
    uid = get_user_id()
    db  = get_db()
    try:
        row = db.execute("SELECT * FROM tasks WHERE id=? AND user_id=?", (tid, uid)).fetchone()
        if not row: return jsonify({"error": "Not found."}), 404
        new_st = "completed" if row["status"] == "pending" else "pending"
        db.execute("UPDATE tasks SET status=? WHERE id=?", (new_st, tid))
        db.commit()
        updated = db.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        return jsonify({"task": task_to_dict(updated)}), 200
    finally:
        db.close()
