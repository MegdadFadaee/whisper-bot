import os, io
import sys
import asyncio
import inspect
import whisper
import requests
from colorama import Style
from pydub import AudioSegment
from dotenv import load_dotenv
from mimetypes import guess_extension

load_dotenv()
if not os.path.isdir('temp'):
    os.mkdir('temp')

TOKEN = os.getenv('BOT_TOKEN')
BASE_URL = f"https://tapi.bale.ai"
API_URL = f"{BASE_URL}/bot{TOKEN}"
DOWNLOAD_URL = f"{BASE_URL}/file/bot{TOKEN}"

whisper_model = whisper.load_model("large")


class Messages:
    hello = "👋 سلام"
    help = "یک نجوا کافی است."
    file_received = "✅ فایل با موفقیت دریافت شد، در حال پردازش..."
    transcription_result = "متن استخراج‌شده:\n"
    invalid_file_type = "فایل ارسالی باید به صورت صوتی (MP3 یا OGG) باشد."
    request_audio = "لطفاً یک فایل صوتی (Voice یا MP3) ارسال کنید."


def get_me():
    url = f"{API_URL}/getMe"
    response = requests.get(url)
    return response.json().get('result')


def get_updates() -> dict:
    url = f"{API_URL}/getUpdates"
    response = requests.get(url)
    return response.json()


def send_message(chat_id, text, reply_to_message_id=None):
    url = f"{API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_message_id}
    return requests.post(url, json=data).json()


def download_file(file_id):
    file_url = f"{API_URL}/getFile?file_id={file_id}"
    file_info = requests.get(file_url).json()
    file_path = file_info['result']['file_path']
    download_url = f"{DOWNLOAD_URL}/{file_path}"
    return requests.get(download_url).content


def save_file(file_id, mime_type):
    content = download_file(file_id)
    ext = guess_extension(mime_type)
    file_name = f"temp/{file_id}{ext}".replace(':', '[]')
    with open(file_name, 'wb') as f:
        f.write(content)
    return file_name


def transcribe_audio(audio_data, file_id, ext="ogg"):
    file_name = f"temp/{file_id}.{ext}".replace(':', '[]')
    audio = AudioSegment.from_file(io.BytesIO(audio_data), format=ext)
    audio.export(file_name, format="wav")
    result = whisper_model.transcribe(file_name)
    # os.remove(file_name)
    return result['text']


def handle_voice_message(chat_id, message_id, file_id):
    send_message(chat_id, Messages.file_received, reply_to_message_id=message_id)

    audio_data = download_file(file_id)
    transcript = transcribe_audio(audio_data, file_id, ext="ogg")

    send_message(chat_id, f"{Messages.transcription_result}{transcript}", reply_to_message_id=message_id)


def handle_document_message(chat_id, message_id, document):
    mime_type = document.get("mime_type", "")

    if "audio/" in mime_type:
        file_id = document["file_id"]
        mime_type = document["mime_type"]
        if mime_type == "audio/mp3":
            ext = 'mp3'
        else:
            ext = guess_extension(mime_type).removeprefix('.')

        send_message(chat_id, Messages.file_received, reply_to_message_id=message_id)

        audio_data = download_file(file_id)
        transcript = transcribe_audio(audio_data, file_id, ext=ext)

        send_message(chat_id, f"{Messages.transcription_result}{transcript}", reply_to_message_id=message_id)
    else:
        send_message(chat_id, Messages.invalid_file_type, reply_to_message_id=message_id)


def process_update(message):
    if message:
        chat_id = message["chat"]["id"]
        message_id = message["message_id"]

        if "voice" in message:
            handle_voice_message(chat_id, message_id, message["voice"]["file_id"])
        elif "document" in message:
            handle_document_message(chat_id, message_id, message["document"])
        else:
            send_message(chat_id, Messages.request_audio)


def log_ready():
    os.system('clear' or 'cls')
    client = get_me()
    print(inspect.cleandoc(f"""
        Logged in as {client['username']} (ID: {client['id']})
    """), end="\n\n")


def log_message(message):
    print(
        f"> {Style.BRIGHT}{message['from']['username']} (ID: {message['from']['id']}) {Style.RESET_ALL} send message.")


def get_resulted_updates() -> list:
    result = get_updates().get('result')
    return list(map(lambda x: x.get('update_id'), result))


def say_hello(message):
    chat_id = message["chat"]["id"]
    user = message.get("from")

    return send_message(chat_id, f"{Messages.hello} {user.get('first_name')} {user.get('last_name')}")


def send_help(message):
    chat_id = message["chat"]["id"]
    user = message.get("from")

    return send_message(chat_id, f"{Messages.help}")


def pull_repository():
    os.system('git pull')
    script_name = f'"{sys.argv[0]}"'
    os.execv(sys.executable, ['python3'] + [script_name] + sys.argv[1:])


def pong(message):
    chat_id = message["chat"]["id"]
    return send_message(chat_id, "pong")


async def main():
    log_ready()
    resulted_updates = get_resulted_updates()
    while True:
        updates = get_updates()
        for update in updates.get("result", []):
            update_id = update.get("update_id")
            if update_id not in resulted_updates:
                resulted_updates.append(update_id)

                message = update.get("message")
                log_message(message)

                match message.get("text", '').lower():
                    case '/start':
                        say_hello(message)
                    case '/hi':
                        say_hello(message)
                    case '/hello':
                        say_hello(message)
                    case '/help':
                        send_help(message)
                    case '/pull':
                        pull_repository()
                    case 'ping':
                        pong(message)
                    case _:
                        process_update(message)


if __name__ == "__main__":
    me = get_me()
    asyncio.run(main())
