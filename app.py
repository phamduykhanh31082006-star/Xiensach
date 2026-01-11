from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta, timezone
import uuid
import requests
import re
import time

app = Flask(__name__)

# ===== CONFIG =====
VIETNAM_TZ = timezone(timedelta(hours=7))

SPAM_LIMIT_MINUTES = 3          # chặn spam cùng IP + phone
TOKEN_EXPIRE_SECONDS = 120     # token chỉ sống 2 phút

order_cache = {}               # {phone_ip: datetime}
used_tokens = {}               # {token: timestamp}

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxb9XhVyTbU8uJ_KpVSfBrpmOjwa4U62Ncah_uIrlejF00Dv1zrf87RYcu1OrfmVhEPew/exec"

TELEGRAM_BOT_TOKEN = "8338747162:AAFnIT2NHXD0ha--Mp5ZsCvMNHr7pDIYxyg"
TELEGRAM_CHAT_ID = "6285097453"

# ===== ROUTES =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/program")
def program():
    return render_template("program.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/success")
def success():
    order_id = request.args.get("order_id")
    if not order_id:
        return redirect("/")
    return render_template("success.html", order_id=order_id)

# ===== PLACE ORDER =====
@app.route("/place-order", methods=["POST"])
def place_order():
    # ===== HONEYPOT =====
    if request.form.get("website"):
        return redirect("/")

    # ===== GET DATA =====
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    note = request.form.get("note", "").strip()

    cart_text = request.form.get("cart_text", "").strip()
    sauce_text = request.form.get("sauce_text", "").strip()
    total = request.form.get("total", "").strip()

    order_token = request.form.get("order_token")
    timestamp = request.form.get("timestamp")

    # ===== BASIC VALIDATE =====
    if not all([name, phone, address, cart_text, total, order_token, timestamp]):
        return redirect(url_for("cart"))

    # ===== PHONE VALIDATE (VN) =====
    if not re.fullmatch(r"0\d{9}", phone):
        return redirect(url_for("cart"))

    # ===== TOTAL VALIDATE =====
    try:
        total_int = int(total)
        if total_int <= 0:
            return redirect(url_for("cart"))
    except:
        return redirect(url_for("cart"))

    # ===== TIMESTAMP VALIDATE =====
    try:
        ts = int(timestamp)
        now_ts = int(time.time() * 1000)
        if abs(now_ts - ts) > TOKEN_EXPIRE_SECONDS * 1000:
            return redirect(url_for("cart"))
    except:
        return redirect(url_for("cart"))

    # ===== TOKEN REPLAY ATTACK =====
    if order_token in used_tokens:
        return redirect(url_for("cart"))

    used_tokens[order_token] = ts

    # cleanup token cũ
    for t, tts in list(used_tokens.items()):
        if now_ts - tts > TOKEN_EXPIRE_SECONDS * 1000:
            used_tokens.pop(t, None)

    # ===== SPAM LIMIT =====
    now = datetime.now(VIETNAM_TZ)
    ip = request.remote_addr or "unknown"
    spam_key = f"{phone}_{ip}"

    last_time = order_cache.get(spam_key)
    if last_time and now - last_time < timedelta(minutes=SPAM_LIMIT_MINUTES):
        return redirect(url_for("cart"))

    order_cache[spam_key] = now

    # ===== CREATE ORDER ID =====
    order_id = f"XS-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # ===== GOOGLE SHEET =====
    try:
        requests.post(
            GOOGLE_SCRIPT_URL,
            json={
                "order_id": order_id,
                "time": now.strftime("%d/%m/%Y %H:%M:%S"),
                "name": name,
                "phone": phone,
                "address": address,
                "items": cart_text,
                "sauces": sauce_text,
                "total": total_int,
                "note": note
            },
            timeout=10
        ).raise_for_status()
    except Exception as e:
        print("Google Sheet error:", e)
        return redirect(url_for("cart"))

    # ===== TELEGRAM =====
    try:
        msg = f"""🛎️ ĐƠN MỚI
Mã: {order_id}

👤 {name}
📞 {phone}
📍 {address}

🍢 {cart_text}
🥣 {sauce_text}

💰 {total_int:,}đ
📝 {note}
"""
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)

    return redirect(url_for("success", order_id=order_id, total=total_int))



if __name__ == "__main__":
    app.run(debug=True)
