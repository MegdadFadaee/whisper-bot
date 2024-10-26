import os, io
import inspect
import whisper
import requests
from colorama import Style
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
if not os.path.isdir('temp'):
    os.mkdir('temp')

TOKEN = os.getenv('BOT_TOKEN')
BASE_URL = f"https://tapi.bale.ai"
API_URL = f"{BASE_URL}/bot{TOKEN}"
DOWNLOAD_URL = f"{BASE_URL}/file/bot{TOKEN}"

whisper_model = whisper.load_model("large")


class Messages:
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
    audio_data = requests.get(download_url).content
    return audio_data


def transcribe_audio(audio_data, file_id, format="ogg"):
    file_name = f"temp/{file_id}.{format}".replace(':', '[]')
    audio = AudioSegment.from_file(io.BytesIO(audio_data), format=format)
    audio.export(file_name, format="wav")
    result = whisper_model.transcribe(file_name)
    # os.remove(file_name)
    return result['text']


def handle_voice_message(chat_id, message_id, file_id):
    send_message(chat_id, Messages.file_received, reply_to_message_id=message_id)

    audio_data = download_file(file_id)
    transcript = transcribe_audio(audio_data, file_id, format="ogg")

    send_message(chat_id, f"{Messages.transcription_result}{transcript}", reply_to_message_id=message_id)


def handle_document_message(chat_id, message_id, document):
    mime_type = document.get("mime_type", "")

    if mime_type == "audio/mpeg":
        file_id = document["file_id"]

        send_message(chat_id, Messages.file_received, reply_to_message_id=message_id)

        audio_data = download_file(file_id)
        transcript = transcribe_audio(audio_data, file_id, format="mp3")

        send_message(chat_id, f"{Messages.transcription_result}{transcript}", reply_to_message_id=message_id)
    else:
        send_message(chat_id, Messages.invalid_file_type, reply_to_message_id=message_id)


def process_update(update):
    message = update.get("message")

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
    client = get_me()
    print(inspect.cleandoc(f"""
        Logged in as {client['username']} (ID: {client['id']})
    """), end="\n\n")


def log_message(message):
    print(f"> {Style.BRIGHT}{message['from']['username']} (ID: {message['from']['id']}) {Style.RESET_ALL} send message.")


def get_resulted_updates() -> list:
    result = get_updates().get('result')
    return list(map(lambda x: x.get('update_id'), result))

def main():
    log_ready()
    resulted_updates = get_resulted_updates()
    while True:
        updates = get_updates()
        for update in updates.get("result", []):
            update_id = update.get("update_id")
            if update_id not in resulted_updates:
                resulted_updates.append(update_id)

                message = update.get("message")

                if message.get("text") == '/pull':
                    os.system('git reset --hard')
                    os.system('git pull')

                log_message(message)
                process_update(update)


if __name__ == "__main__":
    main()
