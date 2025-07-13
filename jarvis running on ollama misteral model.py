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
import sqlite3
import random
import webbrowser
from datetime import timedelta
from tkinter.font import Font

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
openai.api_key = "type your api key"

OPENWEATHER_API_KEY = "af447c4cc560efe8876a3498a8e1ef6f"
NEWSAPI_KEY = "pub_45f1a8d540bb4ebd936de5020e5014f0"

# === Listen Function ===
def listen(timeout=8, phrase_time_limit=10):
    with sr.Microphone() as source:
        # recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Optional: comment out or set low
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return recognizer.recognize_google(audio)
        except (sr.UnknownValueError, sr.WaitTimeoutError, sr.RequestError):
            return ""

# --- DB Setup ---
conn = sqlite3.connect("jarvis_logs.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS conversations (
    timestamp TEXT,
    role TEXT,
    message TEXT
)''')
conn.commit()

def db_log(role, msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO conversations VALUES (?, ?, ?)", (timestamp, role, msg))
    conn.commit()

def export_logs():
    with open("jarvis_export_log.txt", "w", encoding="utf-8") as f:
        for row in cursor.execute("SELECT * FROM conversations"):
            f.write(f"{row[0]} - {row[1]}: {row[2]}\n")

def get_weather(city="karur"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url).json()
        if response.get("cod") != 200:
            return f"Sorry, I couldn't find weather info for {city}."
        desc = response['weather'][0]['description']
        temp = response['main']['temp']
        humidity = response['main']['humidity']
        weather_report = f"The weather in {city} is {desc} with temperature {temp} degree Celsius and humidity {humidity} percent."
        return weather_report
    except Exception as e:
        return f"Failed to get weather: {e}"

def get_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWSAPI_KEY}"
        response = requests.get(url).json()
        if response.get("status") != "ok":
            return "Sorry, I can't get the news right now."
        articles = response.get("articles", [])[:3]
        news_report = "Here are the top news headlines: "
        for i, article in enumerate(articles, 1):
            news_report += f"{i}. {article['title']}. "
        return news_report
    except Exception as e:
        return f"Failed to get news: {e}"

def open_app(name):
    apps = {
        "spotify": r"C:\Users\LOQ\AppData\Roaming\Spotify\Spotify.exe",
        "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "games folder": r"D:\games",
        "gta5": r"D:\games\Grand Theft Auto V",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
    }
    path = apps.get(name)
    if path:
        subprocess.Popen(path)
        speak(f"Opening {name}")
    else:
        speak(f"Sorry, I don't know how to open {name}.")

def close_app(name):
    processes = {
        "spotify": "Spotify.exe",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "chrome": "chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "Calculator.exe",
    }
    proc = processes.get(name)
    if proc:
        os.system(f"taskkill /f /im {proc}")
        speak(f"Closed {name}")
    else:
        speak(f"Sorry, I don't know how to close {name}.")

def describe_image(file_path, gui_callback):
    try:
        with open(file_path, 'rb') as f:
            img_bytes = base64.b64encode(f.read()).decode("utf-8")
        url = "http://localhost:11434/api/generate"
        response = requests.post(url, json={
            "model": "llava:13b",
            "prompt": "Describe this image.",
            "images": [img_bytes]
        })
        if response.status_code == 200:
            result = response.json().get("response", "")
            speak(result, gui_callback=gui_callback)
        else:
            speak("Failed to process image.", gui_callback=gui_callback)
    except Exception:
        speak("Failed to process image.", gui_callback=gui_callback)

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

# === System Information Functions ===
def get_battery_status():
    try:
        # For Windows
        output = subprocess.check_output("wmic path win32_battery get estimatedchargeremaining", shell=True)
        charge = int(output.decode().strip().split("\n")[-1])
        return f"Battery charge is at {charge}%."
    except:
        return "Battery status not available."

def get_system_specs():
    try:
        # Using WMIC to get system specifications
        specs = subprocess.check_output("wmic cpu get caption, deviceid, name, numberofcores, maxclockspeed", shell=True)
        return "System Specs: " + specs.decode()
    except:
        return "Failed to get system specs."

def get_temperatures():
    try:
        # Using wmi module to get temperature (works on Windows)
        import wmi
        w = wmi.WMI(namespace="root\wmi")
        temperature_info = w.MSAcpi_ThermalZone()
        temperatures = [temp.CurrentTemperature for temp in temperature_info]
        # Convert from tenths of Kelvin to Celsius
        temperatures_celsius = [round((temp / 10) - 273.15, 2) for temp in temperatures]
        return "Temperatures: " + ", ".join([f"{temp}°C" for temp in temperatures_celsius])
    except:
        return "Failed to get temperatures."

def get_ram_usage():
    try:
        # Using psutil to get RAM usage
        import psutil
        ram = psutil.virtual_memory()
        return f"RAM Usage: {ram.percent}%"
    except:
        return "Failed to get RAM usage."

def get_disk_usage():
    try:
        # Using psutil to get Disk usage
        import psutil
        disk = psutil.disk_usage('/')
        return f"Disk Usage: {disk.percent}%"
    except:
        return "Failed to get Disk usage."

def get_uptime():
    try:
        # Using uptime command
        output = subprocess.check_output("uptime -p", shell=True)
        return "Uptime: " + output.decode().strip()
    except:
        return "Failed to get uptime."

def get_ip_address():
    try:
        # Using requests to get public IP
        response = requests.get("https://api.ipify.org")
        return "Public IP Address: " + response.text
    except:
        return "Failed to get IP address."

def check_internet():
    try:
        # Using requests to check internet connectivity
        requests.get("https://www.google.com", timeout=5)
        return "Internet is connected."
    except:
        return "No internet connection."

# --- Note and To-Do Functions ---
def save_note(note):
    try:
        with open("notes.txt", "a") as f:
            f.write(note + "\n")
    except Exception as e:
        return f"Error saving note: {e}"

def get_notes():
    try:
        with open("notes.txt", "r") as f:
            notes = f.readlines()
        return "Notes: " + "".join(notes)
    except Exception as e:
        return f"Error retrieving notes: {e}"

def add_todo(task):
    try:
        with open("todo.txt", "a") as f:
            f.write(task + "\n")
    except Exception as e:
        return f"Error adding task: {e}"

def get_todo():
    try:
        with open("todo.txt", "r") as f:
            tasks = f.readlines()
        return "To-Do List: " + "".join(tasks)
    except Exception as e:
        return f"Error retrieving tasks: {e}"

def set_reminder(task, minutes):
    try:
        time.sleep(minutes * 60)
        speak(f"Reminder: {task}")
        return f"Reminder set for {task} in {minutes} minutes."
    except Exception as e:
        return f"Error setting reminder: {e}"

# === Handle Voice Commands ===
def handle_command(command, gui_print):
    global conversation_mode
    stop_speaking()  # Interrupt speech on any new command
    command = command.lower()
    db_log("User", command)

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
    elif "battery" in command:
        speak(get_battery_status(), gui_print)
    elif "specs" in command:
        speak(get_system_specs(), gui_print)
    elif "temperature" in command:
        speak(get_temperatures(), gui_print)
    elif "ram" in command:
        speak(get_ram_usage(), gui_print)
    elif "disk" in command:
        speak(get_disk_usage(), gui_print)
    elif "uptime" in command:
        speak(get_uptime(), gui_print)
    elif "ip" in command:
        speak(get_ip_address(), gui_print)
    elif "internet" in command:
        speak(check_internet(), gui_print)
    elif "note" in command:
        note = command.replace("take a note", "").strip()
        save_note(note)
        speak("Note saved", gui_print)
    elif "show notes" in command:
        speak(get_notes(), gui_print)
    elif "to-do" in command:
        task = command.replace("add", "").replace("to-do list", "").strip()
        add_todo(task)
        speak("Task added", gui_print)
    elif "show tasks" in command:
        speak(get_todo(), gui_print)
    elif "remind me" in command:
        parts = command.split(" in ")
        task = parts[0].replace("remind me to", "").strip()
        minutes = int(parts[1].replace("minutes", "").strip())
        speak(set_reminder(task, minutes), gui_print)
    elif "open" in command:
        speak(open_site(command), gui_print)
    elif "search" in command:
        query = command.replace("search", "").strip()
        speak(search_web(query), gui_print)
    elif "download" in command:
        url = command.replace("download file from", "").strip()
        speak(download_file(url), gui_print)
    elif "play music" in command:
        speak(play_music(), gui_print)
    elif "joke" in command:
        speak(tell_joke(), gui_print)
    elif "quote" in command:
        speak(get_quote(), gui_print)
    elif "time" in command:
        speak(datetime.datetime.now().strftime("%I:%M %p"), gui_print)
    elif "date" in command:
        speak(datetime.datetime.now().strftime("%A, %d %B %Y"), gui_print)
    elif "exit" in command:
        speak("Shutting down.", gui_print)
        os._exit(0)
    elif "time" in command:
        speak("The current time is " + datetime.datetime.now().strftime("%I:%M %p"), gui_callback=gui_print)
        return

    elif "date" in command:
        speak("Today's date is " + datetime.datetime.now().strftime("%d %B %Y"), gui_callback=gui_print)
        return

    elif "day" in command:
        speak("Today is " + datetime.datetime.now().strftime("%A"), gui_callback=gui_print)
        return

    elif "weather" in command:
        city = "karur"
        if "in" in command:
            city = command.split("in")[-1].strip()
        weather_report = get_weather(city)
        speak(weather_report, gui_callback=gui_print)
        return

    elif "news" in command:
        news = get_news()
        speak(news, gui_callback=gui_print)
        return

    elif "open" in command:
        for app in ["spotify", "word", "excel", "chrome", "notepad", "calculator","games folder", "gta5"]:
            if app in command:
                open_app(app)
                break
        else:
            speak("Please specify a known app to open.", gui_callback=gui_print)
        return

    elif "close" in command:
        for app in ["spotify", "word", "excel", "chrome", "notepad", "calculator","games folder", "gta5"]:
            if app in command:
                close_app(app)
                break
        else:
            speak("Please specify a known app to close.", gui_callback=gui_print)
        return

    elif "export logs" in command:
        export_logs()
        speak("Logs have been exported to jarvis_export_log.txt", gui_callback=gui_print)
        return

    elif "joke" in command:
        joke = random.choice([
            "Why did the computer go to therapy? Because it had too many bytes!",
            "I'm not lazy, I'm on energy-saving mode."
        ])
        speak(joke, gui_callback=gui_print)
        return

    elif "describe image" in command or "analyze image" in command:
        speak("Please select an image file.", gui_callback=gui_print)
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            describe_image(file_path, gui_callback)
        else:
            speak("No image selected.", gui_callback=gui_print)
        return

    elif conversation_mode["enabled"]:
        conversation_mode["memory"].append({"role": "user", "content": command})
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_mode["memory"]])
        response = ollama.run_query(prompt)
        conversation_mode["memory"].append({"role": "assistant", "content": response})
        speak(response, gui_callback=gui_print)
        return

    elif "exit" in command or "stop" in command:
        speak("Shutting down. Goodbye!", gui_callback=gui_print)
        save_memory(conversation_mode["memory"])
        os._exit(0)
        return

    # --- NEW: Send unknown commands to AI model ---
    else:
        # Use Ollama by default, fallback to OpenAI if needed
        response = ollama.run_query(command)
        if not response or "Failed" in response or "Error" in response:
            response = ask_openai(command)
        speak(response, gui_callback=gui_print)

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
        user_text = user_entry.get().strip()  # <-- add indentation here
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
        cmd = listen()  # <-- add indentation here
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
