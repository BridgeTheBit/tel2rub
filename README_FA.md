[English Help](https://github.com/BridgeTheBit/tel2rub/blob/main/README.md)
# 🚀 Tel2Rub — پل انتقال پیام از تلگرام به روبیکا

**Tel2Rub** ابزاری حرفه‌ای برای انتقال پیام از تلگرام به روبیکا است.  
این پروژه با هدف اجرای پایدار، نصب بسیار آسان، مدیریت خودکار سشن روبیکا، و یک CLI اختصاصی توسعه داده شده است.

---

# ✨ قابلیت‌ها

### 🔹 انتقال خودکار پیام‌ها از تلگرام به روبیکا
هماهنگ‌سازی پیام‌های یک کانال/گروه/چت تلگرام با روبیکا.

### 🔹 مدیریت کاملاً خودکار Rubika Session
- تشخیص وجود سشن قبلی  
- امکان استفاده مجدد یا ساخت سشن جدید  
- دریافت شماره موبایل و کد تأیید  
- ذخیره خودکار `rubika.session`  
- به‌روزرسانی اتوماتیک `.env`

### 🔹 نصب یک‌خطی (One‑Command Installer)
تنها با یک دستور، کل سرویس به صورت کامل نصب می‌شود.

### 🔹 آپدیت خودکار
اجرای دوباره دستور نصب → بررسی آخرین نسخه و بروزرسانی در صورت وجود نسخه جدید.


---

# 🛠️ نصب (Install)

برای نصب کامل برنامه فقط کافیست دستور زیر را اجرا کنید:
```bash
bash <(curl -s https://raw.githubusercontent.com/BridgeTheBit/tel2rub/main/install.sh)
```


# در طول نصب موارد زیر انجام می‌شود:
- دانلود آخرین نسخه از GitHub
- ایجاد مسیر /opt/tel2rub
- ساخت venv و نصب dependencies
- ایجاد .env
- دریافت API ID / API HASH / BOT TOKEN
- ساخت و مدیریت خودکار Rubika session
- ساخت سرویس systemd
- افزودن CLI جهانی

## 🔄 بروزرسانی (Update)
برای آپدیت، دوباره همین دستور را اجرا کنید:

```bash
bash <(curl -s https://raw.githubusercontent.com/BridgeTheBit/tel2rub/main/install.sh)
```
- اگر نسخه جدید باشد → بروزرسانی انجام می‌شود
- اگر آخرین نسخه باشد → پیام “Already up to date” نمایش داده می‌شود

## 📂 ساختار پوشه‌ها
```text
/opt/tel2rub
 ├── install.sh
 ├── installer_session.py
 ├── requirements.txt
 ├── main.py
 ├── rub.py
 ├── telebot.py
 ├── tel2rub
 ├── VERSION
 ├── .env
 └── venv/
```
# توضیح فایل‌ها
- main.py → نقطه شروع برنامه
- rub.py → منطق ارتباط با روبیکا
- telebot.py → ارتباط با تلگرام
- installer_session.py → مدیریت خودکار سشن روبیکا
- tel2rub → ابزار CLI نصب‌شده در /usr/local/bin
- VERSION → نسخه نصب‌شده
- .env → فایل تنظیمات محیطی
## ▶️ اجرای برنامه
سرویس به صورت خودکار پس از نصب فعال می‌شود:

```bash
systemctl status tel2rub
```

# اجرای CLI:

```bash
tel2rub
```
## 🧰 دستورات CLI
```bash
tel2rub start
tel2rub stop
tel2rub restart
tel2rub logs
```

❤️ تشکر
اگر این پروژه برایتان مفید بوده، لطفاً ⭐ ستاره بدهید و به توسعه آن کمک کنید.
