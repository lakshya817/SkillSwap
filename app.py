
import os

import mysql.connector
from flask import Flask, jsonify

app = Flask(__name__)


def get_db_connection():
    """Create a connection to the SkillSwap MySQL database."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "skillswap"),
        connection_timeout=5,
    )


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
    """Check whether SkillSwap can connect to its configured database."""
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
        app.logger.exception("SkillSwap database connection failed")

        return jsonify({
            "status": "unavailable",
            "database": "disconnected"
        }), 503

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
