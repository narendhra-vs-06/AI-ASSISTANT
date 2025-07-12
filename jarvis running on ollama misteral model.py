import os
import threading
import subprocess
import time
import speech_recognition as sr
import pyttsx3
import datetime
import queue
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import openai
import base64
import json
from tkinter import ttk, scrolledtext

# === Initialization ===
engine = pyttsx3.init()
recognizer = sr.Recognizer()
command_queue = queue.Queue()

# --- Thread-safe TTS with interrupt ---
tts_lock = threading.Lock()
tts_stop_flag = threading.Event()

def stop_speaking():
    with tts_lock:
        tts_stop_flag.set()
        try:
            engine.stop()
        except Exception:
            pass
        tts_stop_flag.clear()

def speak(text, gui_callback=None):
    def tts_job():
        with tts_lock:
            if gui_callback:
                gui_callback("JARVIS: " + text)
            engine.say(text)
            try:
                engine.runAndWait()
            except RuntimeError:
                pass
    threading.Thread(target=tts_job, daemon=True).start()

# === Set your OpenAI API Key ===
openai.api_key = "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"

# === Listen Function ===
def listen(timeout=8, phrase_time_limit=10):
    with sr.Microphone() as source:
        # recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Optional: comment out or set low
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return recognizer.recognize_google(audio)
        except (sr.UnknownValueError, sr.WaitTimeoutError, sr.RequestError):
            return ""

# === Ollama Integration ===
class OllamaManager:
    def __init__(self):
        self.process = None
        self.current_model = "mistral"
        self.available_models = ["llama3:8b", "mistral", "llava:13b"]
        self.model_descriptions = {
            "llama3": "Meta's latest model",
            "mistral": "Fast and lightweight 7B model",
            "llava:13b": "Visual reasoning model for multimodal input (image + text)"
        }

    def start_server(self):
        if not self.is_running():
            try:
                self.process = subprocess.Popen(["ollama", "serve"],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                time.sleep(2)
                return True
            except Exception as e:
                print(f"Failed to start Ollama: {e}")
                return False
        return True

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def run_query(self, prompt, model=None):
        try:
            if model is None:
                model = self.current_model
            url = "http://localhost:11434/api/generate"
            response = requests.post(url, json={"model": model, "prompt": prompt}, stream=True)
            if response.status_code == 200:
                result = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            data = json.loads(line)
                            result += data.get("response", "")
                        except Exception:
                            continue
                return result.strip()
            return "Failed to get response from model."
        except Exception as e:
            return f"Error querying Ollama: {str(e)}"

    def run_image_query(self, prompt, image_path):
        try:
            with open(image_path, "rb") as f:
                image_bytes = base64.b64encode(f.read()).decode("utf-8")
            url = "http://localhost:11434/api/generate"
            response = requests.post(url, json={
                "model": "llava",
                "prompt": prompt,
                "images": [image_bytes]
            })
            if response.status_code == 200:
                return response.json().get("response", "")
            return "Failed to get image response from model."
        except Exception as e:
            return f"Image query error: {e}"

ollama = OllamaManager()
ollama.start_server()

conversation_mode = {"enabled": False, "memory": []}

# === Memory Storage ===
def save_memory(history):
    try:
        with open("conversation_memory.json", "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        pass

# === Ask OpenAI (Online LLM) ===
def ask_openai(prompt, history=None):
    messages = [{"role": "user", "content": prompt}]
    if history:
        messages = history + messages
    try:
        res = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        return res['choices'][0]['message']['content']
    except Exception as e:
        return f"OpenAI error: {e}"

# === Handle Voice Commands ===
def handle_command(command, gui_print):
    global conversation_mode
    stop_speaking()  # Interrupt speech on any new command
    command = command.lower()

    if command.startswith("switch model to"):
        found = False
        for model in ollama.available_models:
            if model in command or model.split(":")[0] in command:
                ollama.current_model = model
                speak(f"Switched model to {model}", gui_callback=gui_print)
                found = True
                break
        if not found:
            speak("Sorry, I couldn't find that model.", gui_callback=gui_print)
        return

    elif "time" in command:
        speak("The current time is " + datetime.datetime.now().strftime("%I:%M %p"), gui_callback=gui_print)

    elif "date" in command:
        speak("Today's date is " + datetime.datetime.now().strftime("%d %B %Y"), gui_callback=gui_print)

    elif "day" in command:
        speak("Today is " + datetime.datetime.now().strftime("%A"), gui_callback=gui_print)

    elif "open calculator" in command:
        subprocess.Popen('calc.exe')
        speak("Opening calculator", gui_callback=gui_print)

    elif "open notepad" in command:
        subprocess.Popen(['notepad.exe'])
        speak("Opening Notepad", gui_callback=gui_print)

    elif "note" in command:
        speak("What would you like me to note?", gui_callback=gui_print)
        note = listen()
        if note:
            with open("notes.txt", "a") as f:
                f.write(note + "\n")
            speak("Noted.", gui_callback=gui_print)
        else:
            speak("I didn't catch that.", gui_callback=gui_print)

    elif "open google" in command:
        speak("Opening Google", gui_callback=gui_print)
        os.system("start https://www.google.com")

    elif "start ai conversation" in command:
        conversation_mode["enabled"] = True
        conversation_mode["memory"] = []
        speak("AI conversation mode started.", gui_callback=gui_print)

    elif "end conversation" in command:
        conversation_mode["enabled"] = False
        save_memory(conversation_mode["memory"])
        conversation_mode["memory"] = []
        speak("AI conversation ended.", gui_callback=gui_print)

    elif "ask online ai" in command:
        speak("What would you like to ask?", gui_callback=gui_print)
        question = listen()
        if question:
            response = ask_openai(question)
            speak(response, gui_callback=gui_print)

    elif "ask ai" in command:
        speak("What should I ask the AI?", gui_callback=gui_print)
        question = listen()
        if question:
            speak("Thinking...", gui_callback=gui_print)
            answer = ollama.run_query(question)
            speak(answer, gui_callback=gui_print)

    elif "analyze image" in command or "describe image" in command:
        speak("Please select an image file.", gui_callback=gui_print)
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            speak("What should I ask about the image?", gui_callback=gui_print)
            question = listen()
            if question:
                speak("Analyzing image...", gui_callback=gui_print)
                response = ollama.run_image_query(question, file_path)
                speak(response, gui_callback=gui_print)

    elif conversation_mode["enabled"]:
        conversation_mode["memory"].append({"role": "user", "content": command})
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_mode["memory"]])
        response = ollama.run_query(prompt)
        conversation_mode["memory"].append({"role": "assistant", "content": response})
        speak(response, gui_callback=gui_print)

    elif "exit" in command or "stop" in command:
        speak("Shutting down. Goodbye!", gui_callback=gui_print)
        save_memory(conversation_mode["memory"])
        os._exit(0)

    else:
        speak("Sorry, I didn't understand that.", gui_callback=gui_print)

def command_worker(gui_print):
    while True:
        cmd = command_queue.get()
        if cmd:
            gui_print("You: " + cmd)
            handle_command(cmd, gui_print)
        command_queue.task_done()

def start_gui():
    root = tk.Tk()
    root.title("JARVIS Assistant")
    root.geometry("500x500")
    root.configure(bg="#ffffff")

    chat_box = scrolledtext.ScrolledText(
        root,
        font=("Consolas", 12),
        bg="#ffffff",
        fg="#000000",
        state="disabled",
        wrap=tk.WORD
    )
    chat_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def gui_print(msg):
        chat_box.config(state="normal")
        chat_box.insert(tk.END, msg + "\n")
        chat_box.see(tk.END)
        chat_box.config(state="disabled")

    model_var = tk.StringVar(value=ollama.current_model)
    model_label = tk.Label(root, text="Model:", bg="#ffffff", fg="#000000")
    model_label.pack()
    model_dropdown = ttk.Combobox(root, textvariable=model_var, values=ollama.available_models, state="readonly")
    model_dropdown.pack(pady=5)

    def switch_model(event=None):
        selected = model_var.get()
        ollama.current_model = selected
        gui_print(f"Switched to model: {selected}")

    model_dropdown.bind("<<ComboboxSelected>>", switch_model)

    input_frame = tk.Frame(root, bg="#ffffff")
    input_frame.pack(fill=tk.X, padx=10, pady=5)
    user_entry = tk.Entry(input_frame, font=("Arial", 12), bg="#ffffff", fg="#000000")
    user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    def on_send():
        user_text = user_entry.get().strip()
        if user_text:
            stop_speaking()  # Interrupt JARVIS if speaking
            gui_print("You: " + user_text)
            user_entry.delete(0, tk.END)
            command_queue.put(user_text)

    send_btn = tk.Button(
        input_frame,
        text="Send",
        command=on_send,
        bg="#e0e0e0",
        fg="#000000",
        font=("Arial", 12)
    )
    send_btn.pack(side=tk.LEFT)

    def on_voice():
        stop_speaking()  # Interrupt JARVIS if speaking
        gui_print("Listening...")
        cmd = listen()
        if cmd:
            gui_print("You: " + cmd)
            command_queue.put(cmd)
        else:
            gui_print("Didn't catch that.")

    voice_btn = tk.Button(
        root,
        text="🎤 Speak",
        command=on_voice,
        bg="#e0e0e0",
        fg="#000000",
        font=("Arial", 12)
    )
    voice_btn.pack(pady=5)

    threading.Thread(target=command_worker, args=(gui_print,), daemon=True).start()
    # Start always-on listener in the background, using the same gui_print
    threading.Thread(target=listener_loop, args=(lambda msg: None,), daemon=True).start()
    root.mainloop()

def listener_loop(gui_print):
    while True:
        cmd = listen()
        if cmd:
            gui_print("You: " + cmd)
            command_queue.put(cmd)

def main():
    speak("JARVIS online. How can I assist you today?")
    start_gui()

if __name__ == '__main__':
    main()