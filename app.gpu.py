import whisper
import torch


device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("large").to(device)

audio_file = "output.mp3"
result = model.transcribe(audio_file, device=device, language='fa')
text_without_diacritics = result["text"]


print(result["text"])

str.join(' ', ['qwe', 'asd', 'zxc'])
