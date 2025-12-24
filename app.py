from flask import Flask, render_template, request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import time

app = Flask(__name__)

# =========================
# CONFIG – CHỈ CẦN ĐỔI 3 DÒNG NÀY
# =========================
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx6TTf_SUN616jNvubvh80bQN3omoa1KKNVWoXd-Sp4UkUy4OGtOs85X4WDVOf8Kg2L/exec"
TELEGRAM_BOT_TOKEN = "8338747162:AAFnIT2NHXD0ha--Mp5ZsCvMNHr7pDIYxyg"
TELEGRAM_CHAT_ID = "6285097453"

ORDER_LIMIT_SECONDS = 180  # 3 phút
order_cache = {}

# =========================
# TRANG CHỦ
# =========================
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# =========================
# XỬ LÝ ĐẶT HÀNG
# =========================
@app.route("/order", methods=["POST"])
def order():
    # ========= CHỐNG SPAM – HONEYPOT =========
    if request.form.get("website"):
        return "Spam detected", 400

    # ========= GIỚI HẠN 1 ĐƠN / 3 PHÚT =========
    phone = request.form.get("phone")
    now_ts = time.time()
    last_time = order_cache.get(phone)

    if last_time and now_ts - last_time < ORDER_LIMIT_SECONDS:
        return """
        <h2>⚠️ Bạn đặt đơn quá nhanh</h2>
        <p>Vui lòng chờ vài phút rồi thử lại.</p>
        """

    order_cache[phone] = now_ts

    # ========= THÔNG TIN KHÁCH =========
    name = request.form.get("name")
    address = request.form.get("address")

    # ========= THÔNG TIN ĐƠN =========
    combo = request.form.get("combo")
    price = request.form.get("price")
    sauce = request.form.get("sauce")
    spicy = request.form.get("spicy")
    note = request.form.get("note")

    drink = request.form.get("drink")
    tobacco = request.form.get("tobacco")
    total = request.form.get("total")

    # ========= THỜI GIAN VN =========
    time_now = datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).strftime("%d/%m/%Y %H:%M:%S")

    # ========= GỬI GOOGLE SHEET =========
    data = {
        "time": time_now,
        "name": name,
        "phone": phone,
        "address": address,
        "combo": combo,
        "price": price,
        "sauce": sauce,
        "spicy": spicy,
        "drink": drink,
        "tobacco": tobacco,
        "total": total,
        "note": note
    }

    try:
        requests.post(GOOGLE_SCRIPT_URL, json=data, timeout=10)
    except:
        pass

    # ========= GỬI TELEGRAM =========
    telegram_msg = f"""
🧾 ĐƠN HÀNG MỚI
⏰ {time_now}

👤 {name}
📞 {phone}
📍 {address}

🍢 Combo: {combo}
🥫 Sốt: {sauce}
🌶 Cay: {spicy}
🥤 Nước: {drink}
🚬 Thuốc: {tobacco}

💰 Tổng tiền: {total}đ
📝 Ghi chú: {note}
"""

    try:
        requests.post(
            f"https://api.telegram.org/bot8338747162:AAFnIT2NHXD0ha--Mp5ZsCvMNHr7pDIYxyg/sendMessage",
            json={
                "chat_id": 6285097453,
                "text": telegram_msg
            },
            timeout=5
        )
    except:
        pass

    # ========= TRANG THÀNH CÔNG =========
    return render_template(
        "success.html",
        name=name,
        phone=phone,
        total=total
    )

# =========================
# CHẠY LOCAL / RENDER
# =========================
if __name__ == "__main__":
    app.run(debug=True)
