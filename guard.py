import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os
import sys
import platform
import time
import smtplib
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

# ─────────────────────────────────────────
#  PATHS — PyInstaller + normal mode safe
# ─────────────────────────────────────────
def resource_path(filename):
    """Bundled read-only files (ships inside .exe)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

def writable_path(filename):
    """Writable files (state.json, log) — always next to the .exe or script."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

CONFIG_FILE = resource_path("config.json")
STATE_FILE  = writable_path("state.json")
LOG_FILE    = writable_path("attempts.log")

# ─────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ─────────────────────────────────────────
#  CONFIG  (email, PIN, limits)
# ─────────────────────────────────────────
DEFAULT_CONFIG = {
    "pin": "1234",
    "max_attempts": 3,
    "cooldown_seconds": 1800,
    "email_alerts": False,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_pass": "",
    "alert_email": "",
    "child_name": "your child",
    "device_name": platform.node()
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)
    # fill any missing keys from defaults
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg

config = load_config()

# ─────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"count": 0, "last_time": 0, "total": 0}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)

state = load_state()

# ─────────────────────────────────────────
#  EMAIL ALERT
# ─────────────────────────────────────────
def send_email_alert(attempt_number: int):
    if not config.get("email_alerts"):
        return
    if not config["smtp_user"] or not config["alert_email"]:
        return

    try:
        child  = config["child_name"]
        device = config["device_name"]
        now    = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ Incognito Attempt Detected – {child}"
        msg["From"]    = config["smtp_user"]
        msg["To"]      = config["alert_email"]

        text = (
            f"Alert from Incognito Guard\n\n"
            f"{child} tried to open an incognito/private browser window.\n"
            f"Time: {now}\n"
            f"Device: {device}\n"
            f"Attempt #{attempt_number} in this session.\n\n"
            f"The tab was closed automatically.\n"
            f"If {attempt_number} >= {config['max_attempts']}, the device has been locked."
        )

        html = f"""
        <html><body style="font-family:Arial,sans-serif;padding:20px;">
          <div style="max-width:500px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
            <div style="background:#e53935;padding:16px;">
              <h2 style="color:white;margin:0;">⚠️ Incognito Attempt Detected</h2>
            </div>
            <div style="padding:20px;">
              <p><strong>{child}</strong> tried to open a private/incognito browser window.</p>
              <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:6px;color:#555;">Time</td><td style="padding:6px;"><strong>{now}</strong></td></tr>
                <tr style="background:#f9f9f9;"><td style="padding:6px;color:#555;">Device</td><td style="padding:6px;"><strong>{device}</strong></td></tr>
                <tr><td style="padding:6px;color:#555;">Attempt</td><td style="padding:6px;"><strong>#{attempt_number}</strong></td></tr>
              </table>
              <p style="margin-top:16px;color:#888;font-size:13px;">
                The tab was closed automatically by Incognito Guard.
              </p>
            </div>
          </div>
        </body></html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["smtp_user"], config["smtp_pass"])
            server.sendmail(config["smtp_user"], config["alert_email"], msg.as_string())

        logging.info(f"Email alert sent for attempt #{attempt_number}")

    except Exception as e:
        logging.error(f"Email send failed: {e}")

# ─────────────────────────────────────────
#  SYSTEM LOCK
# ─────────────────────────────────────────
def lock_system():
    os_name = platform.system()
    logging.info("System lock triggered")
    if os_name == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif os_name == "Linux":
        os.system("loginctl lock-session")
    elif os_name == "Darwin":
        os.system('osascript -e \'tell application "System Events" to keystroke "q" using {command down, control down, option down}\'')

# ─────────────────────────────────────────
#  REGISTER ATTEMPT  (must run on main thread)
# ─────────────────────────────────────────
def register_attempt():
    global state
    now = time.time()

    if now - state["last_time"] > config["cooldown_seconds"]:
        state["count"] = 0

    state["count"]  += 1
    state["total"]  += 1
    state["last_time"] = now
    save_state(state)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Incognito attempt #{state['count']} (total: {state['total']})")

    counter_label.config(text=str(state["count"]))
    total_label.config(text=f"Total all-time: {state['total']}")
    last_label.config(text=f"Last: {ts}")

    # Send email in background so UI doesn't freeze
    threading.Thread(
        target=send_email_alert,
        args=(state["count"],),
        daemon=True
    ).start()

    if state["count"] >= config["max_attempts"]:
        status_label.config(text="⚠️ Limit reached! Locking...", fg="#e53935")
        root.after(1500, lock_system)
    else:
        remaining = config["max_attempts"] - state["count"]
        status_label.config(
            text=f"⚠️ Attempt logged! {remaining} left before lock.",
            fg="#f57c00"
        )

# ─────────────────────────────────────────
#  HTTP SERVER
# ─────────────────────────────────────────
class IncognitoHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/incognito":
            # Schedule on main thread — thread-safe Tkinter
            root.after(0, register_attempt)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # silence server logs to console

def start_server():
    server = HTTPServer(("127.0.0.1", 8765), IncognitoHandler)
    server.serve_forever()

# ─────────────────────────────────────────
#  PIN PROTECTION
# ─────────────────────────────────────────
def prompt_pin(action_label="proceed"):
    pin = simpledialog.askstring(
        "PIN Required",
        f"Enter your parent PIN to {action_label}:",
        show="*",
        parent=root
    )
    return pin == config["pin"]

def on_close():
    if prompt_pin("close Incognito Guard"):
        logging.info("App closed by parent (PIN verified)")
        root.destroy()
    else:
        messagebox.showerror("Access Denied", "Incorrect PIN.")

# ─────────────────────────────────────────
#  SETTINGS WINDOW
# ─────────────────────────────────────────
def open_settings():
    if not prompt_pin("open Settings"):
        messagebox.showerror("Access Denied", "Incorrect PIN.")
        return

    win = tk.Toplevel(root)
    win.title("Settings")
    win.geometry("380x480")
    win.resizable(False, False)

    fields = {}

    def row(label, key, show=None):
        tk.Label(win, text=label, anchor="w").pack(fill="x", padx=20, pady=(8, 0))
        e = tk.Entry(win, show=show)
        e.insert(0, str(config.get(key, "")))
        e.pack(fill="x", padx=20)
        fields[key] = e

    row("Child's Name",     "child_name")
    row("Device Name",      "device_name")
    row("Max Attempts",     "max_attempts")
    row("Parent PIN",       "pin",       show="*")
    row("Alert Email",      "alert_email")
    row("SMTP Host",        "smtp_host")
    row("SMTP Port",        "smtp_port")
    row("SMTP Username",    "smtp_user")
    row("SMTP Password",    "smtp_pass", show="*")

    email_var = tk.BooleanVar(value=config["email_alerts"])
    tk.Checkbutton(win, text="Enable Email Alerts", variable=email_var).pack(pady=8)

    def save():
        for key, entry in fields.items():
            val = entry.get()
            if key in ("max_attempts", "smtp_port"):
                try:
                    val = int(val)
                except ValueError:
                    pass
            config[key] = val
        config["email_alerts"] = email_var.get()
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        messagebox.showinfo("Saved", "Settings saved successfully.")
        win.destroy()

    tk.Button(win, text="Save Settings", command=save,
              bg="#2e7d32", fg="white", padx=10, pady=6).pack(pady=12)

# ─────────────────────────────────────────
#  UI
# ─────────────────────────────────────────
#  TRAY + UI
# ─────────────────────────────────────────
root = tk.Tk()
root.title("Incognito Guard")
root.geometry("340x380")
root.resizable(False, False)
root.configure(bg="#1a1a2e")

# ── Hide to tray on startup ──────────────
root.withdraw()  # start hidden

def show_window():
    root.deiconify()
    root.lift()
    root.focus_force()

def hide_window():
    root.withdraw()

def quit_app():
    if prompt_pin("quit Incognito Guard"):
        logging.info("App quit by parent (PIN verified)")
        if tray_icon:
            tray_icon.stop()
        root.destroy()
    else:
        messagebox.showerror("Access Denied", "Incorrect PIN.")

# ── System tray icon ─────────────────────
tray_icon = None

def setup_tray():
    global tray_icon
    try:
        import pystray
        from PIL import Image as PILImage

        # Load or create tray icon image
        try:
            img = PILImage.open(resource_path("icon48.png")).resize((64, 64))
        except Exception:
            # Fallback: draw a red square
            img = PILImage.new("RGB", (64, 64), color=(255, 62, 94))

        menu = pystray.Menu(
            pystray.MenuItem("Open Incognito Guard", lambda: root.after(0, show_window), default=True),
            pystray.MenuItem("Settings", lambda: root.after(0, open_settings)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit (PIN required)", lambda: root.after(0, quit_app)),
        )

        tray_icon = pystray.Icon(
            "IncognitoGuard",
            img,
            "Incognito Guard — Monitoring",
            menu
        )

        threading.Thread(target=tray_icon.run, daemon=True).start()

    except ImportError:
        # pystray not installed — fall back to showing the window
        root.deiconify()

setup_tray()

# ── Build UI (shown when user opens from tray) ──
# Header
header = tk.Frame(root, bg="#e53935", pady=12)
header.pack(fill="x")
tk.Label(header, text="🛡 Incognito Guard", font=("Arial", 15, "bold"),
         bg="#e53935", fg="white").pack()
tk.Label(header, text="Parental Control Monitor", font=("Arial", 9),
         bg="#e53935", fg="#ffcdd2").pack()

# Body
body = tk.Frame(root, bg="#1a1a2e", pady=10)
body.pack(fill="both", expand=True)

tk.Label(body, text="Attempts This Session",
         font=("Arial", 10), bg="#1a1a2e", fg="#aaa").pack(pady=(10, 0))

counter_label = tk.Label(body, text=str(state["count"]),
                          font=("Arial", 48, "bold"), bg="#1a1a2e", fg="#ef5350")
counter_label.pack()

total_label = tk.Label(body, text=f"Total all-time: {state['total']}",
                        font=("Arial", 9), bg="#1a1a2e", fg="#777")
total_label.pack()

last_ts = datetime.fromtimestamp(state["last_time"]).strftime("%Y-%m-%d %H:%M:%S") \
    if state["last_time"] else "Never"
last_label = tk.Label(body, text=f"Last: {last_ts}",
                       font=("Arial", 9), bg="#1a1a2e", fg="#777")
last_label.pack(pady=(2, 8))

status_label = tk.Label(body, text="✅ Monitoring...",
                          font=("Arial", 10), bg="#1a1a2e", fg="#66bb6a")
status_label.pack()

email_status = "📧 Email alerts ON" if config["email_alerts"] else "📧 Email alerts OFF"
tk.Label(body, text=email_status, font=("Arial", 9),
         bg="#1a1a2e", fg="#90caf9").pack(pady=4)

# Footer
footer = tk.Frame(root, bg="#1a1a2e", pady=8)
footer.pack(fill="x")
tk.Button(footer, text="⚙ Settings", command=open_settings,
          bg="#37474f", fg="white", relief="flat", padx=12, pady=5).pack(side="left", padx=12)
tk.Button(footer, text="📄 View Log",
          command=lambda: os.startfile(LOG_FILE) if platform.system() == "Windows"
          else os.system(f"xdg-open {LOG_FILE}"),
          bg="#37474f", fg="white", relief="flat", padx=12, pady=5).pack(side="left")
tk.Button(footer, text="Hide to Tray", command=hide_window,
          bg="#37474f", fg="white", relief="flat", padx=12, pady=5).pack(side="right", padx=12)

# Closing window hides to tray instead of quitting
root.protocol("WM_DELETE_WINDOW", hide_window)

# Start HTTP server
threading.Thread(target=start_server, daemon=True).start()

root.mainloop()
