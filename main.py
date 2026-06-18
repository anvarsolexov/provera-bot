import telebot
from telebot import types
import os
from flask import Flask
import re
import time
import sqlite3

# Render veb-serveri
server = Flask(__name__)

# 🔑 API TOKEN
TOKEN = '8760453840:AAF7GPFBVMEg0jvxa8hsKfdlaee1VI8V1IA'
bot = telebot.TeleBot(TOKEN)

# 📢 MAJBURIY OBUNA SOZLAMALARI
MAJBURIY_KANAL_ID = "@ProVera_Design"  
MAJBURIY_KANAL_LINK = "https://t.me/ProVera_Design"  

# 📂 PORTFOLIO KANALI
PORTFOLIO_KANAL = "ProVera_Design_Portfolio"  

# Guruh ID raqami (Buyurtmalar tushadigan guruh)
ADMIN_CHAT_ID = "-1003997246734"  
ADMIN_USERNAME = "@ProVera_Design_Admin"

# 💳 KARTA MA'LUMOTLARI
KARTA_MA'LUMOTLARI = (
    "💳 **To'lov uchun karta ma'lumotlari:**\n\n"
    "• Karta raqami: `5614 6818 5637 1004`\n"
    "• Ism-sharif: ANVAR SOLEXOV\n"
    "• Bank: Hamkorbank\n\n"
    "⚠️ **Muhim:** To'lovni amalga oshirgach, to'lov chekini (skrinshot) aynan shu yerga rasm ko'rinishida yuboring!"
)

user_data = {}

# 🗄 MA'LUMOTLAR BAZASINI SOZLASH (RENDER REJIMIDA MAXSUS /TMP JOYLAShUVI)
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
        print(f"Baza xatosi chetlab o'tildi: {e}")

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
    except Exception as e:
        return int(time.time())

def get_order_status(order_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status, service FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        conn.close()
        return res
    except Exception as e:
        return None

def check_sub(user_id):
    try:
        member = bot.get_chat_member(MAJBURIY_KANAL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return True

def bosh_menyu(message):
    try:
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
    except Exception:
        pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
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
            bot.send_message(message.chat.id, "🚀 Botdan to'liq foydalanish uchun iltimos kanalimizga a'zo bo'ling: \n\n" + MAJBURIY_KANAL_LINK, reply_markup=inline_markup)
            bot.send_message(message.chat.id, "⚠️ Kanalga a'zo bo'lmaguningizcha menyu bloklanadi.", reply_markup=remove_keyboard)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
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
            new_status = "⚙️ Jarayonda" if status_type == "process" else "⏳ To'lov qilinishi kutilmoqda" if status_type == "payment" else "✅ Tayyor"
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, service, name, phone FROM orders WHERE id = ?", (order_id,))
            res = cursor.fetchone()
            
            if res:
                user_id, service, name, phone = res
                cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
                conn.commit()
                bot.answer_callback_query(call.id, "Holat yangilandi!")
                
                if status_type == "payment":
                    try:
                        bot.send_message(user_id, f"🎉 **#{order_id}** buyurtmangiz qabul qilindi.\n\n{KARTA_MA'LUMOTLARI}", parse_mode="Markdown")
                    except Exception: pass
            conn.close()
    except Exception:
        pass

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    try:
        user_id = message.from_user.id
        if user_id in user_data and user_data[user_id].get('step') == 3:
            user_data[user_id]['phone'] = message.contact.phone_number
            finish_order(message, user_id)
    except Exception:
        pass

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
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
                "✨ *ProVera Design — Yangilangan Grafik dizayn narxlari va Kombolar:* \n\n"
                "1️⃣ *Logotip 'Start' Paket:* **350 000 so'm**\n"
                "2️⃣ *Logotip 'Pro' Paket:* **600 000 so'm**\n"
                "3️⃣ *Eksklyuziv Vizitkalar:* **200 000 so'm**\n"
                "4️⃣ *🔥 Kombo 'Start':* **500 000 so'm**\n"
                "5️⃣ *💎 Kombo 'Premium':* **950 000 so'm**\n\n"
                f"💡 _Aloqa uchun:_ {ADMIN_USERNAME}"
            )
            bot.send_message(message.chat.id, narxlar_matni, parse_mode="Markdown")
            
        elif message.text == "📂 Portfolio (Bizning ishlar)":
            inline_portfolio = types.InlineKeyboardMarkup()
            inline_portfolio.add(types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish", url=f"https://t.me/{PORTFOLIO_KANAL}"))
            bot.send_message(message.chat.id, "📂 Bizning ishlarimiz bilan tanishing:", reply_markup=inline_portfolio)
            
        elif message.text == "📞 Buyurtma berish / Aloqa":
            markup_aloqa = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup_aloqa.add(types.KeyboardButton("✍️ Onlayn Buyurtma berish"), types.KeyboardButton("⬅️ Orqaga (Bosh menyu)"))
            bot.send_message(message.chat.id, f"📱 Tel: +998200271779\n🤖 Admin: {ADMIN_USERNAME}", reply_markup=markup_aloqa)

        elif message.text == "✍️ Onlayn Buyurtma berish":
            user_data[user_id] = {'step': 1}
            markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
            bot.send_message(message.chat.id, "📝 Ism va familiyangizni kiriting:", reply_markup=markup_cancel)

        elif message.text == "🔍 Tekshirish (Provera)":
            user_data[user_id] = {'action': 'checking_id'}
            markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
            bot.send_message(message.chat.id, "🔍 Buyurtma ID raqamini kiriting:", reply_markup=markup_cancel)

        elif message.text == "⬅️ Orqaga (Bosh menyu)":
            bosh_menyu(message)
    except Exception:
        pass

def process_order_steps(message):
    try:
        user_id = message.from_user.id
        current_step = user_data[user_id]['step']
        text = message.text

        if current_step == 1:
            user_data[user_id]['name'] = text
            user_data[user_id]['step'] = 2
            bot.send_message(message.chat.id, "💼 Qanday xizmat kerak? (Masalan: Logo Start, Vizitka):")
        elif current_step == 2:
            user_data[user_id]['service'] = text
            user_data[user_id]['step'] = 3
            markup_phone = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup_phone.add(types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True), types.KeyboardButton("❌ Buyurtmani bekor qilish"))
            bot.send_message(message.chat.id, "📞 Telefon raqamingizni kiriting yoki yuboring:", reply_markup=markup_phone)
        elif current_step == 3:
            user_data[user_id]['phone'] = text
            finish_order(message, user_id)
    except Exception:
        pass

def process_checking_id(message):
    try:
        user_id = message.from_user.id
        if message.text.isdigit():
            res = get_order_status(int(message.text))
            if res:
                bot.send_message(message.chat.id, f"🆔 ID: #{message.text}\n💼 Xizmat: {res[1]}\n📌 Holat: {res[0]}")
            else:
                bot.send_message(message.chat.id, "❌ Buyurtma topilmadi.")
        if user_id in user_data: del user_data[user_id]
        bosh_menyu(message)
    except Exception:
        pass

def finish_order(message, user_id):
    try:
        name = user_data[user_id]['name']
        service = user_data[user_id]['service']
        phone = user_data[user_id]['phone']
        order_id = add_order(user_id, name, service, phone)
        
        raw_username = message.from_user.username
        username_text = f"@{raw_username}" if raw_username else "Mavjud emas"
        
        admin_matn = f"🔔 **YANGI BUYURTMA (ID: #{order_id})**\n👤 Mijoz: {name}\n💼 Xizmat: {service}\n📞 Tel: {phone}\n🤖 Profil: {username_text}"
        
        try: bot.send_message(ADMIN_CHAT_ID, admin_matn)
        except Exception: pass

        bot.send_message(message.chat.id, f"🎉 Rahmat! Buyurtmangiz qabul qilindi. Sizning ID: `#{order_id}`", parse_mode="Markdown")
    except Exception:
        pass
    if user_id in user_data: del user_data[user_id]
    bosh_menyu(message)

# RENDERGA INTEGRATSIYA: WHATSAPP/WEBHOOK YOKI DOIMIY ISHGA TUSHIRISH
@server.route('/')
def index():
    return "Bot is active", 200

# Eng muhim qismi: Renderda bot xato bermasligi uchun pollingni Flask bilan bir vaqtda boshqarish rejimiga o'tamiz
if __name__ == "__main__":
    import threading
    # Pollingni alohida oqimda xavfsiz va tinch holatda qoldiramiz
    t = threading.Thread(target=lambda: bot.infinity_polling(allowed_updates=types.User), daemon=True)
    t.start()
    
    # Render portni ochganda Flask srazu javob beradi va "status 1 running" xatosi yo'qoladi
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
