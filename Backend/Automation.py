"""
Automation.py
--------------
Core system + browser automation module for the Jarvis voice assistant.

Sections:
    1. App control        (open/close apps)
    2. Web search          (quick google lookups)
    3. System control       (shutdown/restart/sleep/volume/brightness)
    4. Chrome control       (tabs, windows, navigation via Chrome DevTools Protocol)

Requirements:
    pip install psutil requests websocket-client screen-brightness-control

Notes:
    - Chrome control requires Chrome to be launched with remote debugging enabled.
      This module handles that automatically (see ensure_chrome_debugging()).
    - Written for Windows (uses os.startfile, shutdown/powershell commands).
      The Chrome control section is OS-agnostic.
"""

import os
import json
import time
import subprocess
import webbrowser
import logging

import psutil
import requests

try:
    import websocket  # from websocket-client
except ImportError:
    websocket = None

try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("Automation")


# ============================================================
# 1. APP CONTROL
# ============================================================

APP_PATHS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "spotify": "spotify.exe",
}


def OpenApp(app_name: str) -> str:
    """Open a known app, fall back to a generic file-open, then a web search."""
    app_name = app_name.lower().strip()

    if app_name in APP_PATHS:
        try:
            subprocess.Popen(APP_PATHS[app_name])
            return f"Opening {app_name}"
        except Exception as e:
            log.warning(f"Direct launch of {app_name} failed: {e}")

    try:
        os.startfile(app_name)
        return f"Opening {app_name}"
    except Exception:
        webbrowser.open(f"https://www.google.com/search?q={app_name}")
        return f"I couldn't find {app_name} on your PC, so I searched for it on the web instead."


def CloseApp(app_name: str) -> str:
    """Kill the first running process whose name matches app_name."""
    app_name = app_name.lower().strip()
    for proc in psutil.process_iter(["name"]):
        try:
            proc_name = (proc.info["name"] or "").lower()
        except Exception:
            continue
        if app_name in proc_name:
            try:
                proc.kill()
                return f"Closed {app_name}"
            except Exception as e:
                return f"Found {app_name} but couldn't close it: {e}"
    return f"Could not find any running process for {app_name}"


# ============================================================
# 2. WEB SEARCH
# ============================================================

def WebSearch(query: str) -> str:
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Searching for {query} on the web."


# ============================================================
# 3. SYSTEM CONTROL
# ============================================================

def SystemControl(command: str) -> str:
    """Handles shutdown/restart/sleep/volume commands via OS calls."""
    command = command.lower()

    if "shutdown" in command:
        os.system("shutdown /s /t 1")
        return "Shutting down."
    if "restart" in command:
        os.system("shutdown /r /t 1")
        return "Restarting."
    if "sleep" in command:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Going to sleep."
    if "volume up" in command:
        for _ in range(5):
            os.system('powershell -Command "(new-object -com wscript.shell).SendKeys([char]175)"')
        return "Volume increased."
    if "volume down" in command:
        for _ in range(5):
            os.system('powershell -Command "(new-object -com wscript.shell).SendKeys([char]174)"')
        return "Volume decreased."
    if "mute" in command:
        os.system('powershell -Command "(new-object -com wscript.shell).SendKeys([char]173)"')
        return "Muted."

    return "I didn't recognize that system command."


def SetBrightness(level: int) -> str:
    """Set screen brightness (0-100). Requires screen-brightness-control."""
    if sbc is None:
        return "Brightness control isn't available. Install screen-brightness-control first."
    try:
        level = max(0, min(100, int(level)))
        sbc.set_brightness(level)
        return f"Brightness set to {level}%."
    except Exception as e:
        return f"Couldn't change brightness: {e}"


# ============================================================
# 4. CHROME CONTROL (Chrome DevTools Protocol)
# ============================================================

CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
CDP_BASE = f"http://{CDP_HOST}:{CDP_PORT}"


def ensure_chrome_debugging() -> bool:
    """Make sure a Chrome instance is running with remote debugging enabled.
    Launches one if not already running. Returns True if reachable."""
    try:
        requests.get(f"{CDP_BASE}/json/version", timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        pass

    chrome_path = APP_PATHS.get("chrome")
    try:
        subprocess.Popen([
            chrome_path,
            f"--remote-debugging-port={CDP_PORT}",
            "--remote-allow-origins=*",
        ])
    except Exception as e:
        log.error(f"Could not launch Chrome with debugging enabled: {e}")
        return False

    for _ in range(20):
        time.sleep(0.25)
        try:
            requests.get(f"{CDP_BASE}/json/version", timeout=1)
            return True
        except requests.exceptions.ConnectionError:
            continue
    return False


def _list_targets():
    """Raw list of Chrome tab/page targets from CDP."""
    resp = requests.get(f"{CDP_BASE}/json/list", timeout=2)
    resp.raise_for_status()
    return [t for t in resp.json() if t.get("type") == "page"]


def _send_cdp(ws_url: str, method: str, params: dict = None, timeout: float = 3.0):
    """Send a single CDP command over a tab's websocket and return the result."""
    if websocket is None:
        raise RuntimeError("websocket-client is not installed.")
    ws = websocket.create_connection(ws_url, timeout=timeout)
    try:
        msg = {"id": 1, "method": method, "params": params or {}}
        ws.send(json.dumps(msg))
        while True:
            raw = ws.recv()
            data = json.loads(raw)
            if data.get("id") == 1:
                return data
    finally:
        ws.close()


def list_tabs() -> list:
    """Return [{index, title, url}] for every open Chrome tab."""
    if not ensure_chrome_debugging():
        return []
    targets = _list_targets()
    return [
        {"index": i, "title": t.get("title", ""), "url": t.get("url", "")}
        for i, t in enumerate(targets)
    ]


def open_tab(url: str = "https://www.google.com") -> str:
    """Open a new Chrome tab at the given URL."""
    if not ensure_chrome_debugging():
        return "Couldn't connect to Chrome."
    if not url.startswith("http"):
        url = "https://" + url
    try:
        requests.put(f"{CDP_BASE}/json/new?{url}", timeout=3)
        return f"Opened a new tab: {url}"
    except Exception as e:
        return f"Couldn't open tab: {e}"


def close_tab(index: int = None, title_contains: str = None) -> str:
    """Close a tab by index (from list_tabs) or by partial title match."""
    if not ensure_chrome_debugging():
        return "Couldn't connect to Chrome."
    targets = _list_targets()
    target = None

    if index is not None and 0 <= index < len(targets):
        target = targets[index]
    elif title_contains:
        title_contains = title_contains.lower()
        for t in targets:
            if title_contains in t.get("title", "").lower():
                target = t
                break

    if not target:
        return "Couldn't find that tab."

    try:
        requests.get(f"{CDP_BASE}/json/close/{target['id']}", timeout=3)
        return f"Closed tab: {target.get('title', target['id'])}"
    except Exception as e:
        return f"Couldn't close tab: {e}"


def switch_tab(index: int = None, title_contains: str = None) -> str:
    """Bring a tab to the front by index or partial title match."""
    if not ensure_chrome_debugging():
        return "Couldn't connect to Chrome."
    targets = _list_targets()
    target = None

    if index is not None and 0 <= index < len(targets):
        target = targets[index]
    elif title_contains:
        title_contains = title_contains.lower()
        for t in targets:
            if title_contains in t.get("title", "").lower():
                target = t
                break

    if not target:
        return "Couldn't find that tab."

    try:
        requests.get(f"{CDP_BASE}/json/activate/{target['id']}", timeout=3)
        return f"Switched to tab: {target.get('title', target['id'])}"
    except Exception as e:
        return f"Couldn't switch tab: {e}"


def get_current_tab() -> dict:
    """Return {title, url} of the first (topmost) page target."""
    targets = _list_targets() if ensure_chrome_debugging() else []
    if not targets:
        return {}
    t = targets[0]
    return {"title": t.get("title", ""), "url": t.get("url", "")}


def go_to(url: str, index: int = 0) -> str:
    """Navigate a tab (default: first tab) to a new URL."""
    if not ensure_chrome_debugging():
        return "Couldn't connect to Chrome."
    if not url.startswith("http"):
        url = "https://" + url
    targets = _list_targets()
    if not targets or index >= len(targets):
        return "No matching tab found."
    try:
        _send_cdp(targets[index]["webSocketDebuggerUrl"], "Page.navigate", {"url": url})
        return f"Navigating to {url}"
    except Exception as e:
        return f"Couldn't navigate: {e}"


def go_back(index: int = 0) -> str:
    return _navigate_history(index, delta=-1)


def go_forward(index: int = 0) -> str:
    return _navigate_history(index, delta=1)


def _navigate_history(index: int, delta: int) -> str:
    if not ensure_chrome_debugging():
        return "Couldn't connect to Chrome."
    targets = _list_targets()
    if not targets or index >= len(targets):
        return "No matching tab found."
    ws_url = targets[index]["webSocketDebuggerUrl"]
    try:
        history = _send_cdp(ws_url, "Page.getNavigationHistory")
        entries = history["result"]["entries"]
        current = history["result"]["currentIndex"]
        new_index = current + delta
        if 0 <= new_index < len(entries):
            entry_id = entries[new_index]["id"]
            _send_cdp(ws_url, "Page.navigateToHistoryEntry", {"entryId": entry_id})
            return "Went back." if delta < 0 else "Went forward."
        return "No more history in that direction."
    except Exception as e:
        return f"Couldn't navigate history: {e}"


def refresh(index: int = 0) -> str:
    if not ensure_chrome_debugging():
        return "Couldn't connect to Chrome."
    targets = _list_targets()
    if not targets or index >= len(targets):
        return "No matching tab found."
    try:
        _send_cdp(targets[index]["webSocketDebuggerUrl"], "Page.reload")
        return "Page refreshed."
    except Exception as e:
        return f"Couldn't refresh: {e}"


def new_window(url: str = "https://www.google.com") -> str:
    """Open a brand new Chrome window."""
    chrome_path = APP_PATHS.get("chrome")
    try:
        subprocess.Popen([chrome_path, "--new-window", url])
        return "Opened a new Chrome window."
    except Exception as e:
        return f"Couldn't open a new window: {e}"


# ============================================================
# VOICE COMMAND ROUTER (optional convenience layer)
# ============================================================

CHROME_LAUNCH_WORDS = {"chrome", "google chrome", "the browser", "browser"}


def handle_chrome_command(text: str) -> str:
    """Very simple keyword router for natural-language Chrome commands.
    Plug this into your Jarvis intent handler."""
    text = text.lower().strip()

    if text.startswith(("open ", "go to ")):
        target = text.split(" ", 1)[1].strip()
        # "open chrome" / "open the browser" -> launch the app itself,
        # not a tab pointed at a URL called "chrome".
        if target in CHROME_LAUNCH_WORDS:
            return OpenApp("chrome")
        return open_tab(target)
    if "new tab" in text:
        return open_tab()
    if "close tab" in text or "close this tab" in text:
        return close_tab(index=0)
    if "new window" in text:
        return new_window()
    if "go back" in text:
        return go_back()
    if "go forward" in text:
        return go_forward()
    if "refresh" in text or "reload" in text:
        return refresh()
    if "list tabs" in text or "what tabs" in text:
        tabs = list_tabs()
        return "; ".join(f"{t['index']}: {t['title']}" for t in tabs) or "No tabs open."
    if "switch to" in text:
        title = text.split("switch to", 1)[1].strip()
        return switch_tab(title_contains=title)

    return "I didn't understand that Chrome command."


if __name__ == "__main__":
    handle_chrome_command("new tab")