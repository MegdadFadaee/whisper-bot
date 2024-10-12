FROM pytorch/pytorch:2.0.1-cpu

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

RUN python -c "\
    import whisper; \
    whisper.load_model('tiny'); \
    whisper.load_model('base'); \
    whisper.load_model('small'); \
    whisper.load_model('medium'); \
    whisper.load_model('large')"

WORKDIR /app

COPY . /app

CMD ["python", "app.py"]
