import telebot
from telebot import types
import sqlite3
from datetime import datetime
import re
import os
import time
import requests
from flask import Flask
import threading

# 🌐 Render uchun Flask veb-serveri
server = Flask(__name__)

# 🔑 TELEGRAM BOT TOKEN
TOKEN = '8923702378:AAHPlRF3qSsT7jNbPmqbHFxSc74fbW1yuX8'
bot = telebot.TeleBot(TOKEN)

# 🛑 ESKI ULANISHLARNI TOZALASH
try:
    bot.remove_webhook(drop_pending_updates=True)
except Exception:
    pass

# ⚙️ KONFIGURATSIYA
PORTFOLIO_KANAL = "ProVera_Design_Portfolio"
ADMIN_CHAT_ID = "-1003997246734"  # Buyurtmalar tushadigan guruh yoki kanal ID
KARTA_RAQAM = "5614 6818 5637 1004"
KARTA_EGASI = "Anvar Solexov"

user_data = {}

# 🗄 MA'LUMOTLAR BAZASI
def init_db():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        name TEXT, 
        service TEXT, 
        phone TEXT, 
        status TEXT)''')
    conn.commit()
    conn.close()

def add_order(user_id, name, service, phone):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, name, service, phone, status) VALUES (?, ?, ?, ?, ?)",
                   (user_id, name, service, phone, "⌛ To'lov tekshirilmoqda"))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

def get_order_info(order_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, service, phone, status FROM orders WHERE id = ?", (order_id,))
    res = cursor.fetchone()
    conn.close()
    return res

# 🏠 BOSH MENYU
def bosh_menyu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Xizmatlar va Narxlar"), types.KeyboardButton("📂 Portfolio"))
    markup.add(types.KeyboardButton("📞 Buyurtma berish"), types.KeyboardButton("🔍 Buyurtmani tekshirish"))
    
    chat_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    bot.send_message(chat_id, "ProVera Dizayn markazi asosiy menyusi:", reply_markup=markup)

# 💠 XIZMATLAR BO'LIMI
@bot.message_handler(func=lambda message: message.text == "💰 Xizmatlar va Narxlar")
def xizmatlar_kategoriya(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎨 Logo va Brending", callback_data="xizmat_logo"),
        types.InlineKeyboardButton("📱 SMM Dizayn", callback_data="xizmat_smm"),
        types.InlineKeyboardButton("🗂 Poligrafiya", callback_data="xizmat_print")
    )
    bot.send_message(message.chat.id, "Bizning xizmatlarimiz va tariflarimiz:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("xizmat_"))
def callback_xizmatlar(call):
    if call.data == "xizmat_logo":
        matn = "🎨 **LOGO VA BRENDING**\n\n• Ekonom: 149 000 so'm\n• Standart: 390 000 so'm\n• Premium: 890 000 so'm"
    elif call.data == "xizmat_smm":
        matn = "📱 **SMM DIZAYN**\n\n• 1 ta post: 49 000 so'm\n• Oylik paket: 590 000 so'm"
    elif call.data == "xizmat_print":
        matn = "🗂 **POLIGRAFIYA**\n\n• Vizitka: 69 000 so'm\n• Banner: 249 000 so'mdan"
    elif call.data == "xizmatlar_back":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🎨 Logo va Brending", callback_data="xizmat_logo"),
            types.InlineKeyboardButton("📱 SMM Dizayn", callback_data="xizmat_smm"),
            types.InlineKeyboardButton("🗂 Poligrafiya", callback_data="xizmat_print")
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Bizning xizmatlarimiz:", reply_markup=markup)
        return
    else:
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="xizmatlar_back"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=matn, reply_markup=markup, parse_mode="Markdown")

# 🔍 BUYURTMANI TEKSHIRISH
@bot.message_handler(func=lambda message: message.text == "🔍 Buyurtmani tekshirish")
def check_order_start(message):
    user_id = message.from_user.id
    user_data[user_id] = {'action': 'checking_id'}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Bekor qilish"))
    bot.send_message(message.chat.id, "🔍 Buyurtma holatini tekshirish uchun ID raqamini kiriting (Masalan: 1):", reply_markup=markup)

# 🟢 ADMIN TUGMALARI BOSILGANDA (CALLBACK)
@bot.callback_query_handler(func=lambda call: call.data.startswith(("admin_accept_", "admin_reject_", "user_retry_")))
def admin_buttons_handler(call):
    # 1. Admin to'lovni tasdiqlasa va buyurtmani qabul qilsa
    if call.data.startswith("admin_accept_"):
        order_id = call.data.split("_")[2]
        info = get_order_info(order_id)
        
        if info:
            user_id, name, service, phone, _ = info
            new_status = "⚙️ Tayyorlanmoqda (Admin qabul qildi)"
            update_order_status(order_id, new_status)
            
            # Kanal/Guruh xabarini yangilash
            updated_caption = call.message.caption.replace("⌛ To'lov tekshirilmoqda", f"🟢 QABUL QILINDI\n👤 Tasdiqladi: {call.from_user.first_name}")
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=updated_caption, reply_markup=None)
            
            # Mijozga xabar berish
            try:
                bot.send_message(user_id, f"🟢 **Xushxabar!** Sizning `#{order_id}` raqamli buyurtmangiz to'lovi tasdiqlandi va ish jarayoniga topshirildi! 🚀")
            except Exception:
                pass
                
    # 2. Admin to'lov chekini rad etsa (Soxta chek yoki pul tushmagan bo'lsa)
    elif call.data.startswith("admin_reject_"):
        order_id = call.data.split("_")[2]
        info = get_order_info(order_id)
        
        if info:
            user_id, name, service, phone, _ = info
            new_status = "❌ To'lov rad etildi"
            update_order_status(order_id, new_status)
            
            # Kanal/Guruh xabarini yangilash
            updated_caption = call.message.caption.replace("⌛ To'lov tekshirilmoqda", f"❌ TO'LOV RAD ETILDI\n👤 Rad etdi: {call.from_user.first_name}")
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=updated_caption, reply_markup=None)
            
            # Mijozga qayta yuborish inline tugmasi bilan xabar yuborish
            try:
                retry_markup = types.InlineKeyboardMarkup()
                retry_markup.add(types.InlineKeyboardButton("🔄 Chekni qayta yuborish", callback_data=f"user_retry_{name}_{service}_{phone}"))
                
                bot.send_message(
                    user_id, 
                    f"❌ **Ogohlantirish!** Siz yuborgan to'lov cheki admin tomonidan tasdiqlanmadi (Chek xato yoki pul tushmagan).\n\n"
                    f"Iltimos, qaytadan to'g'ri skrinshotni yuborish uchun quyidagi tugmani bosing:", 
                    reply_markup=retry_markup
                )
            except Exception:
                pass

    # 3. Mijoz chekni qayta yuborish tugmasini bosganda
    elif call.data.startswith("user_retry_"):
        _, _, name, service, phone = call.data.split("_")
        user_id = call.from_user.id
        
        user_data[user_id] = {
            'step': 4,
            'name': name,
            'service': service,
            'phone': phone
        }
        
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Bekor qilish"))
        bot.send_message(user_id, f"💳 **To'lovni qayta yuborish bosqichi**\n\nRekvizit: `{KARTA_RAQAM}` ({KARTA_EGASI})\n\nIltimos, haqiqiy to'lov chekini rasm (skrinshot) holatida shu yerga yuboring:", reply_markup=markup)

# 🚀 ASOSIY MATRIX (TEXT, CONTACT, PHOTO ISHLOVCHI)
@bot.message_handler(content_types=['text', 'contact', 'photo'])
def handle_all(message):
    user_id = message.from_user.id
    text = message.text

    # Bekor qilish tugmasi yoki /start bosilsa
    if text in ["/start", "❌ Bekor qilish"]:
        if user_id in user_data: 
            del user_data[user_id]
        bosh_menyu(message)
        return
        
    elif text == "📂 Portfolio":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎨 Portfolioni ko'rish", url=f"https://t.me/{PORTFOLIO_KANAL}"))
        bot.send_message(message.chat.id, "Bizning amalga oshirgan ishlarimiz:", reply_markup=markup)
        return

    elif text == "📞 Buyurtma berish":
        user_data[user_id] = {'step': 1}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Bekor qilish"))
        bot.send_message(message.chat.id, "📝 1-Bosqich: Ism va familiyangizni yozing:", reply_markup=markup)
        return

    # Buyurtma holatini tekshirish jarayoni
    if user_id in user_data and user_data[user_id].get('action') == 'checking_id':
        if not text.isdigit():
            bot.send_message(message.chat.id, "⚠️ Iltimos, faqat raqamlardan iborat buyurtma ID sini kiriting:")
            return
            
        info = get_order_info(int(text))
        if info:
            _, name, service, phone, status = info
            bot.send_message(message.chat.id, f"📊 **BUYURTMA MA'LUMOTLARI (ID: #{text})**\n\n👤 Mijoz: {name}\n💼 Xizmat: {service}\n📌 Holati: *{status}*", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ `#{text}` raqamli buyurtma tizimdan topilmadi.")
        
        del user_data[user_id]
        bosh_menyu(message)
        return

    # Buyurtma berish qadamlari nazorati
    if user_id in user_data and 'step' in user_data[user_id]:
        step = user_data[user_id].get('step')
        
        if step == 1:
            user_data[user_id]['name'] = text
            user_data[user_id]['step'] = 2
            bot.send_message(message.chat.id, "💼 2-Bosqich: Qaysi xizmat turi kerak? (Masalan: Standart Logo, SMM post):")
            
        elif step == 2:
            user_data[user_id]['service'] = text
            user_data[user_id]['step'] = 3
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("📱 Kontaktni ulash", request_contact=True), types.KeyboardButton("❌ Bekor qilish"))
            bot.send_message(message.chat.id, "📞 3-Bosqich: Telefon raqamingizni yuboring (yoki pastdagi tugmani bosing):", reply_markup=markup)
            
        elif step == 3:
            phone = message.contact.phone_number if message.contact else text
            user_data[user_id]['phone'] = phone
            user_data[user_id]['step'] = 4
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("❌ Bekor qilish"))
            
            matn = (f"💳 **4-Bosqich: To'lov tizimi**\n\n"
                    f"Buyurtmani tasdiqlash uchun ko'rsatilgan kartaga to'lov qiling:\n"
                    f" Rekvizit: `{KARTA_RAQAM}`\n"
                    f"👤 Egasi: *{KARTA_EGASI}*\n\n"
                    f"📥 To'lovni amalga oshirib, chek skrinshotini shu yerga **rasm shaklida** yuboring.")
            bot.send_message(message.chat.id, matn, parse_mode="Markdown", reply_markup=markup)
            
        elif step == 4:
            if not message.photo:
                bot.send_message(message.chat.id, "⚠️ Iltimos, to'lov chekini faqat rasm (skrinshot) ko'rinishida yuboring!")
                return
                
            name = user_data[user_id]['name']
            service = user_data[user_id]['service']
            phone = user_data[user_id]['phone']
            
            order_id = add_order(user_id, name, service, phone)
            
            # Admin guruhiga boradigan xabar formati va tugmalari
            caption = (f"💰 **YANGI BUYURTMA (ID: #{order_id})**\n\n"
                       f"👤 Mijoz: {name}\n"
                       f"💼 Xizmat: {service}\n"
                       f"📞 Tel: {phone}\n"
                       f"📌 Holat: ⌛ To'lov tekshirilmoqda")
                       
            admin_markup = types.InlineKeyboardMarkup()
            admin_markup.add(
                types.InlineKeyboardButton("🟢 Qabul qilindi", callback_data=f"admin_accept_{order_id}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_reject_{order_id}")
            )
            
            try:
                bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=caption, reply_markup=admin_markup)
                bot.send_message(message.chat.id, f"🎉 Rahmat! To'lov chekingiz adminlarga tekshirish uchun yuborildi. Buyurtma ID raqamingiz: `#{order_id}`")
            except Exception as e:
                bot.send_message(message.chat.id, "⚠️ Xatolik yuz berdi, bot guruhda admin ekanligini tekshiring.")
            
            del user_data[user_id]
            bosh_menyu(message)

# 🌐 Flask yo'nalishi (Render o'chib qolmasligi uchun)
@server.route('/')
def webhook():
    return "ProVera Bot is active", 200

def run_bot():
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

# 🔄 RENDER BEPUL TARIFIDA BOTNI UYG'OQ SAQLASH (PING TIZIMI)
def keep_alive():
    while True:
        try:
            # Localhost orqali serverni har 10 daqiqada uyg'otib turadi
            requests.get("http://0.0.0.0:5000/")
        except Exception:
            pass
        time.sleep(600)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
