from fastapi import FastAPI, UploadFile, File
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqGeneration
import torch
from PIL import Image
import io
import gtts
from pathlib import Path
import os
import base64

app = FastAPI()

# Initialize models
HF_TOKEN = "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"

# Plant disease classifier
classifier = pipeline("image-classification", 
                     model="deep-plants/AGM_HS",
                     token=HF_TOKEN)

# Translation model
tokenizer = AutoTokenizer.from_pretrained("abdulwaheed1/english-to-urdu-translation-mbart")
translation_model = AutoModelForSeq2SeqTranslation.from_pretrained("abdulwaheed1/english-to-urdu-translation-mbart")

@app.post("/classify")
async def classify_plant(file: UploadFile = File(...)):
    # Read and process image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Classify image
    result = classifier(image)
    
    # Translate to Urdu
    inputs = tokenizer(result[0]["label"], return_tensors="pt")
    translated = translation_model.generate(**inputs)
    urdu_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    
    # Generate audio
    tts = gtts.gTTS(text=urdu_text, lang='ur')
    audio_path = "temp_audio.mp3"
    tts.save(audio_path)
    
    # Read audio file and convert to base64
    with open(audio_path, "rb") as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode()
    
    # Clean up
    os.remove(audio_path)
    
    return {
        "english_classification": result[0]["label"],
        "confidence": float(result[0]["score"]),
        "urdu_translation": urdu_text,
        "audio_base64": audio_base64
    }