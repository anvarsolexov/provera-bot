import telebot
from telebot import types
import os
from flask import Flask
import threading
import re

# Render veb-serveri
server = Flask(__name__)

# Botingiz tokeni
TOKEN = '8760453840:AAEjCAOwtGZ-d8xGiIpaZ5xQ2MmeDasYZpI'
bot = telebot.TeleBot(TOKEN)

# 🚀 SIZNING HAQIQIY PORTFOLIO KANALINGIZ HAVOLASI (Boshidagi @ belgisiz)
KANAL_USERNAME = "ProVera_Design_Portfolio"  

# Guruh ID raqami (Buyurtmalar tushadigan joy)
ADMIN_CHAT_ID = "-1003997246734"  

user_data = {}

def check_sub(user_id):
    try:
        # Haqiqiy portfolio kanalingiz orqali a'zolikni tekshirish
        member = bot.get_chat_member(f"@{KANAL_USERNAME}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Tekshirishda xato: {e}")
        # Agar qandaydir texnik uzilish bo'lsa, mijoz bloklanib qolmasligi uchun True qaytaramiz
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
        btn_kanal = types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{KANAL_USERNAME}")
        btn_check = types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")
        inline_markup.add(btn_kanal)
        inline_markup.add(btn_check)
        
        bot.send_message(
            message.chat.id, 
            "👋 Assalomu aleykum!\n\nBotdan to'liq foydalanish uchun iltimos birinchi bo'lib rasmiy kanalimizga a'zo bo'ling. 👇", 
            reply_markup=inline_markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check(call):
    if check_sub(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, "🎉 Rahmat! Obuna tasdiqlandi.")
        bosh_menyu(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz. Iltimos, oldin a'zo bo'ling!", show_alert=True)

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
        if user_id in user_data:
            del user_data[user_id]
        bot.send_message(message.chat.id, "❌ Buyurtma berish jarayoni bekor qilindi.")
        bosh_menyu(message)
        return

    if user_id in user_data and message.text != "✍️ Onlayn Buyurtma berish":
        process_order_steps(message)
        return

    if message.text == "📱 Ilovani yuklab olish":
        bot.send_message(message.chat.id, "Ilovani yuklab olish uchun havola: https://share.google/yYkrudNSAmI7V...")
        
    elif message.text == "💰 Xizmatlar va Narxlar":
        narxlar_matni = (
            "✨ *ProVera Design — Grafik dizayn xizmatlari va narxlari:* \n\n"
            "🔥 *Asosiy xizmatlarimiz:* \n"
            "1️⃣ *Logo yaratish (Brending):* \n"
            "└ 50 000 so'mdan — 500 000 so'mgacha\n\n"
            "2️⃣ *Vizitkalar va Korporativ kartalar:* \n"
            "└ 60 000 so'mdan — 800 000 so'mgacha\n\n"
            "3️⃣ *Banner, Flayer va Bukletlar (Poligrafiya):* \n"
            "└ 100 000 so'mdan — 700 000 so'mgacha\n\n"
            "4️⃣ *SMM postlar va Storizlar uchun dizayn:* \n"
            "└ 40 000 so'mdan — 300 000 so'mgacha\n\n"
            "5️⃣ *Tashqi reklama (Bilbord va Vitrina dizayni):* \n"
            "└ 150 000 so'mdan — 1 200 000 so'mgacha\n\n"
            "6️⃣ *Sertifikat, Diplom va Taklifnomalar:* \n"
            "└ 30 000 so'mdan — 250 000 so'mgacha\n\n"
            "⚙️ *Boshqa barcha turdagi grafik xizmatlar:* \n"
            "• Firma stillari (Brandbook) yaratish\n"
            "• Qadoq va etiketka (Packaging) dizayni\n"
            "• Kitob, jurnal va kataloglarni sahifalash\n"
            "• Futbolka, krujka va merch mahsulotlari uchun printlar\n"
            "• Menu dizayni (Restoran va kafelar uchun)\n"
            "• Vektorli illyustratsiyalar va chizmalar\n"
            "• Fotosuratlarni professional retush qilish\n"
            "• Telegram uchun maxsus rasm va sticker'lar\n\n"
            "💡 _Eslatma: Yakuniy narx buyurtmaning murakkabligi va muddatiga qarab o'zgarishi mumkin._"
        )
        bot.send_message(message.chat.id, narxlar_matni, parse_mode="Markdown")
        
    elif message.text == "📂 Portfolio (Bizning ishlar)":
        inline_portfolio = types.InlineKeyboardMarkup(row_width=1)
        btn_kanal = types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish (Kanal)", url=f"https://t.me/{KANAL_USERNAME}")
        inline_portfolio.add(btn_kanal)
        
        portfolio_matni = (
            "📂 *ProVera Design — Bizning ishlarimiz bilan tanishing!*\n\n"
            "Biz yaratgan eng sara logotiplar, SMM dizaynlar va brending loyihalarini "
            "rasmiy kanalimiz orqali to'g'ridan-to'g'ri kuzatishingiz mumkin. 👇\n\n"
            "💡 _Kanalda ishlarni oson topish uchun #logo, #smm heshteglaridan foydalaning._"
        )
        bot.send_message(message.chat.id, portfolio_matni, parse_mode="Markdown", reply_markup=inline_portfolio)
        
    elif message.text == "📞 Buyurtma berish / Aloqa":
        markup_aloqa = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_new_order = types.KeyboardButton("✍️ Onlayn Buyurtma berish")
        btn_back = types.KeyboardButton("⬅️ Orqaga (Bosh menyu)")
        markup_aloqa.add(btn_new_order, btn_back)
        
        inline_markup = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="✍️ Logomasterga yozish", url="https://t.me/ProVera_Design_Admin")
        inline_markup.add(url_button)
        
        aloqa_matni = (
            "📞 Biz bilan bog'lanish:\n\n"
            "Pastdagi '✍️ Onlayn Buyurtma berish' tugmasini bosib, bot orqali tezkor buyurtma qoldirishingiz mumkin.\n\n"
            "Yoki to'g'ridan-to'g'ri admin bilan bog'laning:\n"
            "📱 Telefon: +998200271779 | +998200057207\n"
            "🤖 Telegram: @ProVera_Design_Admin"
        )
        bot.send_message(message.chat.id, aloqa_matni, reply_markup=markup_aloqa)
        bot.send_message(message.chat.id, "Admin bilan to'g'ridan-to'g'ri suhbat ochish:", reply_markup=inline_markup)

    elif message.text == "✍️ Onlayn Buyurtma berish":
        user_data[user_id] = {'step': 1}
        markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        
        bot.send_message(message.chat.id, "📝 *1-Bosqich:* Ism va familiyangizni kiriting:", parse_mode="Markdown", reply_markup=markup_cancel)

    elif message.text == "⬅️ Orqaga (Bosh menyu)":
        bosh_menyu(message)
        
    elif message.text == "ℹ️ Yordam":
        bot.send_message(message.chat.id, "Sizga qanday yordam bera olaman? Muammo bo'lsa biz bilan bog'laning.")
        
    elif message.text == "🔍 Tekshirish (Provera)":
        bot.send_message(message.chat.id, "Tekshirish tizimi ishga tushdi...")
    else:
        bot.send_message(message.chat.id, "⚠️ *Noto'g'ri buyruq!* Iltimos, pastdagi tayyor menyu tugmalaridan birini bosing. 👇", parse_mode="Markdown")

def process_order_steps(message):
    user_id = message.from_user.id
    current_step = user_data[user_id]['step']
    text = message.text

    if current_step == 1:
        if len(text) < 3 or any(char.isdigit() for char in text):
            bot.send_message(message.chat.id, "❌ *Xato ism kiritildi!* Iltimos, ismingizni to'g'ri va faqat harflar bilan yozing:")
            return
            
        user_data[user_id]['name'] = text
        user_data[user_id]['step'] = 2
        
        markup_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_cancel.add(types.KeyboardButton("❌ Buyurtmani bekor qilish"))
        bot.send_message(message.chat.id, "💼 *2-Bosqich:* Sizga qanday xizmat kerak? (Masalan: Logo, Vizitka, SMM dizayn):", parse_mode="Markdown", reply_markup=markup_cancel)

    elif current_step == 2:
        if len(text) < 2:
            bot.send_message(message.chat.id, "❌ *Xato matn!* Iltimos, qanday dizayn xizmati kerakligini batafsilroq yozing:")
            return
            
        user_data[user_id]['service'] = text
        user_data[user_id]['step'] = 3
        
        markup_phone = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_phone = types.KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
        btn_cancel = types.KeyboardButton("❌ Buyurtmani bekor qilish")
        markup_phone.add(btn_phone, btn_cancel)
        
        bot.send_message(message.chat.id, "📞 *3-Bosqich:* Telefon raqamingizni kiriting (Masalan: +998901234567) yoki pastdagi tugma orqali yuboring:", parse_mode="Markdown", reply_markup=markup_phone)

    elif current_step == 3:
        clean_phone = re.sub(r'[^\d+]', '', text)
        if len(clean_phone) < 9:
            bot.send_message(message.chat.id, "❌ *Noto'g'ri telefon raqami!* Iltimos, raqamingizni to'g'ri formatda kiriting yoki pastdagi tugmani bosing:")
            return
            
        user_data[user_id]['phone'] = clean_phone
        finish_order(message, user_id)

@bot.message_handler(content_types=['photo', 'document', 'audio', 'video'])
def handle_other_contents(message):
    bot.send_message(message.chat.id, "⚠️ *Kutilmagan fayl yoki rasm!* Iltimos, faqat menyudagi tugmalardan foydalaning.")

def finish_order(message, user_id):
    name = user_data[user_id]['name']
    service = user_data[user_id]['service']
    phone = user_data[user_id]['phone']
    
    raw_username = message.from_user.username
    username_text = f"@{raw_username}" if raw_username else "Mavjud emas"
    
    admin_matn = (
        "🔥 YANGI BUYURTMA KELDI! 🔥\n\n"
        f"👤 Mijoz: {name}\n"
        f"💼 Xizmat turi: {service}\n"
        f"📞 Telefon: {phone}\n"
        f"🤖 Telegram profili: {username_text}\n"
    )
    
    try:
        bot.send_message(ADMIN_CHAT_ID, admin_matn)
        bot.send_message(message.chat.id, "🎉 Rahmat! Buyurtmangiz muvaffaqiyatli qabul qilindi.\n\nTez orada loyiha menejerlarimiz siz bilan bog'lanishadi.")
    except Exception as e:
        xato_xabar = f"⚠️ Tizimda xatolik! Guruhga xabar ketmadi.\nXatolik: {str(e)}"
        bot.send_message(message.chat.id, xato_xabar)
        print(f"Xatolik: {e}")
        
    if user_id in user_data:
        del user_data[user_id]
    bosh_menyu(message)

@server.route('/')
def webhook():
    return "ProVera bot is running 24/7!", 200

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
