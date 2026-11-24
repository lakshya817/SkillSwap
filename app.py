
import os
import re
from functools import wraps

import mysql.connector
from flask import Flask, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "development-only-change-this")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production"
)


def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "skillswap"),
        connection_timeout=5,
    )


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Login required"}), 401
        return function(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return jsonify({
        "project": "SkillSwap",
        "message": "Welcome to SkillSwap!",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/db-health")
def database_health():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()

        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200

    except mysql.connector.Error:
        app.logger.exception("Database connection failed")
        return jsonify({
            "status": "unavailable",
            "database": "disconnected"
        }), 503

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not full_name or len(full_name) > 100:
        return jsonify({"error": "Enter a valid full name"}), 400

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"error": "Enter a valid email address"}), 400

    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        return jsonify({
            "error": "Password must be 8 to 128 characters"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (full_name, email, password_hash)
        )

        connection.commit()
        user_id = cursor.lastrowid

        return jsonify({
            "message": "Registration successful",
            "user_id": user_id
        }), 201

    except mysql.connector.IntegrityError as error:
        if error.errno == 1062:
            return jsonify({"error": "Email already registered"}), 409
        app.logger.exception("Registration integrity error")
        return jsonify({"error": "Registration failed"}), 400

    except mysql.connector.Error:
        app.logger.exception("Registration database error")
        return jsonify({"error": "Database unavailable"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not isinstance(password, str):
        return jsonify({"error": "Email and password required"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id, full_name, email, password_hash, role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({"error": "Invalid email or password"}), 401

        session.clear()
        session["user_id"] = user["user_id"]

        return jsonify({
            "message": "Login successful",
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }
        }), 200

    except mysql.connector.Error:
        app.logger.exception("Login database error")
        return jsonify({"error": "Database unavailable"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@app.route("/api/me", methods=["GET"])
@login_required
def get_profile():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id, full_name, email, role, created_at
            FROM users
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if not user:
            session.clear()
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user}), 200

    except mysql.connector.Error:
        app.logger.exception("Profile database error")
        return jsonify({"error": "Database unavailable"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

