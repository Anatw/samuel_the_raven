import queue
import sounddevice as sd  # capture live audio from the microphone
import vosk
import sys
import json
import re
import os
from rapidfuzz import fuzz

from private_words_behavior import NAME_CORRECTIONS_REGEX
from animatron_audio_devices import get_audio_device_indices


MODEL_PATH = "models/vosk-model-small-en-us-0.15"
FUZZY_MATCHES = "speech_variants.json"
# The index of the microphone device to use. You can find the index by running:  arecord -l
MIC_INDEX = get_audio_device_indices()["mic_index"]


class SpeechRecognition:
    def __init__(self, model_path=MODEL_PATH, sample_rate=16000, threshold=85):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.q = queue.Queue()  # Autio stream setup
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")
        self.model = vosk.Model(model_path)

        with open(file=FUZZY_MATCHES, mode="r", encoding="utf-8") as f:
            self.trained_variants = json.load(f)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        self.q.put(bytes(indata))

    def match_targets_with_regex(self, text):
        found = set()
        for pattern, label in NAME_CORRECTIONS_REGEX.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)
        return found

    def match_from_trained_variants(self, text):
        text = text.lower()
        words = text.split()
        found = {}

        for target, phrases in self.trained_variants.items():
            for phrase in phrases:
                phrase = phrase.lower().strip()
                if not phrase:
                    continue
                for n in range(1, 4):
                    for i in range(len(words) - n + 1):
                        chunk = " ".join(words[i : i + n])
                        score = fuzz.ratio(chunk, phrase)
                        if score >= self.threshold:
                            if target not in found or found[target]["score"] < score:
                                found[target] = {
                                    "score": score,
                                    "match": chunk,
                                    "variant": phrase,
                                }
        return found

    def recognize_words_from_microphone(self):
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            device=MIC_INDEX,
            callback=self.audio_callback,
        ):
            recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            print("Hello! I'm listening")

            while True:
                data = self.q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    raw_text = result.get("text", "").strip()

                    if not raw_text:
                        continue

                    print(f"\n📝 Recognized: '{raw_text}'")

                    regex_matches = self.match_targets_with_regex(text=raw_text)
                    fuzzy_matches = self.match_from_trained_variants(text=raw_text)

                    matched_words = sorted(
                        set(regex_matches) | set(fuzzy_matches.keys())
                    )

                    if matched_words:
                        print(f"✅ Matched: {matched_words}")
                        for word, details in fuzzy_matches.items():
                            print(
                                f"   • Fuzzy: '{details['match']}' ≈ '{details['variant']}' → '{word}' (score: {details['score']})"
                            )
