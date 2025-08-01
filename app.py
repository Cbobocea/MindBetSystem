import os
import sqlite3
import stripe
import requests
import random
import time
import json
from datetime import datetime
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify
)
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash

from football_data_connect import get_upcoming_fixtures, get_premier_league_standings
from simulate_from_dataorg import simulate_match_full
from esports_data_connect import get_supported_games, get_upcoming_esports_matches
from esports_simulation import simulate_esports_match

# === Load environment variables ===
load_dotenv()
APP_ENV = os.getenv("APP_ENV", "development")

# === Flask app setup ===
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "default-secret-key"

# === Email config (Flask-Mail) ===
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")
mail = Mail(app)

# === Flask Security Settings ===
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# === Security Middleware ===
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app)

# === Stripe API ===
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def refresh_subscription_status():
    if "email" in session:
        print("🔁 Refreshing subscription from DB for", session["email"])
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT is_subscriber FROM users WHERE email = ?", (session["email"],))
        row = c.fetchone()
        conn.close()
        session["is_subscriber"] = bool(row[0]) if row else False
        print(f"🧠 session['is_subscriber'] updated to: {session['is_subscriber']}")

def fetch_fixtures_for_league(league_code):
    from football_data_connect import headers
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches?status=SCHEDULED"
    response = requests.get(url, headers=headers)
    data = response.json()
    if 'matches' not in data:
        return []
    return [{
        "match_id": match['id'],
        "home_team": match['homeTeam']['name'],
        "away_team": match['awayTeam']['name'],
        "date": match['utcDate'][:10]
    } for match in data['matches']]


@app.route("/esports", methods=["GET", "POST"])
def esports():
    """Combined eSports page for all games and match simulations"""
    games = get_supported_games()
    selected_game = request.form.get("game", "csgo")  # Default to CSGO
    matches = []
    simulation = None
    dominant_result = None
    error = None

    if "email" in session:
        refresh_subscription_status()

    # Filter games to make sure selected_game is valid
    valid_game_ids = [g["id"] for g in games]
    if selected_game not in valid_game_ids and valid_game_ids:
        selected_game = valid_game_ids[0]

    try:
        if request.method == "POST":
            action = request.form.get("action")

            if action == "load":
                matches = get_upcoming_esports_matches(selected_game)
                print(f"Loaded {len(matches)} matches for {selected_game}")

            elif action == "simulate" and 'match' in request.form:
                today = datetime.now().strftime("%Y-%m-%d")
                if session.get("date") != today:
                    session["date"] = today
                    session["esports_simulations_today"] = 0

                is_subscribed = session.get("is_subscriber", False)
                if not is_subscribed and session.get("esports_simulations_today", 0) >= 3:
                    error = "❌ Free limit reached (3/day). Please upgrade!"
                    matches = get_upcoming_esports_matches(selected_game)
                    return render_template("esports.html",
                                           games=games,
                                           selected_game=selected_game,
                                           matches=matches,
                                           simulation=None,
                                           dominant_result=None,
                                           error=error)

                session["esports_simulations_today"] = session.get("esports_simulations_today", 0) + 1
                matches = get_upcoming_esports_matches(selected_game)

                try:
                    match_index = int(request.form.get("match"))
                    print(f"Selected match index: {match_index}, Total matches: {len(matches)}")

                    if match_index >= len(matches):
                        raise IndexError(f"Match index {match_index} out of range for {len(matches)} matches")

                    selected_match = matches[match_index]
                    print(f"Selected match: {selected_match}")

                    n_simulations = 10000 if session.get("is_subscriber") else 1000

                    # Debug output before simulation
                    print(
                        f"Running simulation for {selected_match['home_team']} vs {selected_match['away_team']} in {selected_game}")

                    simulation = simulate_esports_match(
                        selected_match,
                        selected_game,
                        n_simulations=n_simulations
                    )

                    print("Simulation complete:", simulation)

                    if APP_ENV == "production":
                        time.sleep(2)

                    if simulation and "results" in simulation:
                        dominant_result = max(simulation["results"], key=simulation["results"].get)
                except (ValueError, IndexError) as e:
                    print(f"Error in simulation: {e}")
                    error = f"Failed to run simulation: {str(e)}"
                except Exception as e:
                    print(f"Unexpected error in simulation: {type(e).__name__}: {e}")
                    error = "Unexpected error in simulation. Please try again."
        else:
            # On GET request, just load matches for the default game
            matches = get_upcoming_esports_matches(selected_game)

    except Exception as e:
        import traceback
        print(f"Error in esports route: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        error = "An error occurred. Please try again later."

    # Ensure we have something to return
    if not matches:
        matches = []

    return render_template("esports.html",
                           games=games,
                           selected_game=selected_game,
                           matches=matches,
                           simulation=simulation,
                           dominant_result=dominant_result,
                           error=error)



@app.route("/privacy")
def privacy():
    return render_template("privacy.html", now=datetime.now())

@app.route("/terms")
def terms():
    return render_template("terms.html", now=datetime.now())


@app.route("/", methods=["GET", "POST"])
def index():
    fixtures = []
    simulation = None
    dominant_result = None
    selected_league = "PL"
    error = None

    if "email" in session:
        refresh_subscription_status()

    if request.method == "POST":
        selected_league = request.form.get("league", "PL")
        action = request.form.get("action")
        fixtures = fetch_fixtures_for_league(selected_league)

        if action == "simulate" and 'match' in request.form:
            today = datetime.now().strftime("%Y-%m-%d")
            if session.get("date") != today:
                session["date"] = today
                session["simulations_today"] = 0

            is_subscribed = session.get("is_subscriber", False)
            if not is_subscribed and session.get("simulations_today", 0) >= 3:
                error = "❌ Free limit reached (3/day). Please upgrade!"
                return render_template("index.html", fixtures=fixtures, simulation=None, dominant_result=None, selected_league=selected_league, error=error)

            session["simulations_today"] = session.get("simulations_today", 0) + 1

            try:
                match_index = int(request.form.get("match"))
                selected_match = fixtures[match_index]
                standings = get_premier_league_standings()
                n_simulations = 10000 if session.get("is_subscriber") else 1000
                simulation = simulate_match_full(selected_match, standings, n_simulations=n_simulations)
                if APP_ENV == "production":
                    time.sleep(2)
                if simulation:
                    dominant_result = max(simulation["results"], key=simulation["results"].get)
            except (ValueError, IndexError):
                pass
    else:
        fixtures = fetch_fixtures_for_league(selected_league)

    return render_template("index.html", fixtures=fixtures, simulation=simulation, dominant_result=dominant_result, selected_league=selected_league, error=error)

@limiter.limit("5 per minute")
@app.route("/signup", methods=["GET", "POST"])
def signup():
    site_key = os.getenv("RECAPTCHA_SITE_KEY")
    secret_key = os.getenv("RECAPTCHA_SECRET_KEY")

    if request.method == "POST":
        # CSRF is automatically validated by Flask-WTF (if enabled)

        # Verify CAPTCHA
        # token = request.form.get("g-recaptcha-response")
        # recaptcha_response = requests.post(
        #     "https://www.google.com/recaptcha/api/siteverify",
        #     data={"secret": secret_key, "response": token}
        # ).json()

        # if not recaptcha_response.get("success"):
        #     return render_template("login.html", login_error="CAPTCHA failed.", site_key=site_key)

        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            return render_template("signup.html", signup_error="Passwords do not match.", site_key=site_key)

        password_hash = generate_password_hash(password)

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return render_template("signup.html", signup_error="Email already exists.", site_key=site_key)

        c.execute(
            "INSERT INTO users (email, password_hash, is_subscriber) VALUES (?, ?, 0)",
            (email, password_hash)
        )
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html", site_key=site_key)

def generate_code():
    return str(random.randint(100000, 999999))

@limiter.limit("5 per minute")
@app.route("/login", methods=["GET", "POST"])
def login():
    site_key = os.getenv("RECAPTCHA_SITE_KEY")
    secret_key = os.getenv("RECAPTCHA_SECRET_KEY")

    if request.method == "POST":
        token = request.form.get("g-recaptcha-response")
        recaptcha_response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": secret_key, "response": token}
        ).json()

        if not recaptcha_response.get("success"):
            return render_template("login.html", login_error="⚠️ CAPTCHA verification failed.", site_key=site_key)

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT id, password_hash, is_subscriber FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            code = generate_code()
            session["pending_user"] = {
                "id": user[0],
                "email": email,
                "is_subscriber": bool(user[2]),
                "code": code,
                "code_created": time.time()
            }

            # Send email
            msg = Message(
                subject="🔐 Mindbet Login Verification Code",
                sender=("Mindbet Systems", os.getenv("MAIL_USERNAME")),
                recipients=[email]
            )

            msg.body = f"Your login verification code is: {code}"  # Fallback text version

            msg.html = f"""
            <!DOCTYPE html>
            <html>
              <body style="font-family:Segoe UI, sans-serif; background-color:#f4f4f4; padding:20px;">
                <div style="max-width:480px; margin:0 auto; background:#fff; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.1); padding:30px;">
                  <div style="text-align:center;">
                    <img src="https://mindbet.store/static/img/logo.jpg" alt="Mindbet Logo" style="max-height:60px; margin-bottom:20px;" />
                    <h2 style="color:#1f6feb;">🔐 Verify Your Login</h2>
                  </div>
                  <p style="font-size:16px; color:#333;">Hi there 👋,</p>
                  <p style="font-size:16px; color:#333;">
                    Your one-time login code is:
                  </p>
                  <div style="font-size:28px; font-weight:bold; letter-spacing:3px; background:#eaf4ff; color:#1f6feb; padding:15px; border-radius:8px; text-align:center; margin:20px 0;">
                    {code}
                  </div>
                  <p style="font-size:14px; color:#555;">This code will expire in 5 minutes. If you didn’t try to log in, you can safely ignore this email.</p>
                  <hr style="border:none; border-top:1px solid #ddd; margin:30px 0;">
                  <p style="font-size:12px; color:#999; text-align:center;">Mindbet Systems • mindbet.store</p>
                </div>
              </body>
            </html>
            """
            mail.send(msg)

            return redirect("/verify")
        else:
            return render_template("login.html", login_error="Invalid email or password.", site_key=site_key)

    return render_template("login.html", site_key=site_key)

@app.route("/verify", methods=["GET", "POST"])
def verify_code():
    if request.method == "POST":
        user_input = request.form["code"]
        pending = session.get("pending_user")

        if not pending:
            return redirect("/login")

        if time.time() - pending.get("code_created", 0) > 300:
            session.pop("pending_user", None)
            return render_template("verify.html", error="⏱ Code expired. Please login again.")

        if user_input == pending["code"]:
            session["user_id"] = pending["id"]
            session["email"] = pending["email"]
            session["is_subscriber"] = pending["is_subscriber"]
            session.pop("pending_user")
            return redirect("/home")
        else:
            return render_template("verify.html", error="Invalid code.")

    return render_template("verify.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/account", methods=["GET", "POST"])
def account():
    if "email" not in session:
        return redirect("/login")

    email = session["email"]
    password_changed = False
    password_error = None

    if request.method == "POST":
        current_pw = request.form.get("current_password")
        new_pw = request.form.get("new_password")
        confirm_pw = request.form.get("confirm_password")

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        row = c.fetchone()

        if not row or not check_password_hash(row[0], current_pw):
            password_error = "❌ Current password is incorrect."
        elif new_pw != confirm_pw:
            password_error = "❌ New passwords do not match."
        elif len(new_pw) < 6:
            password_error = "❌ Password must be at least 6 characters."
        else:
            new_hash = generate_password_hash(new_pw)
            c.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, email))
            conn.commit()
            password_changed = True

        conn.close()

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT is_subscriber FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    is_subscriber = bool(row[0]) if row else False
    conn.close()

    session["is_subscriber"] = is_subscriber
    simulations_today = session.get("simulations_today", 0) if session.get("date") == datetime.now().strftime("%Y-%m-%d") else 0

    return render_template("account.html",
                           username=email.split("@")[0],
                           email=email,
                           is_subscriber=is_subscriber,
                           simulations_left=max(0, 3 - simulations_today),
                           member_since="2025-05-05",
                           password_changed=password_changed,
                           password_error=password_error)

@app.route("/success")
def success():
    if "email" in session:
        email = session["email"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("UPDATE users SET is_subscriber = 1 WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        session["is_subscriber"] = True
        return render_template("success.html", email=email)
    return redirect("/login")

@app.route("/cancel")
def cancel():
    return "<h2>❌ Payment canceled. Feel free to try again anytime.</h2>"

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = "whsec_a481a0f4008a475a902409b03f36cf7c07b565d0aa36c714cda579f54cddb87d"

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        metadata = session_obj.get('metadata', {})
        email = metadata.get('email')
        if email:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("UPDATE users SET is_subscriber = 1 WHERE email = ?", (email,))
            conn.commit()
            conn.close()

    return "Webhook received", 200

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": "price_1RXjYTFaDavGDLfpCJKQxU60",  # Your Stripe price ID
                "quantity": 1,
            }],
            mode="subscription",
            success_url=url_for('success', _external=True),
            cancel_url=url_for('cancel', _external=True),
            metadata={"email": session["email"]}
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 400

@app.route("/home")
def home():
    return render_template("landing.html", now=datetime.now())

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    success = False
    error = None

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        try:
            msg = Message(
                subject="📩 New Mindbet Contact Submission",
                sender=(name, email),  # appears as "User Name <user@email.com>"
                recipients=[os.getenv("CONTACT_EMAIL_TO")]
            )
            msg.body = f"""
New contact form submission:

From: {name}
Email: {email}

Message:
{message}
            """.strip()

            mail.send(msg)
            success = True

        except Exception as e:
            print(f"[❌ Mail Send Error] {e}")
            error = "Something went wrong. Please try again later."

    return render_template("contact.html", success=success, error=error, now=datetime.now())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
