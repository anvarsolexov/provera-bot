import telebot
from telebot import types

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
            "✨ *ProVera Design xizmatlari va narxlari:* \n\n"
            "🎨 *Logo yaratish:* \n"
            "└ 50 000 so'mdan — 500 000 so'mgacha\n\n"
            "📇 *Vizitkalar:* \n"
            "└ 60 000 so'mdan — 800 000 so'mgacha\n\n"
            "💡 _Narxlar buyurtmaning murakkabligiga qarab o'zgarishi mumkin._"
        )
        bot.send_message(message.chat.id, narxlar_matni, parse_mode="Markdown")
        
    elif message.text == "📂 Portfolio (Bizning ishlar)":
        bot.send_message(message.chat.id, "🎨 *Bizning eng sara ishlarimiz:* \n\nTez orada bu yerga rasmlar va havolalar joylanadi. Hozircha namunalar yuklanmoqda...", parse_mode="Markdown")
        
    elif message.text == "📞 Buyurtma berish / Aloqa":
        # Inline tugma - bosganda to'g'ridan-to'g'ri sizning profilingiz ochiladi
        inline_markup = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="✍️ Logomasterga yozish", url="https://t.me/ProVera_Design_Admin")
        inline_markup.add(url_button)
        
        aloqa_matni = (
            "📞 *Biz bilan bog'lanish:*\n\n"
            "Savollar, takliflar yoki buyurtmalar bo'yicha to'g'ridan-to'g'ri admin bilan bog'lanishingiz mumkin.\n\n"
            "📱 *Telefon:* +998200271779 +998200057207\n"  # Bu yerga o'z raqamingizni yozib qo'yishingiz mumkin
            "🤖 *Telegram:* @ProVera_Design_Admin"
        )
        bot.send_message(message.chat.id, aloqa_matni, parse_mode="Markdown", reply_markup=inline_markup)
        
    elif message.text == "ℹ️ Yordam":
        bot.send_message(message.chat.id, "Sizga qanday yordam bera olaman? Muammo bo'lsa biz bilan bog'laning.")
        
    elif message.text == "🔍 Tekshirish (Provera)":
        bot.send_message(message.chat.id, "Tekshirish tizimi ishga tushdi...")
        
    else:
        bot.send_message(message.chat.id, "Iltimos, pastdagi tayyor tugmalardan birini bosing. 👇")

# Botni ishga tushirish
print("ProVera boti to'liq ma'lumotlar bilan ishga tushdi...")
bot.infinity_polling()
