<br/>
<div align="center">
  <a href="https://github.com/Jokoril/COCK-profanity-processor">
    <img src="https://files.catbox.moe/7kgdti.png" alt="Logo" width="551" height="149">
  </a>

<h3 align="center">A profanity processor for oppressed gamers</h3>

<div align="center">

<br/>

![Platform](https://img.shields.io/badge/Windows-0078D4?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1MTIiIGhlaWdodD0iNTEyIiB2aWV3Qm94PSIwIDAgNTEyIDUxMiI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTQ4MCwyNjVIMjMyVjQ0NGwyNDgsMzZWMjY1WiIvPjxwYXRoIGZpbGw9IiNmZmYiIGQ9Ik0yMTYsMjY1SDMyVjQxNWwxODQsMjYuN1YyNjVaIi8+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTQ4MCwzMiwyMzIsNjcuNFYyNDlINDgwVjMyWiIvPjxwYXRoIGZpbGw9IiNmZmYiIGQ9Ik0yMTYsNjkuNywzMiw5NlYyNDlIMjE2VjY5LjdaIi8+PC9zdmc+&logoColor=white)
[![Python](https://img.shields.io/badge/python%203.13-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/downloads/release/python-3130/)
[![Claude](https://img.shields.io/badge/Claude-D97757?style=for-the-badge&logo=claude&logoColor=white)](https://claude.ai/)
[![Ko-Fi](https://img.shields.io/badge/Buy_me_a_coffee-FFB24D?logo=ko-fi&style=for-the-badge)](Link_to_ko-fi)
[![License](https://img.shields.io/badge/license-GPLv3-purple.svg?style=for-the-badge)](https://github.com/Jokoril/COCK-profanity-processor/blob/main/LICENSE)



</div>
</div>

# 🐔 About COCK

Ever tried to say **"Assassin"** in game chat and got censored? What about **"Basement"**? Or **"Analyze"**?
Or other regular phrases that get rejected because the game you're playing has a profanity filter that's just [too f🤬king sensitive?](https://en.wikipedia.org/wiki/Scunthorpe_problem)

Suffer no more, with the power of 🐔!

COCK is a lightweight desktop tool that intercepts your messages before you send them, detects words that might be filtered, and applies creative text transformations so that your message "complies" with the in game censorship system.

### Before COCK 🚫

```
Chat Input:       "Assassin, Analyze, Basement"

Detection:        "Ass, "Anal, "semen"

Game Output:      "******in, ****yze, Ba*****t"
```

### After COCK ✅

```
Chat Input:       "Assassin, Analyze, Basement"

Optimization:     "🄰ss, "4nal, "s3men"

Game Output:      "🄰ss🄰ssin, 4nalyze, Bas3ment"
```

---

# ✨ Features

### 🔍 Smart Detection

- **Fast Aho-Corasick algorithm** - Can process 50,000+ entries in miliseconds
- **Whitelist system** - Whitelist words that get censored standalone but are ignored when embedded
- **Sliding window detection** - Catches and processes filtered terms that occur across adjacent words, spaces and punctuations
- **Extended Latin Recognition** - Supports any language that use the Latin script
  <img src="https://hatscripts.github.io/circle-flags/flags/gb.svg" height="16" alt="UK">
  <img src="https://hatscripts.github.io/circle-flags/flags/de.svg" height="16" alt="Germany">
  <img src="https://hatscripts.github.io/circle-flags/flags/es.svg" height="16" alt="Spain">
  <img src="https://hatscripts.github.io/circle-flags/flags/vn.svg" height="16" alt="Vietnam">
  <img src="https://hatscripts.github.io/circle-flags/flags/br.svg" height="16" alt="Brazil"> ... and more

### 🍌🥒🦴 TRIPLE PENETRATION™ Profanity Processing Method

1. **Leet-Speak** : `Leet Speak` → `L33t $p34k`
2. **Fancy Text** : `So Fancy!` → `𝓢𝓸 𝓕𝓪𝓷𝓬𝔂!` (8 different styles)
3. **Special Character Interspacing** → Insert symbols that are invisible in game to break patterns

### 🎯 Message Size Limit Optimizations

- **Configurable Limits** - Set custom limits for byte size `default:92` and character length `default: 80`
- **Shorthanding Length Reduction** - `you are someone good` → `u r some1 gud`
- **Message Splitter** - Splits your messages based on set limits so you can send them in parts

### ⚙️ Two Modes


|            **Manual Mode**            |          **Auto Mode**          |
| :-------------------------------------: | :--------------------------------: |
| Review detected issues before sending | Instant optimization and sending |
|  Choose from suggested optimizations  |        Seamless workflow        |
|    Full control over your messages    |  Perfect for fast-paced gaming  |

### 🛡️ Safe for Online Games

- ❌ No game memory access
- ❌ No code injection
- ❌ No process hooking
- ✅ Completely local, offline operation
- ✅ **Acts like your clipboard and keyboard**
- ✅ Compatible with all anti-cheat systems (EasyAntiCheat, BattlEye, Vanguard)


### 🎛️ Customization

- **Custom Hotkeys** 
- **Enable/Disable Processing Techniques**
- **Filter List Manager**
- **Whitelist Manager**
- **Dark/Light themes**

---

# 📥 Installation

### Option 1: Download Portable .exe (Easiest)

1. Go to [Releases](https://github.com/Jokoril/COCK-profanity-processor/releases)
2. Download `CompliantOnlineChatKit.exe`
3. Run it - **no installation needed!**
4. Configure your filter file in Settings

### Option 2: Run from Source (Developers)

**Requirements:**

- Python 3.8+
- Windows 10/11

**Setup:**

```bash
# Clone repository
git clone https://github.com/Jokoril/COCK-profanity-processor.git
cd COCK-profanity-processor

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

**Build your own .exe:**

```bash
pyinstaller build.spec
# Output: dist/CompliantOnlineChatKit.exe
```
---

# 🚀 Quick Start

### 🌱 First Launch

1. **Run the application as Admin** 
   - If your game does not require elevated permissions, you can run it normally
2. **Settings window opens automatically**
3. **Configure filter file:**
   - Settings → General → Filter File → Browse
   - COCK comes pre-loaded with a filter list commonly used in Tencent games
   - Select your filter list (one word per line, plain .txt)
4. **Set hotkey** (default: F12)
5. **Click Save**

### 🛠️ Basic Usage

1. **Type your message** in any application (game chat, Discord, etc.)
2. **Press F12** (or your custom hotkey)
3. **Review suggestions** (Manual mode) or message auto-optimizes (Auto mode)
4. **Click "Use Suggestion"** or press Enter to send

**That's it!** Your optimized message is ready to send.

### ♻️ Example Workflow

```
1. Type: "I'm a specialist assassin from Scunthorpe"
2. Press: F12
3. See:  Detected words: "specialist", "assassin", "Scunthorpe"
4. Get:  "I'm a 🅂pecialist 🄰ss🄰ssin from 🅂cuthorpe"
5. Send: ✓ Message delivered!
```
---

# 🚧 Limitations
### 🔡 No non-Latin support
COCK does not support languages that use non-Latin characters, such as CJK, Thai, Cyrillic,, etc.

### ⌨️ Needs Keyboard Shortcut Recognition
COCK will only work on games that detect and support keyboard shortcuts in the chat box:
- Select All Text `Ctrl + A`
- Copy Text `Ctrl + C`
- Paste Text `Ctrl + V`
- Send `Enter`

### 👻 Some Censorship Systems Are Haunted
You may still run into cases where games randomly censor parts of your message that do not trigger any actual filter hits.

In such cases, use **FORCE OPTIMIZE** `default: Ctrl + F12`

---

## ⚠️ Disclaimer

**This tool is designed to help with overly aggressive chat filters that block legitimate communication.**

- **Your messages, your responsibility** - COCK doesn't determine what's appropriate

- **Abuse at your own risk** - COCK can't stop other players from reporting you for being an asshole

- **Check game Terms of Service** - Some games prohibit automation tools

- **Educational purpose** - This tool is meant to educate people about the Scunthorpe Problem

---

# 🤝 Contributions

### 🐞 Reporting Issues

Found a bug? [Open an issue](https://github.com/Jokoril/COCK-profanity-processor/issues/new)

**Include:**
- COCK version
- Windows version
- Steps to reproduce
- Expected vs actual behavior
- Console output (if available)

### 💡 Suggesting Features

Have an idea? [Open a feature request](https://github.com/Jokoril/COCK-profanity-processor/issues/new?labels=enhancement)

### 📝 Filter List Contributions (HELLO DATAMINERS)
If you have filter lists for certain games, [Open a feature request](https://github.com/Jokoril/COCK-profanity-processor/issues/new?labels=enhancement) 

- Attach the list as a .txt form, with one entry per line.
- Include the game name
---

# 🙏 Acknowledgments

### Technology Stack

- **[PyQt5](https://www.riverbankcomputing.com/software/pyqt/)** - GUI framework
- **[pyahocorasick](https://github.com/WojciechMula/pyahocorasick)** - Fast pattern matching
- **[keyboard](https://github.com/boppreh/keyboard)** - Global hotkey support
- **[pyperclip](https://github.com/asweigart/pyperclip)** - Clipboard operations
- **[PyInstaller](https://pyinstaller.org/)** - .exe packaging

### Special thanks to:
- Claude AI for being my vibe coding partner and emotional punching bag
- NxhardcorE for supplying the mascot for illustrations
- Beta testers who helped to beta test the beta build

---
<div align="center">

### Made with ❤️ for frustrated gamers everywhere

*Because "Raid Spam" shouldn't be fucking censored.*

[⬆ Back to Top](#features)

</div>****
