import os
import urllib.parse
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

HIBP_API_KEY = os.getenv("HIBP_API_KEY")
HIBP_USER_AGENT = os.getenv("HIBP_USER_AGENT", "hibp-devsecops-demo")
HIBP_BASE_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/"

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
