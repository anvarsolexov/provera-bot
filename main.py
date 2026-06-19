import telebot
from telebot import types
import os
import time
import sqlite3
from flask import Flask
import threading

# 🌐 RENDER UCHUN MAJBURIY VEB-SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "ProVera Bot Is Alive!", 200

# 🔑 API TOKEN VA SOZLAMALAR
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
DB_PATH = "/tmp/orders.db"

# 📦 BAZA BILAN ISHLASH
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
        print(f"Baza xatosi: {e}")

init_db()

def add_order(user_id, name, service, phone):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, name, service, phone, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, service, phone, "⏳ Kutilmoqda")
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

# 🔔 OBUNA TEKSHIRISH
def check_sub(user_id):
    try:
        member = bot.get_chat_member(MAJBURIY_KANAL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return True

# 📱 MENYULAR
def bosh_menyu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Xizmatlar va Narxlar"), types.KeyboardButton("📂 Portfolio (Bizning ishlar)"))
    markup.add(types.KeyboardButton("📞 Buyurtma berish / Aloqa"), types.KeyboardButton("🔍 Tekshirish (Provera)"))
    markup.add(types.KeyboardButton("ℹ️ Yordam"))
    bot.send_message(message.chat.id, "ProVera botining asosiy menyusi. Bo'limni tanlang 👇", reply_markup=markup)

def xizmatlar_menyusi(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("1️⃣ Logo Start"), types.KeyboardButton("2️⃣ Logo Pro"))
    markup.add(types.KeyboardButton("3️⃣ Vizitka Dizayn"), types.KeyboardButton("4️⃣ Banner / Flayer"))
    markup.add(types.KeyboardButton("5️⃣ Kombo Start"), types.KeyboardButton("6️⃣ Kombo Premium"))
    markup.add(types.KeyboardButton("⬅️ Orqaga (Bosh menyu)"))
    bot.send_message(message.chat.id, "Kerakli xizmat turini tanlang va batafsil narxlar bilan tanishing 👇", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in user_data: del user_data[user_id]
        
    if check_sub(user_id):
        bot.send_message(message.chat.id, "Assalomu aleykum! ProVera botiga xush kelibsiz!")
        bosh_menyu(message)
    else:
        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=MAJBURIY_KANAL_LINK))
        inline_markup.add(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
        bot.send_message(message.chat.id, f"🚀 Botdan foydalanish uchun kanalimizga a'zo bo'ling:\n\n{MAJBURIY_KANAL_LINK}", reply_markup=inline_markup)

# 🔄 CALLBACK SO'ROVLARI
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "check_subscription":
        if check_sub(call.from_user.id):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass
            bot.send_message(call.message.chat.id, "🎉 Tasdiqlandi!")
            bosh_menyu(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Kanalga a'zo bo'
