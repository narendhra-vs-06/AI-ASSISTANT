# AI-ASSISTANT
Ai assistant 


Here's a detailed `README.md` for your GitHub repository based on the provided code and features:

---

# 🧠 JARVIS AI Assistant (English)

**A smart desktop assistant powered by Ollama's `phi3:mini` and `llava`, featuring voice interaction, GUI, image input (LLaVA), email, daily tasks, and home control.**

---

## 🌟 Features

* 🔁 Continuous speech loop with **interrupt support**
* 🗣️ Speak and respond in **English (default)** or **Tamil** with voice model switching
* 🖼️ **Image input** via LLaVA for image captioning
* 🎛️ Clean **GUI** with command buttons
* 🗓️ Date, time, jokes, music, weather stub
* 🔌 Control for apps (Notepad, Calculator, Chrome)
* ✉️ Email support (SMTP)
* 🧠 LLM-powered conversation with local models via Ollama
* 💾 SQLite-based **conversation logging**
* 🖱️ File selector for image description
* 🧪 Extensible with Home Automation or Calendar integrations

---

## 🛠 Requirements

* Python 3.10+
* Dependencies:

  ```
  pip install -r requirements.txt
  ```
* [Ollama](https://ollama.com) installed and running:

  ```bash
  ollama run phi3:mini
  ollama run llava:13b
  ```

---

## 💡 How to Use

1. **Run the script**:

   ```bash
   python jarvis_phi3_template.py
   ```

2. **Speak your commands**. Examples:

   * `"What is the time?"`
   * `"Open Notepad"`
   * `"Play music"`
   * `"Switch to Tamil"`
   * `"Describe this image"` (use GUI)
   * `"Send Email"`
   * `"Exit"` – quits the app

3. Use **GUI buttons** to control JARVIS manually.

---

## 🎛 GUI Command List

| Button            | Action                              |
| ----------------- | ----------------------------------- |
| Time / Date       | Speak current time/date             |
| Joke              | Tells a light joke                  |
| Music             | Play music via YouTube              |
| Weather           | Stub for weather (customize)        |
| Describe Image    | Image analysis via LLaVA            |
| Stop Speaking     | Interrupt voice output              |
| Export Logs       | Save log to `jarvis_export_log.txt` |
| Email             | Sends email (edit credentials)      |
| Open/Close Apps   | Notepad, Calculator, Chrome         |

---

## 📂 Logs

All conversations are saved in `jarvis_logs.db`.

Use the **Export Logs** button to export as text to `jarvis_export_log.txt`.

---

## 🧠 Model Switching

* **Default**: English via `phi3:mini`
* Use `"Switch to Tamil"` button to:

  * Change model to `llama3.2-tamil`
  * Change voice to Tamil (if available)
* Revert with `"Switch to English"`

---

## 📧 Email Setup

Edit your credentials in the `send_email()` function:

```python
server.login("your_email@gmail.com", "your_password")
server.sendmail("your_email@gmail.com", "recipient@example.com", "Message body")
```

Enable **Less secure apps** or use **App Passwords** if using Gmail.

---

## 🛠️ Coming Soon / TODO Ideas

* 🔌 Home automation via MQTT or local API
* 📅 Calendar (Google Calendar or Outlook API)
* 🧠 Memory or file-based context
* 🌍 Web search integration
* 🎙 Wake word ("Hey Jarvis")

---

## 👨‍💻 Contributing

Pull requests welcome! Make sure your features align with voice interaction and local-first approach. Open an issue for discussion first.

---

## ⚠️ Disclaimer

This project is experimental and runs local LLMs. Always test responsibly. Ensure secure handling of email credentials.

---

## 📸 Screenshot

> *(Add a screenshot of the GUI running)*

---

## 📄 License

MIT License

---

Let me know if you want a PDF/markdown copy or if you'd like it tailored for deployment (e.g., `.exe` with PyInstaller, etc.).
