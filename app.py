import os
import urllib.parse
import requests
from flask import Flask, Blueprint, render_template, request

app = Flask(__name__)

HIBP_API_KEY = os.getenv("HIBP_API_KEY")
HIBP_USER_AGENT = os.getenv("HIBP_USER_AGENT", "ryanhenson-hibp")
HIBP_BASE_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/"

# Health check at root — used by the ALB to verify the container is alive.
# Lives outside the blueprint so the ALB can reach /health directly,
# without needing to know anything about /tools/hibp.
@app.route("/health")
def health():
    return {"status": "ok"}, 200

# Blueprint groups all app routes under /tools/hibp.
# When the ALB forwards /tools/hibp/* to this container, Flask matches
# these routes correctly without any extra nginx or path-stripping config.
bp = Blueprint("hibp", __name__, url_prefix="/tools/hibp")

@bp.route("/", methods=["GET"], strict_slashes=False)
def home():
    return render_template("index.html")

@bp.route("/check", methods=["POST"])
def check_email():
    email = request.form.get("email", "").strip()

    if not email:
        return render_template("index.html", error="Please enter an email address.")

    if not HIBP_API_KEY:
        return render_template("index.html", error="Server is missing HIBP_API_KEY.")

    encoded_email = urllib.parse.quote(email)
    url = f"{HIBP_BASE_URL}{encoded_email}?truncateResponse=false"

    headers = {
        "hibp-api-key": HIBP_API_KEY,
        "user-agent": HIBP_USER_AGENT
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        breaches = response.json()
        return render_template("index.html", email=email, breaches=breaches)

    if response.status_code == 404:
        return render_template("index.html", email=email, breaches=[])

    return render_template(
        "index.html",
        error=f"HIBP API returned unexpected status: {response.status_code}"
    )

app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)  # nosec B104 - intentional for local dev
