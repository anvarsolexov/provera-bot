import telebot
from telebot import types
import os
from flask import Flask
import threading
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
        print(f"Baza xatosi: {e}")

init_db()

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

def check_sub(user_id):
    try:
        member = bot.get_chat_member(MAJBURIY_KANAL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return True

def bosh_menyu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Xizmatlar va Narxlar"), types.KeyboardButton("📂 Portfolio (Bizning ishlar)"))
    markup.add(types.KeyboardButton("📞 Buyurtma berish / Aloqa"), types.KeyboardButton("🔍 Tekshirish (Provera)"))
    markup.add(types.KeyboardButton("ℹ️ Yordam"))
    bot.send_message(message.chat.id, "ProVera botining asosiy menyusi. Bo'limni tanlang 👇", reply_markup=markup)

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

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "check_subscription":
        if check_sub(call.from_user.id):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass
            bot.send_message(call.message.chat.id, "🎉 Tasdiqlandi!")
            bosh_menyu(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Kanalga a'zo bo'lmadingiz!", show_alert=True)
    
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
            bot.answer_callback_query(call.id, "Yangilandi!")
            
            if status_type == "payment":
                try: bot.send_message(user_id, f"🎉 **#{order_id}** buyurtmangiz qabul qilindi.\n\n{KARTA_MA'LUMOTLARI}", parse_mode="Markdown")
                except Exception: pass
            else:
                try: bot.send_message(user_id, f"📢 Holat yangilandi!\n🆔 ID: #{order_id}\n📌 Status: *{new_status}*", parse_mode="Markdown")
                except Exception: pass
        conn.close()

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id].get('step') == 3:
        user_data[user_id]['phone'] = message.contact.phone_number
        finish_order(message, user_id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if message.text == "❌ Buyurtmani bekor qilish":
        if user_id in user_data: del user_data[user_id]
        bot.send_message(message.chat.id, "❌ Bekor qilindi.")
        bosh_menyu(message)
        return

    if user_id in user_data and 'step' in user_data[user_id] and message.text != "✍️ Onlayn Buyurtma berish":
        process_order_steps(message)
        return

    if user_id in user_data and user_data[user_id].get('action') == 'checking_id':
        process_checking_id(message)
        return

    if message.text == "💰 Xizmatlar va Narxlar":
        narxlar = ("✨ *ProVera Design:* \n\n1️⃣ Logo Start: **350 000**\n2️⃣ Logo Pro: **600 000**\n3️⃣ Vizitka: **200 000**\n"
                   f"4️⃣ Kombo Start: **500 000**\n5️⃣ Kombo Premium: **950 000**\n\n💬 Admin: {ADMIN_USERNAME}")
        bot.send_message(message.chat.id, narxlar, parse_mode="Markdown")
    elif message.text == "📂 Portfolio (Bizning ishlar)":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish", url=f"https://t.me/{PORTFOLIO_KANAL}"))
        bot.send_message(message.chat.id, "Bizning ishlar:", reply_markup=m)
    elif message.text == "📞 Buyurtma berish / Aloqa":
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add(types.KeyboardButton("✍️ Onlayn Buyurtma berish"), types.KeyboardButton("⬅️ Orqaga (Bosh menyu)"))
        bot.send_message(message.chat.id, f"📱 Tel: +998200271779\n🤖 Admin: {ADMIN_USERNAME}", reply_markup=m)
    elif message.text == "✍️ Onlayn Buyurtma berish":
        user_data[user_id] = {'step': 1}
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "📝 Ism va familiyangizni kiriting:", reply_markup=m)
    elif message.text == "🔍 Tekshirish (Provera)":
        user_data[user_id] = {'action': 'checking_id'}
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "🔍 Buyurtma ID raqamini kiriting:", reply_markup=m)
    elif message.text == "⬅️ Orqaga (Bosh menyu)":
        bosh_menyu(message)

def process_order_steps(message):
    user_id = message.from_user.id
    step = user_data[user_id]['step']
    if step == 1:
        user_data[user_id]['name'] = message.text
        user_data[user_id]['step'] = 2
        bot.send_message(message.chat.id, "💼 Qanday xizmat kerak? (Masalan: Logo Pro):")
    elif step == 2:
        user_data[user_id]['service'] = message.text
        user_data[user_id]['step'] = 3
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True), types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "📞 Telefon raqamingizni yuboring yoki yozing:", reply_markup=m)
    elif step == 3:
        user_data[user_id]['phone'] = message.text
        finish_order(message, user_id)

def process_checking_id(message):
    user_id = message.from_user.id
    if message.text.isdigit():
        res = get_order_status(int(message.text))
        if res: bot.send_message(message.chat.id, f"🆔 ID: #{message.text}\n💼 Xizmat: {res[1]}\n📌 Holat: *{res[0]}*", parse_mode="Markdown")
        else: bot.send_message(message.chat.id, "❌ Topilmadi.")
    if user_id in user_data: del user_data[user_id]
    bosh_menyu(message)

def finish_order(message, user_id):
    name, service, phone = user_data[user_id]['name'], user_data[user_id]['service'], user_data[user_id]['phone']
    order_id = add_order(user_id, name, service, phone)
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    admin_matn = f"🔔 **YANGI BUYURTMA (ID: #{order_id})**\n\n👤 Mijoz: {name}\n💼 Xizmat: {service}\n📞 Tel: {phone}\n🤖 Profil: {username}"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚙️ Jarayonda", callback_data=f"set_process_{order_id}"), types.InlineKeyboardButton("⏳ To'lov kutilmoqda", callback_data=f"set_payment_{order_id}"), types.InlineKeyboardButton("✅ Tayyor", callback_data=f"set_ready_{order_id}"))
    
    try: bot.send_message(ADMIN_CHAT_ID, admin_matn, reply_markup=m)
    except Exception: pass
    bot.send_message(message.chat.id, f"🎉 Muvaffaqiyatli qabul qilindi. ID: `#{order_id}`", parse_mode="Markdown")
    if user_id in user_data: del user_data[user_id]
    bosh_menyu(message)

@server.route('/')
def index():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Flask alohida oqimda, polling esa asosiy oqimda ishlaydi (Ushbu kombinatsiya Render uchun o'limtik darajada barqaror)
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            time.sleep(3)
