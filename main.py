import telebot
from telebot import types
import os
from flask import Flask
import threading
import re
import sqlite3

# 🌐 Render xatolik bermasligi uchun Flask veb-serveri
server = Flask(__name__)

# 🔑 TELEGRAM BOT TOKEN
TOKEN = '8760453840:AAHkfjYO_xzHW7Igk1vZxE8gfoY6zYsj0Tg'
bot = telebot.TeleBot(TOKEN)

# 🛑 REKLAMANI CHIQARMASLIK UCHUN WEBHOOK TOZALAGICH
try:
    bot.remove_webhook(drop_pending_updates=True)
    print("Eski ulanishlar muvaffaqiyatli tozalandi!")
except Exception as e:
    print(f"Webhookni o'chirishda xatolik: {e}")

# 📂 PORTFOLIO KANALI LINKI
PORTFOLIO_KANAL = "ProVera_Design_Portfolio"  

# 👥 ADMIN GURUHI CHAT ID RAQAMI
ADMIN_CHAT_ID = "-1003997246734"  

# Foydalanuvchilar bosqichlarini saqlash uchun lug'at
user_data = {}

# 🗄 MA'LUMOTLAR BAZASINI YARATISH VA SOZLASH
def init_db():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            service TEXT,
            phone TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def add_order(user_id, name, service, phone):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, name, service, phone, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, service, phone, "⌛ Kutilmoqda")
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_order_status(order_id):
    try:
        conn = sqlite3.connect("orders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT status, service FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        conn.close()
        return res
    except Exception:
        return None

def bosh_menyu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Ilovani yuklab olish")
    btn2 = types.KeyboardButton("💰 Xizmatlar va Narxlar")
    btn3 = types.KeyboardButton("📂 Portfolio (Bizning ishlar)")
    btn4 = types.KeyboardButton("📞 Buyurtma berish / Aloqa")
    btn5 = types.KeyboardButton("🔍 Tekshirish (Provera)")
    btn6 = types.KeyboardButton("ℹ️ Yordam")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    
    bot.send_message(
        message.chat.id, 
        "ProVera botining asosiy menyusi. Kerakli bo'limni tanlang 👇", 
        reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        
    bot.send_message(message.chat.id, "Assalomu aleykum! ProVera botiga xush kelibsiz!")
    bosh_menyu(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("set_"):
        parts = call.data.split("_")
        status_type = parts[1]
        order_id = parts[2]
        
        new_status = "⚙️ Jarayonda" if status_type == "process" else "✅ Tayyor"
        
        conn = sqlite3.connect("orders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, service, name, phone FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        
        if res:
            user_id, service, name, phone = res
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            
            bot.answer_callback_query(call.id, f"Buyurtma holati '{new_status}' ga o'zgartirildi!")
            
            raw_username = "Mavjud emas"
            if "🤖 Telegram profili: " in call.message.text:
                try:
                    raw_username = call.message.text.split("🤖 Telegram profili: ")[1].split("\n")[0]
                except Exception:
                    pass
            
            updated_text = (
                f"🔔 **BUYURTMA HAKIDA MA'LUMOT (ID: #{order_id})** 🔔\n\n"
                f"👤 Mijoz: {name}\n"
                f"💼 Xizmat turi: {service}\n"
                f"📞 Telefon: {phone}\n"
                f"🤖 Telegram profili: {raw_username}\n\n"
                f"📌 **HOZIRGI HOLAT:** {new_status}"
            )
            
            if status_type == "process":
                next_inline = types.InlineKeyboardMarkup()
                btn_ready = types.InlineKeyboardButton("✅ Tayyor deb belgilash", callback_data=f"set_ready_{order_id}")
                next_inline.add(btn_ready)
                bot.edit_message_text(updated_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=next_inline)
            else:
                bot.edit_message_text(updated_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            
            try:
                bot.send_message(user_id, f"📢 **Sizning buyurtmangiz holati yangilandi!**\n\n🆔 Buyurtma raqami: `#{order_id}`\n💼 Xizmat: {service}\n📌 Yangi holat: *{new_status}*")
            except Exception:
                pass
        conn.close()

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]['step'] == 3:
        user_data[user_id]['phone'] = message.contact.phone_number
        finish_order(message, user_id)
    else:
        bot.send_message(message.chat.id, "⚠️ Hozir telefon raqam yuborish bosqichi emas.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if message.text == "❌ Buyurtmani bekor qilish":
        if user_id in user_data: 
            del user_data[user_id]
        bot.send_message(message.chat.id, "❌ Amaliyot bekor qilindi.")
        bosh_menyu(message)
        return

    if user_id in user_data and 'step' in user_data[user_id] and message.text != "✍️ Onlayn Buyurtma berish":
        process_order_steps(message)
        return

    if user_id in user_data and user_data[user_id].get('action') == 'checking_id':
        process_checking_id(message)
        return

    # 1. ILOVA YUKLAB OLISH BO'LIMI
    if message.text == "📱 Ilovani yuklab olish":
        inline_ilova = types.InlineKeyboardMarkup()
        btn_link = types.InlineKeyboardButton("📥 Yuklab olish (Google Drive)", url="https://share.google/yYkrudNSAmI7V...")
        inline_ilova.add(btn_link)
        bot.send_message(message.chat.id, "ProVera rasmiy ilovasini yuklab olish uchun quyidagi tugmani bosing: 👇", reply_markup=inline_ilova)
        
    # 2. XIZMATLAR VA NARXLAR BO'LIMI
    elif message.text == "💰 Xizmatlar va Narxlar":
        narxlar_matni = (
            "✨ *ProVera Design — Professional Tariflar ro'yxati* ✨\n\n"
            "📦 *1. LOGO YARATISH (BRENDING)*\n"
            "• *Ekonom:* 149 000 so'm — 1 ta oddiy variant, **1 kundan 3 kunda tayyor**.\n"
            "• *Standart (Tavsiya etiladi):* 390 000 so'm — 3 ta professional variant, 3D Mockup vizualizatsiyasi, barcha formatlarda (AI, PSD, PNG), **2 kundan 6 kunda tayyor**.\n"
            "• *Premium:* 890 000 so'm — Cheksiz tuzatishlar, brendbuk (firma stili) va VIP yondashuv, **2 kundan 6 kunda tayyor**.\n\n"
            "📱 *2. SMM DIZAYN (IJTIMOIY TARMOQLAR)*\n"
            "• *1 ta post dizayni:* 49 000 so'm\n"
            "• *1 ta Storiz / Reels muqovasi:* 29 000 so'm\n"
            "• *Oylik paket (15 ta post + 10 ta storiz):* 590 000 so'm\n\n"
            "🗂 *3. POLIGRAFIYA VA REKLAMA (BOSMA)*\n"
            "• *Vizitka yoki Korporativ karta:* 69 000 so'm\n"
            "• *Flayer / Buklet / Menyu:* 119 000 so'mdan\n"
            "• *Tashqi reklama (Banner, Bilbord):* 249 000 so'mdan\n\n"
            "🎁 *Kombi Taklif (Aksiya):*\n"
            "Logo (Standart) + Vizitka dizayni birgalikda buyurtma berilsa, 459 000 so'm emas, cheklamagan muddatga atigi **399 000 so'm**! 🔥\n\n"
            "💡 _Barcha ishlar matbaaga tayyor holda (CMYK formatida) yuqori sifatda topshiriladi._\n\n"
            "⚠️ **ESLATMA:**\n"
            "Narxlar aniq qanchaligi va buyurtma tayyor bo'lish vaqtini to'liq aniqlashtirish uchun adminga murojaat qiling: 👉 @ProVera_Design_Admin"
        )
        bot.send_message(message.chat.id, narxlar_matni, parse_mode="Markdown")
        
    # 3. PORTFOLIO BO'LIMI
    elif message.text == "📂 Portfolio (Bizning ishlar)":
        inline_portfolio = types.InlineKeyboardMarkup(row_width=1)
        btn_kanal = types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish (Kanal)", url=f"https://t.me/{PORTFOLIO_KANAL}")
        inline_portfolio.add(btn_kanal)
        
        portfolio_matni = (
            "📂 *ProVera Design — Bizning ishlarimiz bilan tanishing!*\n\n"
            "Biz yaratgan eng sara logotiplar maxsus portfolio kanalimizda! 👇"
        )
        bot.send_message(message.chat.id, portfolio_matni, parse_mode="Markdown", reply_markup=inline_portfolio)
        
    # 4. BUYURTMA BERISH VA ALOQA BO'LIMI
    elif message.text == "📞 Buyurtma berish / Aloqa":
        markup_aloqa = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_new_order = types.KeyboardButton("✍️ Onlayn Buyurtma berish")
        btn_back = types.KeyboardButton("⬅️ Orqaga (Bosh menyu)")
        markup_aloqa.add(btn_new_order, btn_back)
        
        aloqa_matni = (
            "📞 Biz bilan bog'lanish:\n\n"
            "📱 Telefon: +998200271779 | +998200057207\n"
            "🤖 Telegram: @ProVera_Design_Admin"
        )
        bot.send_message(message.chat.id, aloqa_matni, reply_markup=markup_aloqa)

    elif message.text == "✍️ Onlayn Buyurtma berish":
        user_data[user_id] = {'step': 1}
        markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "📝 *1-Bosqich:* Ism va familiyangizni kiriting:", parse_mode="Markdown", reply_markup=markup_cancel)

    elif message.text == "🔍 Tekshirish (Provera)":
        user_data[user_id] = {'action': 'checking_id'}
        markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "🔍 *Buyurtma holatini tekshirish*\n\nIltimos, ID raqamni kiriting (Masalan: 1):", parse_mode="Markdown", reply_markup=markup_cancel)

    elif message.text == "⬅️ Orqaga (Bosh menyu)":
        bosh_menyu(message)
        
    elif message.text == "ℹ️ Yordam":
        bot.send_message(message.chat.id, "Sizga qanday yordam bera olaman? Muammo bo'lsa biz bilan bog'laning: @ProVera_Design_Admin")
    else:
        bot.send_message(message.chat.id, "⚠️ Pastdagi tayyor menyu tugmalaridan birini bosing. 👇")

def process_order_steps(message):
    user_id = message.from_user.id
    current_step = user_data[user_id]['step']
    text = message.text

    if current_step == 1:
        if len(text) < 3 or any(char.isdigit() for char in text):
            bot.send_message(message.chat.id, "❌ Ismingizni to'g'ri va faqat harflar bilan yozing:")
            return
        user_data[user_id]['name'] = text
        user_data[user_id]['step'] = 2
        bot.send_message(message.chat.id, "💼 *2-Bosqich:* Qaysi tarif yoki xizmat turi kerak? (Masalan: Standart Logo, SMM oylik paket):", parse_mode="Markdown")

    elif current_step == 2:
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ Xizmat turini batafsilroq yozing:")
            return
        user_data[user_id]['service'] = text
        user_data[user_id]['step'] = 3
        markup_phone = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_phone.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True), types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "📞 *3-Bosqich:* Telefon raqamingizni kiriting yoki quyidagi tugma orqali yuboring:", parse_mode="Markdown", reply_markup=markup_phone)

    elif current_step == 3:
        clean_phone = re.sub(r'[^\d+]', '', text)
        if len(clean_phone) < 9:
            bot.send_message(message.chat.id, "❌ Noto'g'ri raqam! To'g'ri formatda kiriting:")
            return
        user_data[user_id]['phone'] = clean_phone
        finish_order(message, user_id)

def process_checking_id(message):
    user_id = message.from_user.id
    text = message.text
    
    if not text.isdigit():
        bot.send_message(message.chat.id, "❌ Faqat sonlardan iborat ID raqam kiriting:")
        return
        
    order_id = int(text)
    res = get_order_status(order_id)
    
    if res:
        status, service = res
        bot.send_message(message.chat.id, f"📊 **Buyurtma holati:**\n\n🆔 ID: `#{order_id}`\n💼 Xizmat: {service}\n📌 Holat: *{status}*", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ `#{order_id}` raqamli buyurtma topilmadi.")
    
    if user_id in user_data: 
        del user_data[user_id]
    bosh_menyu(message)

def finish_order(message, user_id):
    name = user_data[user_id]['name']
    service = user_data[user_id]['service']
    phone = user_data[user_id]['phone']
    
    order_id = add_order(user_id, name, service, phone)
    raw_username = message.from_user.username
    username_text = f"@{raw_username}" if raw_username else "Mavjud emas"
    
    admin_matn = (
        f"🔔 **YANGI BUYURTMA (ID: #{order_id})** 🔔\n\n"
        f"👤 Mijoz: {name}\n"
        f"💼 Xizmat: {service}\n"
        f"📞 Telefon: {phone}\n"
        f"🤖 Telegram: {username_text}\n"
        f"📌 Holati: ⌛ Kutilmoqda"
    )
    
    admin_inline = types.InlineKeyboardMarkup()
    admin_inline.add(types.InlineKeyboardButton("⚙️ Jarayonda", callback_data=f"set_process_{order_id}"), types.InlineKeyboardButton("✅ Tayyor", callback_data=f"set_ready_{order_id}"))
    
    try:
        bot.send_message(ADMIN_CHAT_ID, admin_matn, reply_markup=admin_inline)
        bot.send_message(message.chat.id, f"🎉 Rahmat! Buyurtmangiz qabul qilindi. Sizning buyurtma raqamingiz: `#{order_id}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Tizimda xatolik.")
        print(e)
        
    if user_id in user_data: 
        del user_data[user_id]
    bosh_menyu(message)

@server.route('/')
def webhook():
    return "ProVera Bot is active", 200

def run_bot():
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
