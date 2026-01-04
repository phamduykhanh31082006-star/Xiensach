from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta, timezone
import uuid
import requests

app = Flask(__name__)

# ===== CONFIG =====
VIETNAM_TZ = timezone(timedelta(hours=7))
SPAM_LIMIT_MINUTES = 5   # khi test có thể để = 0
order_cache = {}

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxb9XhVyTbU8uJ_KpVSfBrpmOjwa4U62Ncah_uIrlejF00Dv1zrf87RYcu1OrfmVhEPew/exec"

TELEGRAM_BOT_TOKEN = "8338747162:AAFnIT2NHXD0ha--Mp5ZsCvMNHr7pDIYxyg"
TELEGRAM_CHAT_ID = "6285097453"

# ===== ROUTES CƠ BẢN =====
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

# ===== SUCCESS =====
@app.route("/success")
def success():
    order_id = request.args.get("order_id")
    if not order_id:
        return redirect("/")
    return render_template("success.html", order_id=order_id)

# ===== PLACE ORDER (FORM THUẦN – ĐÃ FIX) =====
@app.route("/place-order", methods=["POST"])
def place_order():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    note = request.form.get("note", "").strip()
    cart_text = request.form.get("cart_text", "").strip()
    sauce_text = request.form.get("sauce_text", "").strip()
    total = request.form.get("total", "").strip()

    # ===== VALIDATE CƠ BẢN =====
    if not name or not phone or not address or not cart_text:
        return redirect(url_for("cart"))

    now = datetime.now(VIETNAM_TZ)

    # ===== CHỐNG SPAM (CHỈ CHẶN TRƯỚC KHI GHI ĐƠN) =====
    last = order_cache.get(phone)
    if last and now - last < timedelta(minutes=SPAM_LIMIT_MINUTES):
        # KHÔNG ghi đơn → quay lại cart
        return redirect(url_for("cart"))

    # đánh dấu thời điểm đặt
    order_cache[phone] = now
    order_id = f"XS-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # ===== GHI GOOGLE SHEET (QUAN TRỌNG NHẤT) =====
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
                "total": total,
                "note": note
            },
            timeout=10
        ).raise_for_status()
    except Exception as e:
        print("Google Sheet error:", e)
        # CHƯA GHI ĐƠN → KHÔNG CHO QUA SUCCESS
        return redirect(url_for("cart"))

    # ===== TELEGRAM (LỖI KHÔNG ẢNH HƯỞNG SUCCESS) =====
    try:
        msg = f"""🛎️ ĐƠN MỚI
Mã: {order_id}

👤 Tên Khách: {name}
📞 SĐT: {phone}
📍 Đ/C: {address}

🍢 Món: {cart_text}

🥣 Nước chấm: {sauce_text}

💰 Tổng: {total}
📝 Ghi chú: {note}
"""
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram error (bỏ qua):", e)
        # ❗ KHÔNG redirect về cart nữa

    # ===== ĐÃ GHI ĐƠN → LUÔN SANG SUCCESS =====
    return redirect(url_for("success", order_id=order_id, total=total))


# ===== RUN =====
if __name__ == "__main__":
    app.run(debug=True)
