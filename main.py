import telebot
from telebot import types
import os
from flask import Flask
import threading

# Renderda xatolik bermasligi uchun veb-server ochamiz
server = Flask(__name__)

TOKEN = '8760453840:AAEjCAOwtGZ-d8xGiIpaZ5xQ2MmeDasYZpI'
bot = telebot.TeleBot(TOKEN)

KANAL_USERNAME = "@ProVera_Design"  # Sizning kanalingiz

# Foydalanuvchi kanalga a'zo bo'lganini tekshirish funksiyasi
def check_sub(user_id):
    try:
        member = bot.get_chat_member(KANAL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        # Agar bot kanalda admin bo'lmasa yoki xatolik bo'lsa, foydalanuvchini o'tkazib yuboradi
        return True

# Bosh menyuni chiqarish funksiyasi
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

# /start buyrug'i kelganda
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "Assalomu aleykum! ProVera botiga qayta xush kelibsiz!")
        bosh_menyu(message)
    else:
        # Kanalga a'zo bo'lishni so'rash
        inline_markup = types.InlineKeyboardMarkup()
        btn_kanal = types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{KANAL_USERNAME[1:]}")
        btn_check = types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")
        inline_markup.add(btn_kanal)
        inline_markup.add(btn_check)
        
        bot.send_message(
            message.chat.id, 
            "👋 Assalomu aleykum!\n\nBotdan to'liq foydalanish uchun iltimos birinchi bo'lib rasmiy kanalimizga a'zo bo'ling. 👇", 
            reply_markup=inline_markup
        )

# Inline tugmalar bosilganda (Tekshirish tugmasi uchun)
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🎉 Rahmat! Obuna tasdiqlandi.")
        bosh_menyu(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz. Iltimos, oldin a'zo bo'ling!", show_alert=True)

# Matnli xabarlarni qayta ishlash
@bot.message_handler(content_types=['text'])
def handle_text(message):
    # Har bir tugma bosilganda ham obunani tekshiramiz
    if not check_sub(message.from_user.id):
        send_welcome(message)
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
            "_(Ushbu xizmatlar narxi buyurtma hajmiga qarab individual kelishiladi)_\n"
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
        inline_portfolio = types.InlineKeyboardMarkup()
        btn_port = types.InlineKeyboardButton(text="🎨 Portfolioni ko'rish (Kanal)", url=f"https://t.me/{KANAL_USERNAME[1:]}")
        inline_portfolio.add(btn_port)
        bot.send_message(
            message.chat.id, 
            "🎨 *Bizning eng sara ishlarimiz bilan kanalda tanishishingiz mumkin:*", 
            parse_mode="Markdown", 
            reply_markup=inline_portfolio
        )
        
    elif message.text == "📞 Buyurtma berish / Aloqa":
        inline_markup = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="✍️ Logomasterga yozish", url="https://t.me/ProVera_Design_Admin")
        inline_markup.add(url_button)
        
        aloqa_matni = (
            "📞 *Biz bilan bog'lanish:*\n\n"
            "Savollar, takliflar yoki buyurtmalar bo'yicha to'g'ridan-to'g'ri admin bilan bog'lanishingiz mumkin.\n\n"
            "📱 *Telefon:* +998200271779 | +998200057207\n"
            "🤖 *Telegram:* @ProVera_Design_Admin"
        )
        bot.send_message(message.chat.id, aloqa_matni, parse_mode="Markdown", reply_markup=inline_markup)
        
    elif message.text == "ℹ️ Yordam":
        bot.send_message(message.chat.id, "Sizga qanday yordam bera olaman? Muammo bo'lsa biz bilan bog'laning.")
        
    elif message.text == "🔍 Tekshirish (Provera)":
        bot.send_message(message.chat.id, "Tekshirish tizimi ishga tushdi...")
    else:
        bot.send_message(message.chat.id, "Iltimos, pastdagi tayyor tugmalardan birini bosing. 👇")

@server.route('/')
def webhook():
    return "ProVera bot is running 24/7!", 200

if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
