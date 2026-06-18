import telebot
from telebot import types
import os
from flask import Flask
import re
import time
import sqlite3

# 🌐 RENDER VEB-SERVERI
server = Flask(__name__)

# 🔑 API TOKEN VA ASOSIY SOZLAMALAR
TOKEN = '8760453840:AAF7GPFBVMEg0jvxa8hsKfdlaee1VI8V1IA'
bot = telebot.TeleBot(TOKEN)

MAJBURIY_KANAL_ID = "@ProVera_Design"  
MAJBURIY_KANAL_LINK = "https://t.me/ProVera_Design"  
PORTFOLIO_KANAL = "ProVera_Design_Portfolio"  

ADMIN_CHAT_ID = "-1003997246734"  
ADMIN_USERNAME = "@ProVera_Design_Admin"

KARTA_MA'LUMOTLARI = (
    "💳 **To'lov uchun karta ma'lumotlari:**\n\n"
    "• Karta raqami: `5614 6818 5637 1004`\n"
    "• Ism-sharif: ANVAR SOLEXOV\n"
    "• Bank: Hamkorbank\n\n"
    "⚠️ **Muhim:** To'lovni amalga oshirgach, to'lov chekini (skrinshot) aynan shu yerga rasm ko'rinishida yuboring!"
)

user_data = {}

# 🗄 MA'LUMOTLAR BAZASI (RENDER UCHUN XAVFSIZ /TMP JOYI)
DB_PATH = "/tmp/orders.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"Baza yuklanishida xato: {e}")

init_db()

# ⚙️ BAZA AMALLARI
def add_order(user_id, name, service, phone):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, name, service, phone, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, service, phone, "⌛ Kutilmoqda")
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
    except Exception:
        return int(time.time())

def get_order_status(order_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status, service FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        conn.close()
        return res
    except Exception:
        return None

# 🔄 OBUNANI TEKSHIRISH
def check_sub(user_id):
    try:
        member = bot.get_chat_member(MAJBURIY_KANAL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return True

# 📋 ASOSIY MENYU
def bosh_menyu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 Xizmatlar va Narxlar")
    btn2 = types.KeyboardButton("📂 Portfolio (Bizning ishlar)")
    btn3 = types.KeyboardButton("📞 Buyurtma berish / Aloqa")
    btn4 = types.KeyboardButton("🔍 Tekshirish (Provera)")
    btn5 = types.KeyboardButton("ℹ️ Yordam")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    bot.send_message(message.chat.id, "ProVera botining asosiy menyusi. Kerakli bo'limni tanlang 👇", reply_markup=markup)

# 🚀 START KOMANDASI
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        
    if check_sub(user_id):
        bot.send_message(message.chat.id, "Assalomu aleykum! ProVera botiga xush kelibsiz!")
        bosh_menyu(message)
    else:
        remove_keyboard = types.ReplyKeyboardRemove()
        inline_markup = types.InlineKeyboardMarkup()
        btn_kanal = types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=MAJBURIY_KANAL_LINK)
        btn_check = types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")
        inline_markup.add(btn_kanal)
        inline_markup.add(btn_check)
        bot.send_message(message.chat.id, f"🚀 Botdan to'liq foydalanish uchun iltimos kanalimizga a'zo bo'ling:\n\n{MAJBURIY_KANAL_LINK}", reply_markup=inline_markup)
        bot.send_message(message.chat.id, "⚠️ Kanalga a'zo bo'lmaguningizcha menyu bloklanadi.", reply_markup=remove_keyboard)

# 🛑 CALLBACK HANDLER (INLINE TUGMALAR UCHUN)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "check_subscription":
        if check_sub(call.from_user.id):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass
            bot.send_message(call.message.chat.id, "🎉 Rahmat! Obuna tasdiqlandi.")
            bosh_menyu(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
    
    elif call.data.startswith("set_"):
        parts = call.data.split("_")
        status_type, order_id = parts[1], parts[2]
        new_status = "⚙️ Jarayonda" if status_type == "process" else "⏳ To'lov kutilmoqda" if status_type == "payment" else "✅ Tayyor"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, service, name, phone FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        
        if res:
            user_id, service, name, phone = res
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            bot.answer_callback_query(call.id, "Holat o'zgartirildi!")
            
            if status_type == "payment":
                try:
                    bot.send_message(user_id, f"🎉 **#{order_id}** buyurtmangiz qabul qilindi.\n\n{KARTA_MA'LUMOTLARI}", parse_mode="Markdown")
                except Exception: pass
            else:
                try:
                    bot.send_message(user_id, f"📢 Buyurtmangiz holati yangilandi!\n🆔 ID: #{order_id}\n📌 Yangi holat: *{new_status}*", parse_mode="Markdown")
                except Exception: pass
        conn.close()

# 📱 KONTAKT YUBORILGANDA
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id].get('step') == 3:
        user_data[user_id]['phone'] = message.contact.phone_number
        finish_order(message, user_id)

# 💬 MATNLARNI QABUL QILISH
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if message.text == "❌ Buyurtmani bekor qilish":
        if user_id in user_data: del user_data[user_id]
        bot.send_message(message.chat.id, "❌ Amaliyot bekor qilindi.")
        bosh_menyu(message)
        return

    if user_id in user_data and 'step' in user_data[user_id] and message.text != "✍️ Onlayn Buyurtma berish":
        process_order_steps(message)
        return

    if user_id in user_data and user_data[user_id].get('action') == 'checking_id':
        process_checking_id(message)
        return

    if message.text == "💰 Xizmatlar va Narxlar":
        narxlar_matni = (
            "✨ *ProVera Design — Tariflar va Kombolar:* \n\n"
            "1️⃣ *Logotip 'Start':* **350 000 so'm**\n"
            "2️⃣ *Logotip 'Pro':* **600 000 so'm**\n"
            "3️⃣ *Eksklyuziv Vizitkalar:* **200 000 so'm**\n"
            "4️⃣ *🔥 Kombo 'Start':* **500 000 so'm**\n"
            "5️⃣ *💎 Kombo 'Premium':* **950 000 so'm**\n\n"
            f"💡 _Savollar bo'yicha adminga yozing:_ {ADMIN_USERNAME}"
        )
        bot.send_message(message.chat.id, narxlar_matni, parse_mode="Markdown")
        
    elif message.text == "📂 Portfolio (Bizning ishlar)":
        inline_portfolio = types.InlineKeyboardMarkup()
        inline_portfolio.add(types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish", url=f"https://t.me/{PORTFOLIO_KANAL}"))
        bot.send_message(message.chat.id, "📂 Bizning ishlarimiz bilan tanishish uchun tugmani bosing:", reply_markup=inline_portfolio)
        
    elif message.text == "📞 Buyurtma berish / Aloqa":
        markup_aloqa = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_aloqa.add(types.KeyboardButton("✍️ Onlayn Buyurtma berish"), types.KeyboardButton("⬅️ Orqaga (Bosh menyu)"))
        bot.send_message(message.chat.id, f"📱 Telefon: +998200271779\n🤖 Admin: {ADMIN_USERNAME}", reply_markup=markup_aloqa)

    elif message.text == "✍️ Onlayn Buyurtma berish":
        user_data[user_id] = {'step': 1}
        markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "📝 **1-Bosqich:** Ism va familiyangizni kiriting:", reply_markup=markup_cancel)

    elif message.text == "🔍 Tekshirish (Provera)":
        user_data[user_id] = {'action': 'checking_id'}
        markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "🔍 Buyurtma ID raqamini kiriting (Masalan: 1):", reply_markup=markup_cancel)

    elif message.text == "⬅️ Orqaga (Bosh menyu)":
        bosh_menyu(message)
        
    elif message.text == "ℹ️ Yordam":
        bot.send_message(message.chat.id, f"Sizga qanday yordam kerak? Admin bilan bog'lanish: {ADMIN_USERNAME}")

# 📝 BUYURTMA BOSQICHLARI
def process_order_steps(message):
    user_id = message.from_user.id
    current_step = user_data[user_id]['step']
    text = message.text

    if current_step == 1:
        user_data[user_id]['name'] = text
        user_data[user_id]['step'] = 2
        bot.send_message(message.chat.id, "💼 **2-Bosqich:** Qanday xizmat kerak? (Masalan: Logo Start, Vizitka):")

    elif current_step == 2:
        user_data[user_id]['service'] = text
        user_data[user_id]['step'] = 3
        markup_phone = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_phone.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True), types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "📞 **3-Bosqich:** Telefon raqamingizni yozing yoki pastdagi tugma orqali yuboring:", reply_markup=markup_phone)

    elif current_step == 3:
        user_data[user_id]['phone'] = text
        finish_order(message, user_id)

# 🔍 ID ORQALI TEKSHIRISH
def process_checking_id(message):
    user_id = message.from_user.id
    if message.text.isdigit():
        res = get_order_status(int(message.text))
        if res:
            bot.send_message(message.chat.id, f"🆔 Buyurtma: #{message.text}\n💼 Xizmat: {res[1]}\n📌 Holat: *{res[0]}*", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ Kechirasiz, bunday ID dagi buyurtma topilmadi.")
    if user_id in user_data: del user_data[user_id]
    bosh_menyu(message)

# 🏁 BUYURTMANI YAKUNLASH
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
        f"📞 Tel: {phone}\n"
        f"🤖 Profil: {username_text}\n"
        f"📌 Holat: ⌛ Kutilmoqda"
    )
    
    admin_inline = types.InlineKeyboardMarkup()
    btn_process = types.InlineKeyboardButton("⚙️ Jarayonda", callback_data=f"set_process_{order_id}")
    btn_pay = types.InlineKeyboardButton("⏳ To'lov kutilmoqda", callback_data=f"set_payment_{order_id}")
    btn_ready = types.InlineKeyboardButton("✅ Tayyor", callback_data=f"set_ready_{order_id}")
    admin_inline.add(btn_process, btn_pay, btn_ready)
    
    try: bot.send_message(ADMIN_CHAT_ID, admin_matn, reply_markup=admin_inline)
    except Exception: pass

    bot.send_message(message.chat.id, f"🎉 Rahmat! Buyurtmangiz qabul qilindi.\n🆔 Sizning buyurtma raqamingiz: `#{order_id}`", parse_mode="Markdown")
    if user_id in user_data: del user_data[user_id]
    bosh_menyu(message)

# 🌐 FLASK WEBHOOK MANZILI
@server.route('/')
def index():
    return "ProVera Bot running smoothly!", 200

# 🚀 RENDER WEB SERVICE START REJIMIDA ISHGA TUSHIRISH
if __name__ == "__main__":
    import threading
    # Pollingni alohida oqimda xavfsiz holatda qo'yamiz
    t = threading.Thread(target=lambda: bot.infinity_polling(allowed_updates=types.User), daemon=True)
    t.start()
    
    # Portni band qilamiz (Render talabi)
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
