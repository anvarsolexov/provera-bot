import telebot
from telebot import types
import os
from flask import Flask
import threading

# Renderda xatolik bermasligi uchun veb-server ochamiz
server = Flask(__name__)

TOKEN = '8760453840:AAEjCAOwtGZ-d8xGiIpaZ5xQ2MmeDasYZpI'
bot = telebot.TeleBot(TOKEN)

# /start buyrug'i kelganda bosh menyu
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Tugmalar
    btn1 = types.KeyboardButton("📱 Ilovani yuklab olish")
    btn2 = types.KeyboardButton("💰 Xizmatlar va Narxlar")
    btn3 = types.KeyboardButton("📂 Portfolio (Bizning ishlar)")
    btn4 = types.KeyboardButton("📞 Buyurtma berish / Aloqa")
    btn5 = types.KeyboardButton("🔍 Tekshirish (Provera)")
    btn6 = types.KeyboardButton("ℹ️ Yordam")
    
    # Tugmalarni joylashtirish
    markup.add(btn1, btn2)       # Ilova va Narxlar yonma-yon
    markup.add(btn3, btn4)       # Portfolio va Aloqa yonma-yon
    markup.add(btn5, btn6)       # Tekshirish va Yordam yonma-yon
    
    bot.send_message(
        message.chat.id, 
        "Assalomu aleykum! ProVera botiga qayta xush kelibsiz!\nKerakli bo'limni tanlang 👇", 
        reply_markup=markup
    )

# Matnli xabarlarni qayta ishlash
@bot.message_handler(content_types=['text'])
def handle_text(message):
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
        bot.send_message(message.chat.id, "🎨 *Bizning eng sara ishlarimiz:* \n\nTez orada bu yerga rasmlar va havolalar joylanadi. Hozircha namunalar yuklanmoqda...", parse_mode="Markdown")
        
    elif message.text == "📞 Buyurtma berish / Aloqa":
        # Inline tugma - siz kiritgan @ProVera_Design_Admin profiliga olib boradi
        inline_markup = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="✍️ Logomasterga yozish", url="https://t.me/ProVera_Design_Admin")
        inline_markup.add(url_button)
        
        # Sizning aniq raqamlaringiz va profilingiz joyida qoldi
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

# Render ping qila olishi uchun bosh sahifa
@server.route('/')
def webhook():
    return "ProVera bot is running 24/7!", 200

if __name__ == "__main__":
    # Botni alohida potokda (thread) polling qildiramiz
    threading.Thread(target=bot.infinity_polling).start()
    
    # Render portini aniqlab veb-serverni ishga tushiramiz
    port = int(os.environ.get("PORT", 5000))
    print(f"ProVera boti to'liq ma'lumotlar bilan {port}-portda ishga tushdi...")
    server.run(host="0.0.0.0", port=port)
