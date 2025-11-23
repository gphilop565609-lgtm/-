import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonSpam
from re import compile as compile_link
from os import listdir
from datetime import datetime, timedelta
import random
from telethon.errors import SessionPasswordNeededError, FloodWaitError

# Данные для подключения к Telegram API
api_id = 30613385
api_hash = 'c2483a1b8392956601e2004e0316ed83'
bot_token = '8300485475:AAFWJBhXprvRlUiyz84g1coN_67hxWFfBqE'

# Инициализация клиента бота
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# ID администраторов, owner и лог-чата
admins_id = [8349769663]
owner_id = 8349769663
log_chat_id = -1002327568113
whitelist = set()
path = "sessions/"

# Загрузка данных из файлов (админы и "белый список")
def load_admins():
    global admins_id
    try:
        with open("adm.txt", "r") as file:
            admins_id = [int(line.strip()) for line in file.readlines()]
    except FileNotFoundError:
        admins_id = []

def load_whitelist():
    global whitelist
    try:
        with open('white.txt', 'r') as file:
            whitelist = {int(line.strip()) for line in file if line.strip()}
    except FileNotFoundError:
        open('white.txt', 'w').close()

report_texts = [
    "Сообщение содержит спам",
    "Это сообщение нарушает правила сообщества",
    "Содержанимое сообщения является неприемлемым",
    "Спам",
    "Спам. Примите меры",
    "Спам. Пожалуйста, примите меры",
    "Этот контент нарушает политику сервиса",
    "Этот контент нарушает политику Телаграмм",
    "Этот контент нарушает политику Telegram",
    "Сообщение кажется подозрительным",
    "Прошу удалить это сообщение",
    "Нарушение правил сообщества. Рассмотрите",
    "Нарушение правил"
]

# Функция отправки жалоб на сообщения
async def report_message(link):
    # Код остаётся без изменений
    message_link_pattern = compile_link(r'https://t.me/(?P<username_or_chat>.+)/(?P<message_id>\d+)')
    match = message_link_pattern.search(link)

    if not match:
        return 0, 0

    chat = match.group("username_or_chat")
    message_id = int(match.group("message_id"))

    files = listdir(path)
    sessions = [s for s in files if s.endswith(".session") and s != 'bot.session']

    successful_reports = 0
    failed_reports = 0

    for session in sessions:
        try:
            async with TelegramClient(f"{path}{session}", api_id, api_hash) as client:
                if not await client.is_user_authorized():
                    print(f"Сессия {session} не авторизована, пропуск.")
                    failed_reports += 1
                    await client.disconnect()
                    continue

                try:
                    # Получаем сущность для жалобы
                    entity = await client.get_entity(chat)
                    report_reason = random.choice(report_texts)

                    # Отправляем жалобу
                    await client(ReportRequest(
                        peer=entity,
                        id=[message_id],
                        reason=InputReportReasonSpam(),
                        message=report_reason
                    ))

                    print(f"Жалоба отправлена через сессию {session}. Номер жалобы: {successful_reports}")
                    successful_reports += 1

                except FloodWaitError as e:
                    wait_time = e.seconds
                    print(f"Flood wait error: необходимо подождать {wait_time} секунд. Пауза перед продолжением.")

                except Exception as e:
                    print(f"Ошибка при отправке жалобы через сессию {session}: {e}")
                    failed_reports += 1

        except SessionPasswordNeededError:
            print(f"Сессия {session} требует ввода пароля или кода подтверждения, пропуск.")
            failed_reports += 1

        except Exception as e:
            print(f"Ошибка при инициализации сессии {session}: {e}")
            failed_reports += 1

    return successful_reports, failed_reports

# Обработка команды /start - Убрали отправку фото
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender.id
    first_name = event.sender.first_name or "Пользователь"

    description = "Здарова."

    buttons = [
        [Button.url("📝 Руководство", "https://telegra.ph/RUKOVODSTVO-09-29-2"), Button.inline("📱 Профиль", b"profile"), Button.url("⚡ Канал", "http://t.me/+APqu-s4oNoU5Yzli")],
        [Button.inline("🆕 Spammer", b"new_snos")]
    ]
    await bot.send_message(event.chat_id, description, buttons=buttons) #Отправляем только описание и кнопки

@bot.on(events.CallbackQuery(data=b'new_snos'))
async def new_snos(event):
    user_id = event.sender.id
    if user_id in whitelist:
        await event.respond("📄 Пользователь находится в белом списке.")
        return

    await event.respond("⚡️ Отправьте ссылку на нарушения:")

@bot.on(events.CallbackQuery(data=b"profile"))
async def profile(event):
    user_id = event.sender.id
    first_name = event.sender.first_name or "Пользователь"
    username = event.sender.username if event.sender.username else "Нет"

    is_whitelisted = user_id in whitelist

    description = f"🖥 Ваш профиль\n\n👤 Имя: {first_name}\n🗄 Данные: {user_id} | @{username}\n📄 Вайтлист: {'Да' if is_whitelisted else 'Нет'}" #Убрали фото
    await bot.send_message(event.chat_id, description) #Отправляем только описание

# Обработка сообщений со ссылками для репортов
@bot.on(events.NewMessage)
async def handle_message(event):
    if event.is_private:
        user_id = event.sender.id
        if user_id in whitelist:
            message_text = event.text
            if message_text.startswith("https://t.me/"):
                successful, failed = await report_message(message_text)
                await event.respond(f"Отправлено жалоб: {successful}, неудачных: {failed}")

# Запуск бота
load_admins()
load_whitelist()
bot.start()
bot.run_until_disconnected()
