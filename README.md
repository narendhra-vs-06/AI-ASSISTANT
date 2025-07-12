---
````markdown
# 🧠 JARVIS Desktop AI Assistant (English Only)

A smart desktop assistant using `phi3:mini` for natural language responses and an intuitive GUI with voice control, app management, email, and image-based interaction using LLaVA.

---

## 🚀 Features

- 🔁 Continuous speech interaction (looped listening + speaking)
- 🗣️ Voice input with interruption support
- 🖥️ GUI with action buttons
- 🧠 Responses from **phi3:mini** (Ollama LLM)
- 🖼️ Image analysis using **LLaVA** (optional)
- 📁 Log conversations to SQLite + export as `.txt`
- 🎶 Music playback (YouTube)
- 📅 Date, time, jokes, and weather stubs
- 📤 Email support (SMTP)
- 📂 Open/close apps (Notepad, Calculator, Chrome)

---

## 📦 Requirements

- Python 3.10+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
````

* Install and run [Ollama](https://ollama.com):

  ```bash
  ollama run phi3:mini
  ollama run llava:13b
  ```

---

## 🎮 GUI Shortcuts

| Button          | Description                        |
| --------------- | ---------------------------------- |
| Time / Date     | Speaks current time or date        |
| Joke            | Light humor from built-in list     |
| Music           | Plays relaxing music from YouTube  |
| Weather         | Placeholder, customizable API call |
| Export Logs     | Saves all logs to a text file      |
| Send Email      | Sends basic email (SMTP login)     |
| Open Notepad    | Launches Windows Notepad           |
| Open Calculator | Launches Calculator                |
| Open Chrome     | Launches Google Chrome             |
| Close Notepad   | Force closes Notepad               |
| Close Chrome    | Force closes Chrome                |
| Stop Speaking   | Immediately stops TTS output       |

---

## 🖼️ Image Interaction (via LLaVA)

Click `"Describe Image"` in GUI (if added) to upload an image and get a caption.

Run LLaVA:

```bash
ollama run llava:13b
```

---

## ✉️ Email Setup

Edit credentials in the `send_email()` function:

```python
server.login("your_email@gmail.com", "your_password")
server.sendmail("your_email@gmail.com", "to_email@example.com", "Test email from JARVIS.")
```

For Gmail, use an **App Password** instead of the actual password.

---

## 💾 Log Export

All interactions are stored in `jarvis_logs.db`.
Use the GUI to export to `jarvis_export_log.txt`.

---

## 🔚 Exit Voice Command

Say:

```
exit
```

or

```
quit
```

To shut down the assistant and close the GUI.

---

## 📸 Screenshot (Optional)

*(Insert a screenshot here of the GUI if you want)*

---

## 📃 License

MIT License

---

## 📌 To Do / Ideas

* 🌐 Integrate weather/news APIs
* 🗓️ Add calendar/task management
* 🔌 Home automation (MQTT/HTTP)
* 🎤 Add wake-word trigger
* 🎙️ Streaming ASR for real-time feedback

---

```

Let me know if you'd like this `README.md` converted to a downloadable file or auto-generated in your code directory.
```
