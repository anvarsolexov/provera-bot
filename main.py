import telebot
from telebot import types
import sqlite3
from datetime import datetime
import re

# 🔑 TOKEN
TOKEN = '8923702378:AAEAqjs2hxkFEtgzHPE0tBUGLt0h7C36MrY'
bot = telebot.TeleBot(TOKEN)

# ⚙️ KONFIGURATSIYA
PORTFOLIO_KANAL = "ProVera_Design_Portfolio"
ADMIN_CHAT_ID = "-1003997246734"
KARTA_RAQAM = "5614 6818 5637 1004"
KARTA_EGASI = "Anvar Solexov"

user_data = {}

# 🗄 BAZA BILAN ISHLASH
def init_db():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, name TEXT, service TEXT, phone TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

def add_order(user_id, name, service, phone):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, name, service, phone, status) VALUES (?, ?, ?, ?, ?)",
                   (user_id, name, service, phone, "⌛ To'lov tekshirilmoqda"))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

# 🏠 BOSH MENYU
def bosh_menyu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Xizmatlar va Narxlar"), types.KeyboardButton("📂 Portfolio"))
    markup.add(types.KeyboardButton("📞 Buyurtma berish"), types.KeyboardButton("🔍 Buyurtmani tekshirish"))
    bot.send_message(message.chat.id, "ProVera Dizayn markaziga xush kelibsiz!", reply_markup=markup)

# 💠 XIZMATLAR (Pog‘onali menyu)
@bot.message_handler(func=lambda message: message.text == "💰 Xizmatlar va Narxlar")
def xizmatlar_kategoriya(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎨 Logo va Brending", callback_data="xizmat_logo"),
        types.InlineKeyboardButton("📱 SMM Dizayn", callback_data="xizmat_smm"),
        types.InlineKeyboardButton("🗂 Poligrafiya", callback_data="xizmat_print")
    )
    bot.send_message(message.chat.id, "Bizning xizmatlarimiz:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("xizmat_"))
def callback_xizmatlar(call):
    if call.data == "xizmat_logo":
        matn = "🎨 **LOGO VA BRENDING**\n\n• Ekonom: 149 000 so'm\n• Standart: 390 000 so'm\n• Premium: 890 000 so'm"
    elif call.data == "xizmat_smm":
        matn = "📱 **SMM DIZAYN**\n\n• 1 ta post: 49 000 so'm\n• Oylik paket: 590 000 so'm"
    elif call.data == "xizmat_print":
        matn = "🗂 **POLIGRAFIYA**\n\n• Vizitka: 69 000 so'm\n• Banner: 249 000 so'mdan"
    else: return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="xizmatlar_back"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=matn, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "xizmatlar_back")
def back_xizmat(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎨 Logo va Brending", callback_data="xizmat_logo"),
        types.InlineKeyboardButton("📱 SMM Dizayn", callback_data="xizmat_smm"),
        types.InlineKeyboardButton("🗂 Poligrafiya", callback_data="xizmat_print")
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Bizning xizmatlarimiz:", reply_markup=markup)

# 🚀 BUYURTMA QABUL QILISH
@bot.message_handler(func=lambda message: message.text == "📞 Buyurtma berish")
def start_order(message):
    user_data[message.from_user.id] = {'step': 1}
    bot.send_message(message.chat.id, "📝 1-Bosqich: Ismingizni yozing:")

@bot.message_handler(content_types=['text', 'contact', 'photo'])
def handle_all(message):
    user_id = message.from_user.id
    if user_id in user_data:
        step = user_data[user_id].get('step')
        if step == 1:
            user_data[user_id]['name'] = message.text
            user_data[user_id]['step'] = 2
            bot.send_message(message.chat.id, "💼 2-Bosqich: Qaysi xizmat kerak?")
        elif step == 2:
            user_data[user_id]['service'] = message.text
            user_data[user_id]['step'] = 3
            bot.send_message(message.chat.id, "📞 3-Bosqich: Telefon raqamni yuboring:")
        elif step == 3:
            phone = message.contact.phone_number if message.contact else message.text
            user_data[user_id]['phone'] = phone
            user_data[user_id]['step'] = 4
            bot.send_message(message.chat.id, f"💳 4-Bosqich: To'lovni {KARTA_RAQAM} ga qiling va chekni yuboring.")
        elif step == 4 and message.photo:
            # Buyurtmani admin kanalga yuborish
            order_id = add_order(user_id, user_data[user_id]['name'], user_data[user_id]['service'], user_data[user_id]['phone'])
            caption = f"💰 YANGI BUYURTMA ID: #{order_id}\nMijoz: {user_data[user_id]['name']}\nXizmat: {user_data[user_id]['service']}"
            bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=caption)
            bot.send_message(message.chat.id, "✅ Buyurtmangiz qabul qilindi!")
            del user_data[user_id]
            bosh_menyu(message)
    elif message.text == "/start":
        bosh_menyu(message)
    elif message.text == "📂 Portfolio":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎨 Ko'rish", url=f"https://t.me/{PORTFOLIO_KANAL}"))
        bot.send_message(message.chat.id, "Bizning ishlar:", reply_markup=markup)

if __name__ == "__main__":
    bot.infinity_polling()
