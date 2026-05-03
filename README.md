# 🛡 Incognito Guard

**Block incognito/private browsing and get instant email alerts.**  
Built for parents who want to know what their children do when they go private.

---

## What It Does

- Detects any incognito/private window across **Chrome, Edge, Brave, Firefox**
- Closes the tab instantly
- Logs every attempt with timestamp
- Sends a **real-time email alert** to the parent
- Locks the computer after N attempts (configurable)
- PIN-protected so children can't close or tamper with it
- Works on **Windows, Linux, macOS**

---

## Project Structure

```
incognito-guard/
├── extension/
│   ├── background.js           # Cross-browser extension logic
│   ├── manifest_chromium.json  # For Chrome, Edge, Brave
│   └── manifest_firefox.json   # For Firefox
├── guard.py                    # Main desktop app (Python)
├── config.json                 # Your settings (PIN, email, etc.)
├── attempts.log                # Auto-generated attempt log
├── state.json                  # Auto-generated counter state
├── install.ps1                 # Windows setup script
├── install.sh                  # Linux/macOS setup script
└── requirements.txt
```

---

## Setup Guide

### Step 1 — Install Python (if not installed)
- Windows: https://python.org/downloads (check "Add to PATH")
- Linux/macOS: usually pre-installed

### Step 2 — Configure `config.json`

```json
{
  "pin": "YOUR_CHOSEN_PIN",
  "max_attempts": 3,
  "email_alerts": true,
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your_gmail@gmail.com",
  "smtp_pass": "your_16_char_app_password",
  "alert_email": "you@example.com",
  "child_name": "Emma",
  "device_name": "Emma's Laptop"
}
```

> **Gmail tip:** Use an App Password, not your regular password.  
> Go to: Google Account → Security → 2-Step Verification → App Passwords

### Step 3 — Load the Extension

**Chrome / Edge / Brave:**
1. Copy `extension/manifest_chromium.json` → rename to `manifest.json`
2. Open `chrome://extensions` (or `edge://extensions`)
3. Enable **Developer Mode** (top right)
4. Click **Load Unpacked** → select the `extension/` folder
5. Copy your Extension ID (shown under the extension name)

**Firefox:**
1. Copy `extension/manifest_firefox.json` → rename to `manifest.json`
2. Open `about:debugging` → This Firefox → Load Temporary Add-on
3. Select `extension/manifest.json`

### Step 4 — Run the Installer

**Windows (run PowerShell as Admin):**
```powershell
.\install.ps1 -ExtensionId "YOUR_EXTENSION_ID_HERE"
```

**Linux / macOS:**
```bash
sudo bash install.sh YOUR_EXTENSION_ID_HERE
```

### Step 5 — Start the Guard

```bash
python3 guard.py
```

The app will start with your child's PC and run in the background. It requires your PIN to close.

---

## Email Alerts

Each incognito attempt sends an email like this:

> **⚠️ Incognito Attempt Detected – Emma**  
> Emma tried to open a private browser window.  
> Time: May 12, 2025 at 3:47 PM  
> Device: Emma's Laptop  
> Attempt #1

---

## Pricing Tiers (if distributing)

| Tier | Features |
|------|----------|
| Free | Block + counter |
| Pro ($19.99) | Email alerts + log + settings |
| Family ($29.99) | 3 devices |

---

## FAQ

**Q: Can my child disable this?**  
A: The guard app requires a PIN to close. The extension is force-installed via OS policy and cannot be removed from the browser.

**Q: What if they use a different browser?**  
A: Install scripts cover Chrome, Edge, Brave, and Firefox. For Opera/Vivaldi, additional policy paths apply.

**Q: Does it work without internet?**  
A: Yes. Blocking and locking work offline. Email alerts require internet.

---

## License
MIT — free to modify. If you build on this commercially, attribution appreciated.
