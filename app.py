import whisper
import torch

model = whisper.load_model("large")

audio_file = "output.mp3"
result = model.transcribe(audio_file, language='fa')

print(result["text"])