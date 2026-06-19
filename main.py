import telebot
from telebot import types
import os
from flask import Flask
import threading
import re
import sqlite3
from datetime import datetime

# 🌐 Render xatolik bermasligi uchun Flask veb-serveri
server = Flask(__name__)

# 🔑 YANGI VA TOZA TELEGRAM BOT TOKEN
TOKEN = '8923702378:AAF-6fjEd4Lw705wH7B9AZggmIWcftbvhA8'
bot = telebot.TeleBot(TOKEN)

# 🛑 REKLAMANI CHIQARMASLIK UCHUN WEBHOOK TOZALAGICH
try:
    bot.remove_webhook(drop_pending_updates=True)
    print("Eski ulanishlar muvaffaqiyatli tozalandi!")
except Exception as e:
    print(f"Webhookni o'chirishda xatolik: {e}")

# ⚙️ BOT CHUBURQLARINI (COMMANDS) KOD ORQALI AVTOMATIK O'RNATISH
def set_bot_commands():
    try:
        commands = [
            types.BotCommand("start", "Botni qayta ishga tushirish (Bosh menyu)")
        ]
        bot.set_my_commands(commands)
        print("Bot buyruqlari muvaffaqiyatli o'rnatildi!")
    except Exception as e:
        print(f"Buyruqlarni o'rnatishda xatolik: {e}")

set_bot_commands()

# 📂 PORTFOLIO KANALI LINKI
PORTFOLIO_KANAL = "ProVera_Design_Portfolio"  

# 📢 BUYURTMALAR TUSHADIGAN KANAL ID (YOKI @KANAL_LINKI)
ADMIN_CHAT_ID = "-1003997246734"  

# 💳 TO'LOV MA'LUMOTLARI
KARTA_RAQAM = "5614 6818 5637 1004"
KARTA_EGASI = "Anvar Solexov"

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
        (user_id, name, service, phone, "⌛ To'lov tekshirilmoqda")
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

# 🟢 CALL BACK REAKSIYALARI (ADMIN VA MIJOZ TUGMALARI)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    
    # 1. ADMIN BUYURTMANI QABUL QILGANDA
    if call.data.startswith("accept_"):
        order_id = call.data.split("_")[1]
        new_status = "⚙️ Jarayonda (Admin qabul qildi)"
        
        conn = sqlite3.connect("orders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, service, name, phone FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        
        if res:
            user_id, service, name, phone = res
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            
            admin_user = call.from_user.first_name
            current_time = datetime.now().strftime("%H:%M")
            
            raw_username = "Mavjud emas"
            if "🤖 Telegram profili:" in call.message.caption:
                try:
                    raw_username = call.message.caption.split("🤖 Telegram profili:")[1].split("\n")[0].strip()
                except Exception:
                    pass

            updated_caption = (
                f"✅ **BUYURTMA QABUL QILINDI (ID: #{order_id})** ✅\n\n"
                f"👤 Mijoz: {name}\n"
                f"💼 Xizmat: {service}\n"
                f"📞 Telefon: {phone}\n"
                f"🤖 Telegram profili: {raw_username}\n\n"
                f"🟢 **HOLAT:** Admin ({admin_user}) soat {current_time} da to'lovni tasdiqladi va ishni qabul qildi!"
            )
            
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=updated_caption, reply_markup=None)
            bot.answer_callback_query(call.id, "Buyurtma jarayonga olindi!")
            
            try:
                user_msg = (
                    f"🟢 **Xushxabar! Sizning buyurtmangiz admin tomonidan tasdiqlandi!**\n\n"
                    f"🆔 Buyurtma raqami: `#{order_id}`\n"
                    f"💼 Xizmat: {service}\n"
                    f"⚙️ Holati: *Hozirda jarayonda*\n\n"
                    f"Dizaynerlarimiz ishni boshlashdi, tayyor bo'lishi bilan sizga xabar yuboramiz! 🚀"
                )
                bot.send_message(user_id, user_msg, parse_mode="Markdown")
            except Exception:
                pass
        conn.close()

    # 2. ADMIN TO'LOVNI RAD ETGANDA (SOXTA CHEK HOLATI)
    elif call.data.startswith("reject_"):
        order_id = call.data.split("_")[1]
        new_status = "❌ Rad etildi (To'lov tasdiqlanmadi)"
        
        conn = sqlite3.connect("orders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, service, name, phone FROM orders WHERE id = ?", (order_id,))
        res = cursor.fetchone()
        
        if res:
            user_id, service, name, phone = res
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            
            admin_user = call.from_user.first_name
            current_time = datetime.now().strftime("%H:%M")
            
            raw_username = "Mavjud emas"
            if "🤖 Telegram profili:" in call.message.caption:
                try:
                    raw_username = call.message.caption.split("🤖 Telegram profili:")[1].split("\n")[0].strip()
                except Exception:
                    pass

            updated_caption = (
                f"❌ **BUYURTMA RAD ETILDI (ID: #{order_id})** ❌\n\n"
                f"👤 Mijoz: {name}\n"
                f"💼 Xizmat: {service}\n"
                f"📞 Telefon: {phone}\n"
                f"🤖 Telegram profili: {raw_username}\n\n"
                f"🔴 **HOLAT:** Admin ({admin_user}) soat {current_time} da to'lovni rad etdi (Chek soxta yoki pul tushmagan)!"
            )
            
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=updated_caption, reply_markup=None)
            bot.answer_callback_query(call.id, "Buyurtma rad etildi!")
            
            try:
                # 🔄 MIJOZGA QAYTA YUBORISH TUGMASI
                retry_inline = types.InlineKeyboardMarkup()
                retry_inline.add(types.InlineKeyboardButton("🔄 Chekni qayta yuborish", callback_data=f"retry_{name}_{service}_{phone}"))
                
                user_msg = (
                    f"❌ **Ogohlantirish! Siz yuborgan to'lov cheki admin tomonidan tasdiqlanmadi.**\n\n"
                    f"🆔 Buyurtma raqami: `#{order_id}`\n"
                    f"💼 Xizmat: {service}\n"
                    f"📌 Holati: *To'lov rad etildi*\n\n"
                    f"⚠️ Siz yuborgan rasmda xatolik bo'lishi mumkin. Haqiqiy to'lov chekini (skrinshotini) qayta yuborish uchun pastdagi tugmani bosing:"
                )
                bot.send_message(user_id, user_msg, parse_mode="Markdown", reply_markup=retry_inline)
            except Exception:
                pass
        conn.close()

    # 3. MIJOZ "CHEKNI QAYTA YUBORISH" TUGMASINI BOSGANDA
    elif call.data.startswith("retry_"):
        _, name, service, phone = call.data.split("_")
        user_id = call.from_user.id
        
        # Mijozni qaytadan 4-bosqichga tizimga kiritamiz
        user_data[user_id] = {
            'step': 4,
            'name': name,
            'service': service,
            'phone': phone
        }
        
        # Tugmani olib tashlash uchun eski xabarni o'chirish yoki tahrirlash
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
            
        goToPaymentStep(call.message, user_id)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id].get('step') == 3:
        user_data[user_id]['phone'] = message.contact.phone_number
        goToPaymentStep(message, user_id)
    else:
        bot.send_message(message.chat.id, "⚠️ Hozir telefon raqam yuborish bosqichi emas.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id].get('step') == 4:
        name = user_data[user_id]['name']
        service = user_data[user_id]['service']
        phone = user_data[user_id]['phone']
        
        order_id = add_order(user_id, name, service, phone)
        raw_username = message.from_user.username
        username_text = f"@{raw_username}" if raw_username else "Mavjud emas"
        
        kanal_matn = (
            f"💰 **YANGI BUYURTMA + TO'LOV CHEKI (ID: #{order_id})** 💰\n\n"
            f"👤 Mijoz: {name}\n"
            f"💼 Xizmat: {service}\n"
            f"📞 Telefon: {phone}\n"
            f"🤖 Telegram profili: {username_text}\n\n"
            f"📌 Kelib tushgan holati: ⌛ To'lov tekshirilmoqda\n"
            f"⚖️ Shart: 50% avans bo'lsa, yakunda tiniq format berilmaydi!"
        )
        
        kanal_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_accept = types.InlineKeyboardButton("🟢 Qabul qilindi (Jarayonga olish)", callback_data=f"accept_{order_id}")
        btn_reject = types.InlineKeyboardButton("❌ Rad etildi (To'lov tasdiqlanmadi)", callback_data=f"reject_{order_id}")
        kanal_inline.add(btn_accept, btn_reject)
        
        try:
            bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=kanal_matn, reply_markup=kanal_inline)
            
            bot.send_message(
                message.chat.id, 
                f"🎉 **Rahmat! To'lov chekingiz qabul qilindi va maxsus buyurtmalar kanaliga yo'naltirildi.**\n\n"
                f"Sizning buyurtma raqamingiz: `#{order_id}`\n"
                f"Admin chekni ko'rib, buyurtmani tasdiqlashi bilan sizga avtomatik xabar boradi! 🚀",
                reply_markup=None,
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.send_message(message.chat.id, "⚠️ Tizimda xatolik yuz berdi. Yangi bot kanalda admin ekanligini tekshiring.")
            print(e)
            
        if user_id in user_data: 
            del user_data[user_id]
        bosh_menyu(message)
    else:
        bot.send_message(message.chat.id, "⚠️ Iltimos, faqat buyurtma to'lov bosqichida chek rasmini yuboring.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if message.text == "❌ Buyurtmani bekor qilish":
        if user_id in user_data: 
            del user_data[user_id]
        bot.send_message(message.chat.id, "❌ Amaliyot bekor qilindi.")
        bosh_menyu(message)
        return

    if user_id in user_data and 'step' in user_data[user_id] and user_data[user_id]['step'] in [1, 2, 3] and message.text != "✍️ Onlayn Buyurtma berish":
        process_order_steps(message)
        return

    if user_id in user_data and user_data[user_id].get('action') == 'checking_id':
        process_checking_id(message)
        return

    if message.text == "📱 Ilovani yuklab olish":
        inline_ilova = types.InlineKeyboardMarkup()
        btn_link = types.InlineKeyboardButton("📥 Yuklab olish (Google Drive)", url="https://share.google/yYkrudNSAmI7V...")
        inline_ilova.add(btn_link)
        bot.send_message(message.chat.id, "ProVera rasmiy ilovasini yuklab olish uchun quyidagi tugmani bosing: 👇", reply_markup=inline_ilova)
        
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
        
    elif message.text == "📂 Portfolio (Bizning ishlar)":
        inline_portfolio = types.InlineKeyboardMarkup(row_width=1)
        btn_kanal = types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish (Kanal)", url=f"https://t.me/{PORTFOLIO_KANAL}")
        inline_portfolio.add(btn_kanal)
        
        portfolio_matni = (
            "📂 *ProVera Design — Bizning ishlarimiz bilan tanishing!*\n\n"
            "Biz yaratgan eng sara logotiplar maxsus portfolio kanalimizda! 👇"
        )
        bot.send_message(message.chat.id, portfolio_matni, parse_mode="Markdown", reply_markup=inline_portfolio)
        
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
        if user_id in user_data and user_data[user_id].get('step') == 4:
            bot.send_message(message.chat.id, "⚠️ Iltimos, to'lov chekini rasm (skrinshot) ko'rinishida yuboring!")
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
        goToPaymentStep(message, user_id)

def goToPaymentStep(message, user_id):
    user_data[user_id]['step'] = 4
    markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
    
    payment_text = (
        f"💳 **4-Bosqich: To'lov tizimi** 💳\n\n"
        f"Buyurtmangizni tasdiqlash va ishni boshlashimiz uchun to'lovni amalga oshirishingiz lozim.\n\n"
        f"Xohishingizga ko'ra **100% oldindan** yoki **50% avans** sifatida to'lov qilishingiz mumkin. "
        f"⚠️ *Eslatma:* Agar 50% to'lov qilinsa, ish yakunlangach qolgan 50% to'lanmaguncha dizayn sizga original (tiniq) formatda berilmaydi.\n\n"
        f"📌 **To'lov rekvizitlari:**\n"
        f"💳 Karta raqam: `{KARTA_RAQAM}`\n"
        f"👤 Karta egasi: *{KARTA_EGASI}*\n\n"
        f"📥 To'lovni amalga oshirgach, **to'lov chekini (skrinshotini) mana shu yerga rasm ko'rinishida yuboring:**"
    )
    
    # Agar chat_id bo'lsa (callback orqali chaqirilganda) o'sha chatga yuboradi
    chat_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    bot.send_message(chat_id, payment_text, parse_mode="Markdown", reply_markup=markup_cancel)

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

@server.route('/')
def webhook():
    return "ProVera Bot is active", 200

def run_bot():
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
