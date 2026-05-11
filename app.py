import os

from flask import Flask, render_template


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SITE_TITLE"] = "For Bubu"

    scenes = [
        {
            "eyebrow": "For Bubu",
            "title": "There are some people who quietly become your whole world.",
            "text": (
                "You became that for me. Not loudly. Not all at once. Just softly, "
                "beautifully, and completely."
            ),
            "image": "images/memory-4.jpeg",
            "layout": "hero",
        },
        {
            "eyebrow": "The Softest Part",
            "title": "With you, even ordinary moments feel like something worth keeping.",
            "text": (
                "The way you smile, the way we stand close, the way every memory with you "
                "feels warmer than the day around it."
            ),
            "image": "images/memory-1.jpeg",
            "layout": "split-left",
        },
        {
            "eyebrow": "My Apology",
            "title": "Babu please mala maaf kar.",
            "text": (
                "Me nay krnr prt kdhi asa. This was supposed to make you happy, "
                "and it turned into my apology. Babu sorry so much."
            ),
            "image": "images/memory-6.jpeg",
            "layout": "centered",
        },
        {
            "eyebrow": "What Stays True",
            "title": "Even after the mistake, my heart still reaches for you first.",
            "text": (
                "I still love you. I still miss your softness. I still want to become "
                "better in the places where your heart needed more care from me."
            ),
            "image": "images/memory-2.jpeg",
            "layout": "split-right",
        },
    ]

    gallery = [
        {
            "image": "images/memory-3.jpeg",
            "caption": "A moment that still feels alive inside me.",
        },
        {
            "image": "images/memory-5.jpeg",
            "caption": "The kind of smile I never want to be the reason for losing.",
        },
        {
            "image": "images/memory-6.jpeg",
            "caption": "Us, exactly as I want to remember us.",
        },
    ]

    promises = [
        "I will be gentler with the way I speak.",
        "I will not repeat what hurt you.",
        "I will love you with more care than ego.",
    ]

    @app.route("/")
    def home():
        return render_template(
            "index.html",
            site_title=app.config["SITE_TITLE"],
            her_name="Bubu",
            his_name="Himanshu",
            scenes=scenes,
            gallery=gallery,
            promises=promises,
        )

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
