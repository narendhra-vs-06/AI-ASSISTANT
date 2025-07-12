# === JARVIS AI Assistant with LLaVA:13b, Real-Time Support, Voice, Vision ===

import os
import datetime
import pyttsx3
import speech_recognition as sr
import cv2
import subprocess
import tempfile
from PIL import Image

# === Configuration ===
OLLAMA_MODEL = "llama3.2:latest"

# === Voice Engine Setup ===
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

# === Speech Recognition Setup ===
recognizer = sr.Recognizer()
def listen():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
        except sr.RequestError:
            speak("Speech recognition service failed.")
        return ""

# === Capture Image from Camera ===
def capture_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()
    if ret:
        temp_path = tempfile.mktemp(suffix=".jpg")
        cv2.imwrite(temp_path, frame)
        return temp_path
    return None

# === Run LLaVA with Image + Text Prompt ===
def query_llava(prompt, image_path=None):
    command = ["ollama", "run", OLLAMA_MODEL]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    if image_path:
        prompt = f"<image>\n{prompt}"
    output, _ = p.communicate(prompt)
    return output

# === Real-Time Info Providers ===
def get_current_time():
    return datetime.datetime.now().strftime("%I:%M %p")

def get_current_date():
    return datetime.datetime.now().strftime("%A, %B %d, %Y")

# === Command Handler ===
def handle_command(command):
    if "time" in command:
        now = get_current_time()
        speak(f"The current time is {now}.")
    elif "date" in command:
        today = get_current_date()
        speak(f"Today is {today}.")
    elif "what do you see" in command or "analyze camera" in command:
        speak("Analyzing camera view...")
        image_path = capture_image()
        if image_path:
            response = query_llava("Describe what you see in this image.", image_path=image_path)
            speak(response)
        else:
            speak("Failed to capture image.")
    elif "open notepad" in command:
        speak("Opening Notepad")
        os.system("notepad")
    elif "exit" in command or "shutdown" in command:
        speak("Shutting down. Goodbye!")
        exit()
    else:
        speak("...")
        response = query_llava(command)
        speak(response)

# === Main Loop ===
def main():
    speak("JARVIS online. How can I help you?")
    while True:
        command = listen()
        if command:
            handle_command(command)

if __name__ == "__main__":
    main()
