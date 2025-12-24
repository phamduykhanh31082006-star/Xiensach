from flask import Flask, render_template, request
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

app = Flask(__name__)

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
    # Thông tin khách
    name = request.form.get("name")
    phone = request.form.get("phone")
    address = request.form.get("address")

    # Thông tin đơn hàng
    combo = request.form.get("combo")
    price = request.form.get("price")
    sauce = request.form.get("sauce")
    spicy = request.form.get("spicy")
    note = request.form.get("note")

    # Thời gian đặt
    time_now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y %H:%M:%S")


    # =========================
    # LINK GOOGLE APPS SCRIPT
    # =========================
    google_script_url = "https://script.google.com/macros/s/AKfycbx6TTf_SUN616jNvubvh80bQN3omoa1KKNVWoXd-Sp4UkUy4OGtOs85X4WDVOf8Kg2L/exec"

    # Dữ liệu gửi lên Google Sheet
    data = {
        "time": time_now,
        "name": name,
        "phone": phone,
        "address": address,
        "combo": combo,
        "price": price,
        "sauce": sauce,
        "spicy": spicy,
        "note": note
    }

    try:
        requests.post(google_script_url, json=data, timeout=10)
        return """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Đặt hàng thành công</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-orange-50 flex items-center justify-center min-h-screen px-4">

  <div class="bg-white rounded-3xl shadow-xl max-w-md w-full p-6 text-center">

    <div class="text-5xl mb-3">✅</div>

    <h1 class="text-2xl font-extrabold text-green-600">
      Đặt hàng thành công!
    </h1>

    <p class="text-slate-700 mt-3">
      Cảm ơn bạn đã ủng hộ <b>Xiên Sạch Online</b> ❤️
    </p>

    <p class="text-slate-600 text-sm mt-2">
      Shop sẽ <b>liên hệ xác nhận đơn</b> trong ít phút.
      <br>
      Vui lòng để ý điện thoại giúp shop nhé!
    </p>

    <div class="mt-5 bg-orange-50 border border-orange-200 rounded-2xl p-4 text-sm text-slate-700">
      💳 <b>Thanh toán (tuỳ chọn)</b><br>
      Bạn có thể chuyển khoản trước để shop xử lý nhanh hơn,
      hoặc thanh toán khi nhận hàng (COD).
    </div>

    <a href="/"
       class="block mt-6 bg-gradient-to-r from-orange-500 to-red-500 text-white font-extrabold py-3 rounded-2xl hover:from-orange-600 hover:to-red-600">
      ⬅ Quay lại trang chủ
    </a>

    <p class="text-xs text-slate-400 mt-4">
      Chúc bạn ăn ngon miệng 😋
    </p>

  </div>

</body>
</html>
"""

    except Exception as e:
        return """
        <h2>❌ Có lỗi xảy ra</h2>
        <p>Vui lòng thử lại hoặc liên hệ shop.</p>
        """


# =========================
# CHẠY LOCAL
# =========================
if __name__ == "__main__":
    app.run(debug=True)
