import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "zumba.db"

CLASS_SCHEDULE = [
    {
        "title": "Sunrise Cardio Flow",
        "day": "Monday",
        "time": "6:30 AM",
        "coach": "Anika",
        "level": "All levels",
        "capacity": 18,
    },
    {
        "title": "Power Pulse Zumba",
        "day": "Wednesday",
        "time": "7:00 PM",
        "coach": "Rhea",
        "level": "Intermediate",
        "capacity": 22,
    },
    {
        "title": "Weekend Fiesta Burn",
        "day": "Saturday",
        "time": "9:00 AM",
        "coach": "Maya",
        "level": "Beginner friendly",
        "capacity": 24,
    },
]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["DATABASE"] = os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH))
    app.config["STUDIO_NAME"] = os.getenv("STUDIO_NAME", "Pulse & Rhythm Zumba")
    app.config["CONTACT_EMAIL"] = os.getenv("CONTACT_EMAIL", "hello@pulseandrhythm.com")
    app.config["CONTACT_PHONE"] = os.getenv("CONTACT_PHONE", "+91 98765 43210")
    app.config["ADMIN_EMAIL"] = os.getenv(
        "ADMIN_EMAIL", "patilhimanshu146@gmail.com"
    )
    app.config["SCHEDULER_INTERVAL_SECONDS"] = int(
        os.getenv("SCHEDULER_INTERVAL_SECONDS", "120")
    )

    register_database(app)
    register_routes(app)
    register_scheduler(app)

    return app


def register_database(app: Flask) -> None:
    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    def close_db(_error=None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db() -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            class_name TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS automation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
            connection.executescript(schema)
            connection.commit()

    app.teardown_appcontext(close_db)
    app.get_db = get_db  # type: ignore[attr-defined]
    app.init_db = init_db  # type: ignore[attr-defined]

    with app.app_context():
        init_db()


def insert_automation_log(app: Flask, job_name: str, details: str) -> None:
    with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
        connection.execute(
            """
            INSERT INTO automation_runs (job_name, details, created_at)
            VALUES (?, ?, ?)
            """,
            (job_name, details, datetime.now().isoformat(timespec="seconds")),
        )
        connection.commit()


def follow_up_new_bookings(app: Flask) -> None:
    cutoff = datetime.now() - timedelta(minutes=1)
    with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, name, email, class_name
            FROM bookings
            WHERE status = 'new' AND created_at <= ?
            ORDER BY created_at ASC
            """,
            (cutoff.isoformat(timespec="seconds"),),
        ).fetchall()

        if not rows:
            insert_automation_log(
                app,
                "Lead Follow-up",
                "No new bookings were ready for automated follow-up.",
            )
            return

        booking_ids = [str(row["id"]) for row in rows]
        connection.executemany(
            "UPDATE bookings SET status = 'follow-up queued' WHERE id = ?",
            [(row["id"],) for row in rows],
        )
        connection.commit()

    details = (
        f"Queued follow-up for {len(rows)} booking(s): "
        + ", ".join(f"#{row['id']} {row['name']}" for row in rows)
    )
    insert_automation_log(app, "Lead Follow-up", details)


def publish_schedule_digest(app: Flask) -> None:
    summary = ", ".join(
        f"{item['day']} {item['time']} - {item['title']}" for item in CLASS_SCHEDULE
    )
    insert_automation_log(
        app,
        "Schedule Digest",
        f"Published class digest for website widgets and staff review: {summary}",
    )


def prepare_class_reminders(app: Flask) -> None:
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=1)
    with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, name, class_name, preferred_date
            FROM bookings
            WHERE date(preferred_date) BETWEEN date(?) AND date(?)
            ORDER BY preferred_date ASC, created_at ASC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

    if not rows:
        insert_automation_log(
            app,
            "Reminder Prep",
            "No upcoming trial classes needed reminder prep in the next 24 hours.",
        )
        return

    details = (
        f"Prepared reminder list for {len(rows)} upcoming booking(s): "
        + ", ".join(f"{row['name']} - {row['class_name']}" for row in rows[:5])
    )
    insert_automation_log(app, "Reminder Prep", details)


def review_capacity_watch(app: Flask) -> None:
    with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
        connection.row_factory = sqlite3.Row
        classes = []
        for schedule_item in CLASS_SCHEDULE:
            total = connection.execute(
                """
                SELECT COUNT(*)
                FROM bookings
                WHERE class_name = ?
                """,
                (schedule_item["title"],),
            ).fetchone()[0]
            classes.append(
                f"{schedule_item['title']}: {total}/{schedule_item['capacity']} booked"
            )

    insert_automation_log(
        app,
        "Capacity Watch",
        "Capacity snapshot recorded. " + "; ".join(classes),
    )


def register_scheduler(app: Flask) -> None:
    scheduler = BackgroundScheduler(daemon=True, timezone="Asia/Kolkata")

    scheduler.add_job(
        lambda: follow_up_new_bookings(app),
        trigger="interval",
        seconds=app.config["SCHEDULER_INTERVAL_SECONDS"],
        id="lead-follow-up",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: publish_schedule_digest(app),
        trigger="interval",
        hours=6,
        id="schedule-digest",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: prepare_class_reminders(app),
        trigger="interval",
        hours=4,
        id="reminder-prep",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: review_capacity_watch(app),
        trigger="interval",
        hours=8,
        id="capacity-watch",
        replace_existing=True,
    )
    scheduler.start()
    app.scheduler = scheduler  # type: ignore[attr-defined]


def register_routes(app: Flask) -> None:
    def admin_session_active() -> bool:
        return session.get("admin_email") == app.config["ADMIN_EMAIL"]

    @app.route("/")
    def home():
        db = app.get_db()
        booking_count = db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        automation_count = db.execute(
            "SELECT COUNT(*) FROM automation_runs"
        ).fetchone()[0]
        upcoming_trials = db.execute(
            """
            SELECT COUNT(*)
            FROM bookings
            WHERE date(preferred_date) >= date('now')
            """
        ).fetchone()[0]
        return render_template(
            "index.html",
            classes=CLASS_SCHEDULE,
            booking_count=booking_count,
            automation_count=automation_count,
            upcoming_trials=upcoming_trials,
            studio_name=app.config["STUDIO_NAME"],
            admin_logged_in=admin_session_active(),
        )

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    @app.route("/book", methods=["POST"])
    def book_class():
        form = request.form
        required_fields = ["name", "email", "phone", "class_name", "preferred_date"]
        if any(not form.get(field, "").strip() for field in required_fields):
            flash("Please complete all required booking fields.", "error")
            return redirect(url_for("home"))

        db = app.get_db()
        db.execute(
            """
            INSERT INTO bookings (
                name, email, phone, class_name, preferred_date, message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form["name"].strip(),
                form["email"].strip(),
                form["phone"].strip(),
                form["class_name"].strip(),
                form["preferred_date"].strip(),
                form.get("message", "").strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        db.commit()

        flash(
            "Your spot request is in. Our automation queue will follow up shortly.",
            "success",
        )
        return redirect(url_for("home"))

    @app.route("/admin", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            if email == app.config["ADMIN_EMAIL"].lower():
                session["admin_email"] = email
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_dashboard"))

            session.pop("admin_email", None)
            flash("This email has visitor access only.", "error")

        return render_template(
            "admin_login.html",
            studio_name=app.config["STUDIO_NAME"],
            admin_email=app.config["ADMIN_EMAIL"],
            admin_logged_in=admin_session_active(),
        )

    @app.route("/admin/dashboard")
    def admin_dashboard():
        if not admin_session_active():
            flash("Please sign in with the admin email to open the dashboard.", "error")
            return redirect(url_for("admin_login"))

        db = app.get_db()
        bookings = db.execute(
            """
            SELECT id, name, email, class_name, preferred_date, status, created_at
            FROM bookings
            ORDER BY created_at DESC
            LIMIT 10
            """
        ).fetchall()
        automation_runs = db.execute(
            """
            SELECT job_name, details, created_at
            FROM automation_runs
            ORDER BY created_at DESC
            LIMIT 8
            """
        ).fetchall()
        stats = {
            "total_bookings": db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
            "new_leads": db.execute(
                "SELECT COUNT(*) FROM bookings WHERE status = 'new'"
            ).fetchone()[0],
            "queued_followups": db.execute(
                "SELECT COUNT(*) FROM bookings WHERE status = 'follow-up queued'"
            ).fetchone()[0],
            "automation_runs": db.execute(
                "SELECT COUNT(*) FROM automation_runs"
            ).fetchone()[0],
        }
        return render_template(
            "admin.html",
            bookings=bookings,
            automation_runs=automation_runs,
            stats=stats,
            studio_name=app.config["STUDIO_NAME"],
        )

    @app.route("/admin/logout", methods=["POST"])
    def admin_logout():
        session.pop("admin_email", None)
        flash("Admin session closed.", "success")
        return redirect(url_for("admin_login"))


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
