import telebot
from telebot import types
import os
from flask import Flask
import threading
import re
import time
import requests
import sqlite3

# Render veb-serveri
server = Flask(__name__)

# Botingiz tokeni
TOKEN = '8760453840:AAEjCAOwtGZ-d8xGiIpaZ5xQ2MmeDasYZpI'
bot = telebot.TeleBot(TOKEN)

# 📢 MAJBURIY OBUNA SOZLAMALARI (Yopiq kanal uchun)
MAJBURIY_KANAL_ID = "-1002110067719"  
MAJBURIY_KANAL_LINK = "https://t.me/+UINPPxH9yas4ZDZi"  

# 📂 PORTFOLIO KANALI
PORTFOLIO_KANAL = "ProVera_Design_Portfolio"  

# Guruh ID raqami (Buyurtmalar tushadigan guruh)
ADMIN_CHAT_ID = "-1003997246734"  

user_data = {}

# 🗄 MA'LUMOTLAR BAZASINI SOZLASH
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

# BAZA BILAN ISHLASH FUNKSIYALARI
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
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status, service FROM orders WHERE id = ?", (order_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def check_sub(user_id):
    try:
        member = bot.get_chat_member(MAJBURIY_KANAL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return True

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
        
    if check_sub(user_id):
        bot.send_message(message.chat.id, "Assalomu aleykum! ProVera botiga xush kelibsiz!")
        bosh_menyu(message)
    else:
        inline_markup = types.InlineKeyboardMarkup()
        btn_kanal = types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=MAJBURIY_KANAL_LINK)
        btn_check = types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")
        inline_markup.add(btn_kanal)
        inline_markup.add(btn_check)
        
        bot.send_message(
            message.chat.id, 
            "👋 Assalomu aleykum!\n\nBotdan to'liq foydalanish uchun iltimos birinchi bo'lib rasmiy kanalimizga a'zo bo'ling. 👇", 
            reply_markup=inline_markup
        )

# 🛠 O'ZGARTIRILGAN VA TUZATILGAN CALLBACK HANDLER TIZIMI
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # 1. Obunani tekshirish
    if call.data == "check_subscription":
        if check_sub(call.from_user.id):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass
            bot.send_message(call.message.chat.id, "🎉 Rahmat! Obuna tasdiqlandi.")
            bosh_menyu(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz. Iltimos, oldin a'zo bo'ling!", show_alert=True)
    
    # 2. Admin tomonidan statusni o'zgartirish (Xatolik shu yerda tuzatildi)
    elif call.data.startswith("set_"):
        parts = call.data.split("_")
        status_type = parts[1] # "process" yoki "ready"
        order_id = parts[2]
        
        new_status = "⚙️ Jarayonda" if status_type == "process" else "✅ Tayyor"
        
        # Bazani yangilash
        conn = sqlite3.connect("orders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, service, name, phone FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        
        if res:
            user_id, service, name, phone = res
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            
            bot.answer_callback_query(call.id, f"Buyurtma holati '{new_status}' ga o'zgartirildi!")
            
            # Guruh xabari matnini chiroyli yangilaymiz
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
            
            # 🔄 Tugmalarni qayta chizish mantiqi:
            if status_type == "process":
                # Agar "Jarayonda" bosilsa, "Tayyor" tugmasini xabar ostida qoldiramiz!
                next_inline = types.InlineKeyboardMarkup()
                btn_ready = types.InlineKeyboardButton("✅ Tayyor deb belgilash", callback_data=f"set_ready_{order_id}")
                next_inline.add(btn_ready)
                bot.edit_message_text(updated_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=next_inline)
            else:
                # Agar "Tayyor" bosilsa, hamma tugmalarni butunlay o'chirib tashlaymiz
                bot.edit_message_text(updated_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            
            # Mijozga avtomatik bildirishnoma yuborish
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

    if not check_sub(user_id):
        send_welcome(message)
        return

    if message.text == "❌ Buyurtmani bekor qilish":
        if user_id in user_data: del user_data[user_id]
        bot.send_message(message.chat.id, "❌ Amaliyot bekor qilindi.")
        bosh_menyu(message)
        return

    # Agar foydalanuvchi buyurtma berish bosqichida bo'lsa
    if user_id in user_data and 'step' in user_data[user_id] and message.text != "✍️ Onlayn Buyurtma berish":
        process_order_steps(message)
        return

    # Agar foydalanuvchi buyurtma raqamini kiritib tekshirayotgan bo'lsa
    if user_id in user_data and user_data[user_id].get('action') == 'checking_id':
        process_checking_id(message)
        return

    if message.text == "📱 Ilovani yuklab olish":
        bot.send_message(message.chat.id, "Ilovani yuklab olish uchun havola: https://share.google/yYkrudNSAmI7V...")
        
    elif message.text == "💰 Xizmatlar va Narxlar":
        narxlar_matni = (
            "✨ *ProVera Design — Grafik dizayn xizmatlari va narxlari:* \n\n"
            "🔥 *Asosiy xizmatlarimiz:* \n"
            "1️⃣ *Logo yaratish (Brending):* \n"
            " 80 000 so'mdan — 500 000 so'mgacha\n\n"
            "2️⃣ *Vizitkalar va Korporativ kartalar:* \n"
            " 100 000 so'mdan — 800 000 so'mgacha\n\n"
            "3️⃣ *Banner, Flayer va Bukletlar (Poligrafiya):* \n"
            " 100 000 so'mdan — 700 000 so'mgacha\n\n"
            "4️⃣ *SMM postlar va Storizlar uchun dizayn:* \n"
            " 80 000 so'mdan — 300 000 so'mgacha\n\n"
            "5️⃣ *Tashqi reklama (Bilbord va Vitrina dizayni):* \n"
            " 150 000 so'mdan — 1 200 000 so'mgacha\n\n"
            "6️⃣ *Sertifikat, Diplom va Taklifnomalar:* \n"
            " 30 000 so'mdan — 250 000 so'mgacha\n\n"
            "⚙️ *Boshqa barcha turdagi grafik xizmatlar:* \n"
            "• Firma stillari (Brandbook) yaratish...\n\n"
            "💡 _Eslatma: Yakuniy narx buyurtmaning murakkabligi va muddatiga qarab o'zgarishi mumkin._"
        )
        bot.send_message(message.chat.id, narxlar_matni, parse_mode="Markdown")
        
    elif message.text == "📂 Portfolio (Bizning ishlar)":
        inline_portfolio = types.InlineKeyboardMarkup(row_width=1)
        btn_kanal = types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish (Kanal)", url=f"https://t.me/{PORTFOLIO_KANAL}")
        inline_portfolio.add(btn_kanal)
        
        portfolio_matni = (
            "📂 *ProVera Design — Bizning ishlarimiz bilan
