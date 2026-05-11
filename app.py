import os

from flask import Flask, render_template


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SITE_TITLE"] = "For Bubu"

    memories = [
        {
            "image": "images/memory-1.jpeg",
            "caption": "One hug and the whole world feels quieter.",
        },
        {
            "image": "images/memory-2.jpeg",
            "caption": "Your smile always wins over every bad day.",
        },
        {
            "image": "images/memory-3.jpeg",
            "caption": "You and me, exactly where my heart feels at home.",
        },
        {
            "image": "images/memory-4.jpeg",
            "caption": "The softest kind of happiness is just being near you.",
        },
        {
            "image": "images/memory-5.jpeg",
            "caption": "Even ordinary moments feel special with you.",
        },
        {
            "image": "images/memory-6.jpeg",
            "caption": "You make every little memory worth keeping forever.",
        },
    ]

    promises = [
        "I will speak more softly when your heart needs care.",
        "I will not repeat what hurt you.",
        "I will show love with patience, not just words.",
    ]

    @app.route("/")
    def home():
        return render_template(
            "index.html",
            site_title=app.config["SITE_TITLE"],
            her_name="Bubu",
            his_name="Himanshu",
            apology_line=(
                "Babu please mala maaf kar. Me nahi karnaar parat kadhi asa. "
                "This was supposed to make you happy, and it turned into my apology. "
                "Babu sorry so much."
            ),
            memories=memories,
            promises=promises,
        )

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
