
import os
import re
import uuid
from functools import wraps
from urllib.parse import urlparse
from datetime import datetime

import mysql.connector
from flask import (
    Flask, jsonify, request, session, render_template,
    redirect, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-only-change-this"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    MAX_CONTENT_LENGTH=100 * 1024 * 1024
)

# =========================================
# UPLOAD STORAGE CONFIGURATION
# =========================================

# Azure App Service sets WEBSITE_INSTANCE_ID.
# GitHub Actions and local environments use instance/uploads.

if os.environ.get("WEBSITE_INSTANCE_ID"):
    UPLOAD_FOLDER = "/home/data/skillswap_uploads"
else:
    UPLOAD_FOLDER = os.path.join(app.instance_path, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DOCUMENT_EXTENSIONS = {"pdf", "ppt", "pptx", "doc", "docx"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================
# DATABASE CONNECTION
# =========================================

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "skillswap"),
        connection_timeout=5,
    )


# =========================================
# AUTHENTICATION HELPERS
# =========================================

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Login required"}), 401
        return function(*args, **kwargs)
    return wrapper


def page_login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return function(*args, **kwargs)
    return wrapper


def valid_url(value):
    if not value or not isinstance(value, str):
        return False

    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        return False


# =========================================
# FILE UPLOAD HELPER
# =========================================

def save_uploaded_file(upload, allowed_extensions):
    if not upload or not upload.filename:
        return None

    original_name = secure_filename(upload.filename)

    if not original_name or "." not in original_name:
        raise ValueError("Invalid filename")

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions:
        raise ValueError(
            "Unsupported file format. Allowed formats: "
            + ", ".join(sorted(allowed_extensions))
        )

    stored_name = f"{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(UPLOAD_FOLDER, stored_name)

    upload.save(file_path)

    return {
        "url": f"/uploads/{stored_name}",
        "filename": original_name,
        "mime_type": upload.mimetype or "application/octet-stream",
        "size": os.path.getsize(file_path)
    }


# =========================================
# FRONTEND ROUTES
# =========================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/courses")
@page_login_required
def courses_page():
    return render_template("courses.html")


@app.route("/add-lesson")
@page_login_required
def add_lesson_page():
    return render_template("add_lesson.html")


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=False
    )


# =========================================
# HEALTH CHECK ROUTES
# =========================================

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


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "File too large. Maximum upload size is 100 MB."
    }), 413


# =========================================
# REGISTRATION API
# =========================================

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

        session.clear()
        session["user_id"] = user_id

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


# =========================================
# LOGIN API
# =========================================

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


# =========================================
# LOGOUT API
# =========================================

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


# =========================================
# USER PROFILE API
# =========================================

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


# =========================================
# COURSES API
# =========================================

@app.route("/api/courses", methods=["GET"])
def get_courses():
    connection = None
    cursor = None

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                c.course_id,
                c.title,
                c.category,
                c.description,
                c.level,
                c.language,
                c.thumbnail_url,
                c.instructor_id,
                u.full_name AS instructor_name,
                c.created_at,
                COUNT(DISTINCT e.enrollment_id) AS enrollment_count
            FROM courses c
            JOIN users u ON c.instructor_id = u.user_id
            LEFT JOIN enrollments e
                ON c.course_id = e.course_id
                AND e.status = 'ACTIVE'
            WHERE c.status = 'PUBLISHED'
        """

        params = []

        if search:
            query += " AND (c.title LIKE %s OR c.description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        if category:
            query += " AND c.category = %s"
            params.append(category)

        if level:
            query += " AND c.level = %s"
            params.append(level)

        query += """
            GROUP BY c.course_id
            ORDER BY c.created_at DESC
        """

        cursor.execute(query, params)

        return jsonify({"courses": cursor.fetchall()}), 200

    except mysql.connector.Error:
        app.logger.exception("Course listing error")
        return jsonify({"error": "Unable to load courses"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/courses", methods=["POST"])
@login_required
def create_course():
    data = request.get_json(silent=True) or {}

    title = data.get("title", "").strip()
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    level = data.get("level", "BEGINNER").upper()
    language = data.get("language", "").strip() or None
    thumbnail_url = data.get("thumbnail_url", "").strip() or None

    if not title or len(title) > 150:
        return jsonify({"error": "Enter a valid course title"}), 400

    if not category or len(category) > 100:
        return jsonify({"error": "Enter a valid category"}), 400

    if not description:
        return jsonify({"error": "Course description is required"}), 400

    if level not in {"BEGINNER", "INTERMEDIATE", "ADVANCED"}:
        return jsonify({"error": "Invalid course level"}), 400

    if thumbnail_url and not valid_url(thumbnail_url):
        return jsonify({"error": "Invalid thumbnail URL"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO courses (
                instructor_id, title, category, description,
                level, language, thumbnail_url, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'PUBLISHED')
            """,
            (
                session["user_id"], title, category, description,
                level, language, thumbnail_url
            )
        )

        connection.commit()

        return jsonify({
            "message": "Course published successfully",
            "course_id": cursor.lastrowid
        }), 201

    except mysql.connector.Error:
        app.logger.exception("Course creation error")
        return jsonify({"error": "Unable to create course"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/courses/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll_course(course_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT course_id, instructor_id
            FROM courses
            WHERE course_id = %s AND status = 'PUBLISHED'
            """,
            (course_id,)
        )

        course = cursor.fetchone()

        if not course:
            return jsonify({"error": "Course not found"}), 404

        user_id = session["user_id"]

        if course["instructor_id"] == user_id:
            return jsonify({
                "error": "You cannot enroll in your own course"
            }), 400

        cursor.execute(
            """
            INSERT INTO enrollments (course_id, student_id)
            VALUES (%s, %s)
            """,
            (course_id, user_id)
        )

        connection.commit()

        return jsonify({"message": "Enrollment successful"}), 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "error": "You are already enrolled in this course"
        }), 409

    except mysql.connector.Error:
        app.logger.exception("Course enrollment error")
        return jsonify({"error": "Unable to enroll"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


# =========================================
# LESSONS API
# =========================================

@app.route("/api/lessons", methods=["GET"])
def get_lessons():
    connection = None
    cursor = None

    lesson_type = request.args.get("type", "").strip().upper()
    search = request.args.get("search", "").strip()

    if lesson_type and lesson_type not in {"LIVE", "RECORDED", "UPLOAD"}:
        return jsonify({"error": "Invalid lesson type"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                l.lesson_id,
                l.course_id,
                l.instructor_id,
                l.title,
                l.description,
                l.lesson_type,
                l.meeting_url,
                l.scheduled_at,
                l.duration_minutes,
                l.content_url,
                l.original_filename,
                l.mime_type,
                l.created_at,
                u.full_name AS instructor_name,
                c.title AS course_title
            FROM lessons l
            JOIN users u ON l.instructor_id = u.user_id
            LEFT JOIN courses c ON l.course_id = c.course_id
            WHERE l.status = 'PUBLISHED'
        """

        params = []

        if lesson_type:
            query += " AND l.lesson_type = %s"
            params.append(lesson_type)

        if search:
            query += " AND (l.title LIKE %s OR l.description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY l.created_at DESC"

        cursor.execute(query, params)

        return jsonify({"lessons": cursor.fetchall()}), 200

    except mysql.connector.Error:
        app.logger.exception("Lesson listing error")
        return jsonify({"error": "Unable to load lessons"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/lessons", methods=["POST"])
@login_required
def create_lesson():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    lesson_type = request.form.get("lesson_type", "").strip().upper()
    course_id = request.form.get("course_id", "").strip()
    meeting_url = request.form.get("meeting_url", "").strip()
    scheduled_at = request.form.get("scheduled_at", "").strip()
    content_url = request.form.get("content_url", "").strip()
    duration = request.form.get("duration_minutes", "").strip()

    upload = request.files.get("file")

    if not title or len(title) > 150:
        return jsonify({"error": "Enter a valid lesson title"}), 400

    if not description:
        return jsonify({"error": "Lesson description is required"}), 400

    if lesson_type not in {"LIVE", "RECORDED", "UPLOAD"}:
        return jsonify({"error": "Select a valid lesson format"}), 400

    parsed_course_id = None

    if course_id:
        try:
            parsed_course_id = int(course_id)
            if parsed_course_id <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({"error": "Invalid course selection"}), 400

    parsed_duration = None

    if duration:
        try:
            parsed_duration = int(duration)
            if not 1 <= parsed_duration <= 600:
                raise ValueError()
        except ValueError:
            return jsonify({"error": "Duration must be 1–600 minutes"}), 400

    if lesson_type == "LIVE":
        if not valid_url(meeting_url):
            return jsonify({"error": "Enter a valid meeting URL"}), 400

        if not scheduled_at:
            return jsonify({"error": "Choose a lesson date and time"}), 400

        try:
            datetime.fromisoformat(scheduled_at)
        except ValueError:
            return jsonify({"error": "Invalid lesson date and time"}), 400

        if upload:
            return jsonify({
                "error": "Live lessons cannot have an uploaded file"
            }), 400

    elif lesson_type == "RECORDED":
        if not upload and not valid_url(content_url):
            return jsonify({
                "error": "Upload a video or provide a valid video URL"
            }), 400

    elif lesson_type == "UPLOAD":
        if not upload:
            return jsonify({
                "error": "Choose a document to upload"
            }), 400

        if content_url:
            return jsonify({
                "error": "Uploaded lessons use a file, not a URL"
            }), 400

    connection = None
    cursor = None
    saved_file = None

    try:
        if upload:
            allowed = (
                VIDEO_EXTENSIONS
                if lesson_type == "RECORDED"
                else DOCUMENT_EXTENSIONS
            )

            saved_file = save_uploaded_file(upload, allowed)
            content_url = saved_file["url"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if parsed_course_id is not None:
            cursor.execute(
                """
                SELECT course_id
                FROM courses
                WHERE course_id = %s
                  AND instructor_id = %s
                  AND status = 'PUBLISHED'
                """,
                (parsed_course_id, session["user_id"])
            )

            if not cursor.fetchone():
                if saved_file:
                    os.remove(
                        os.path.join(
                            UPLOAD_FOLDER,
                            saved_file["url"].split("/")[-1]
                        )
                    )

                return jsonify({
                    "error": "Course not found or you do not own it"
                }), 403

        cursor.execute(
            """
            INSERT INTO lessons (
                course_id, instructor_id, title, description,
                lesson_type, meeting_url, scheduled_at,
                duration_minutes, content_url,
                original_filename, mime_type, file_size_bytes,
                status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, 'PUBLISHED'
            )
            """,
            (
                parsed_course_id,
                session["user_id"],
                title,
                description,
                lesson_type,
                meeting_url if lesson_type == "LIVE" else None,
                scheduled_at if lesson_type == "LIVE" else None,
                parsed_duration,
                content_url or None,
                saved_file["filename"] if saved_file else None,
                saved_file["mime_type"] if saved_file else None,
                saved_file["size"] if saved_file else None
            )
        )

        connection.commit()

        return jsonify({
            "message": "Lesson published successfully",
            "lesson_id": cursor.lastrowid
        }), 201

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except OSError:
        app.logger.exception("Lesson file storage error")
        return jsonify({"error": "Unable to save uploaded file"}), 500

    except mysql.connector.Error:
        app.logger.exception("Lesson creation error")

        if saved_file:
            try:
                os.remove(
                    os.path.join(
                        UPLOAD_FOLDER,
                        saved_file["url"].split("/")[-1]
                    )
                )
            except OSError:
                pass

        return jsonify({"error": "Unable to publish lesson"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/my-lessons", methods=["GET"])
@login_required
def get_my_lessons():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                lesson_id, course_id, title, description,
                lesson_type, meeting_url, scheduled_at,
                duration_minutes, content_url,
                original_filename, status, created_at
            FROM lessons
            WHERE instructor_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )

        return jsonify({"lessons": cursor.fetchall()}), 200

    except mysql.connector.Error:
        app.logger.exception("My lessons error")
        return jsonify({"error": "Unable to load your lessons"}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


# =========================================
# APPLICATION START
# =========================================

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

