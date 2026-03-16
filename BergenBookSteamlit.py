import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException, UnexpectedAlertPresentException
)
from selenium_stealth import stealth
import pause
from datetime import datetime, date, timedelta
import time
import html as html_lib
import os
import streamlit as st
from webdriver_manager.chrome import ChromeDriverManager
import threading
import queue

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BergenBook · Tee Time",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── THEME ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #0c1710; color: #e8f5e9; }
  [data-testid="stHeader"] { background: transparent; }
  [data-testid="stDecoration"] { display: none; }
  .block-container { padding-top: 2rem; }

  h1 { color: #7bc47f !important; letter-spacing: -1px; font-size: 2.2rem !important; }
  h3 { color: #a5d6a7 !important; font-size: 1rem !important; text-transform: uppercase;
       letter-spacing: 1px; margin-bottom: 1rem !important; }

  label { color: #c8e6c9 !important; font-size: 0.82rem !important; font-weight: 500 !important; }

  [data-baseweb="input"] > div,
  [data-baseweb="select"] > div:first-child {
      background: #111f14 !important;
      border: 1px solid #2d5a2d !important;
      border-radius: 8px !important;
  }
  /* All input and select text */
  input,
  [data-baseweb="select"] span,
  [data-baseweb="select"] div,
  [data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"] li,
  [data-baseweb="select"] [role="option"],
  [data-baseweb="select"] [role="listbox"] li { color: #e8f5e9 !important; }
  /* Dropdown list background */
  [data-baseweb="popover"] [data-baseweb="menu"],
  [data-baseweb="select"] ul,
  [role="listbox"] {
      background: #1a2e1e !important;
      border: 1px solid #2d5a2d !important;
  }
  [role="option"]:hover, [role="option"][aria-selected="true"] {
      background: #2d5a2d !important;
  }

  .stButton > button {
      background: linear-gradient(135deg, #2e7d32, #1a4d1e) !important;
      color: white !important; border: none !important;
      border-radius: 10px !important; padding: 0.7rem 1rem !important;
      font-size: 1rem !important; font-weight: 600 !important;
      width: 100%; letter-spacing: 0.3px;
      transition: all 0.2s ease;
  }
  .stButton > button:hover {
      background: linear-gradient(135deg, #43a047, #2e7d32) !important;
      box-shadow: 0 4px 16px rgba(46,125,50,0.45) !important;
      transform: translateY(-1px);
  }
  .stButton > button:disabled { opacity: 0.4 !important; }

  hr { border-color: #1e3d1e !important; margin: 0.75rem 0 !important; }

  .info-pill {
      display: inline-block; padding: 0.25rem 0.75rem;
      background: #132518; border: 1px solid #2d5a2d;
      border-radius: 20px; font-size: 0.78rem; color: #81c784;
  }

  .log-panel {
      background: #070e08;
      border: 1px solid #1a3d1a;
      border-radius: 12px;
      padding: 1rem 1.25rem;
      font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
      font-size: 0.78rem;
      line-height: 1.65;
      height: 430px;
      overflow-y: auto;
      color: #69c069;
      white-space: pre-wrap;
  }
  .log-panel .dim  { color: #2d5a2d; }
  .log-panel .ok   { color: #69f069; }
  .log-panel .warn { color: #ffd54f; }
  .log-panel .err  { color: #ff5252; }

  .status-bar {
      display: flex; align-items: center; gap: 0.5rem;
      margin-bottom: 0.6rem;
  }
  .dot {
      width: 8px; height: 8px; border-radius: 50%;
      display: inline-block;
  }
  .dot-idle    { background: #2d5a2d; }
  .dot-running { background: #69f069; box-shadow: 0 0 6px #69f069; animation: pulse 1s infinite; }
  .dot-done    { background: #00e676; }
  .dot-error   { background: #ff5252; }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }

  .status-label { font-size: 0.8rem; font-weight: 600; }
  .idle-label    { color: #2d5a2d; }
  .running-label { color: #69f069; }
  .done-label    { color: #00e676; }
  .error-label   { color: #ff5252; }

  .field-error {
      display: flex; align-items: flex-start; gap: 0.45rem;
      margin: 0.15rem 0 0.4rem;
      padding: 0.35rem 0.75rem;
      background: rgba(255,82,82,0.10);
      border: 1px solid rgba(255,82,82,0.35);
      border-radius: 7px;
      color: #ff7070; font-size: 0.77rem; font-weight: 500;
      line-height: 1.4;
  }
  .field-error-icon { font-size: 0.85rem; margin-top: 0.05rem; flex-shrink: 0; }

  .validation-banner {
      display: flex; align-items: center; gap: 0.6rem;
      margin-bottom: 1rem; padding: 0.65rem 1rem;
      background: rgba(255,82,82,0.12);
      border: 1px solid rgba(255,82,82,0.4);
      border-radius: 10px;
      color: #ff6b6b; font-size: 0.85rem; font-weight: 600;
  }
  .validation-banner-icon { font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# ─── MODULE-LEVEL STATE ───────────────────────────────────────────────────────
_log_queue: queue.Queue = queue.Queue()
_booking_result: dict = {"success": None, "error": None}

def log(msg: str):
    print(msg)
    _log_queue.put(msg)

# ─── BOOKING GLOBALS (overwritten before each run) ────────────────────────────
user = ''
password = ''
month_and_day = ''
player = '4'
tee_time = '12:00 PM'
tee_range = 30         # minutes ± to search around tee_time
desired_courses = []   # ordered list — index 0 = highest priority

COURSES = [
    "Rockleigh R/W 18", "Darlington 18", "Overpeck 18",
    "Soldier Hill 18", "Valley Brook 18", "Orchard Hills",
    "Darlington Back 9", "Overpeck Back 9", "Rockleigh Back 9",
    "Rockleigh Blue 9", "Soldier Hill Back 9", "Valley Brook 9"
]

TEE_TIMES = [
    "6:00 AM","6:30 AM","7:00 AM","7:30 AM","8:00 AM","8:30 AM",
    "9:00 AM","9:30 AM","10:00 AM","10:30 AM","11:00 AM","11:30 AM",
    "12:00 PM","12:30 PM","1:00 PM","1:30 PM","2:00 PM","2:30 PM",
    "3:00 PM","3:30 PM","4:00 PM","4:30 PM","5:00 PM","5:30 PM",
]

# ─── CHROME DRIVER ────────────────────────────────────────────────────────────
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
]

def find_chrome():
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None

def setup_driver():
    chrome_path = find_chrome()
    if not chrome_path:
        raise FileNotFoundError(
            "Chrome not found. Install Google Chrome or set a path in CHROME_PATHS."
        )
    log(f"🖥️   Using Chrome: {chrome_path}")
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-features=NetworkService')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.binary_location = chrome_path
    driver = uc.Chrome(options=chrome_options, version_main=145)
    stealth(driver,
        languages=["en-US", "en"], vendor="Google Inc.", platform="Win32",
        webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True,
    )
    return driver, WebDriverWait(driver, 20)

# ─── POPUP HANDLER ────────────────────────────────────────────────────────────
def dismiss_popup(driver, wait):
    try:
        alert = driver.switch_to.alert
        log(f"[Popup] Native alert: {alert.text}")
        alert.accept()
        return
    except Exception:
        pass
    try:
        btn = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.ID, "btnAlertOk")))
        msg = driver.find_element(By.CLASS_NAME, "modal-body").text
        log(f"[Popup] {msg}")
        btn.click()
        return
    except TimeoutException:
        pass
    try:
        close_btn = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-dialog-container button[mat-dialog-close]"))
        )
        try:
            content = driver.find_element(By.CSS_SELECTOR, "mat-dialog-content").text
            log(f"[Dialog] {content[:80].strip()}…")
        except NoSuchElementException:
            pass
        driver.execute_script("arguments[0].click();", close_btn)
    except Exception:
        pass

# ─── OVERLAY CLEARER ──────────────────────────────────────────────────────────
def clear_overlays(driver, wait):
    """Dismiss popups and wait for all CDK backdrops to disappear (up to 4 passes)."""
    for _ in range(4):
        dismiss_popup(driver, wait)
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "cdk-overlay-backdrop"))
            )
            return
        except Exception:
            pass

# ─── LOGIN ────────────────────────────────────────────────────────────────────
def login(driver, wait):
    log("🌐  Opening booking page...")
    driver.get('https://bergencountygolf.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23')
    dismiss_popup(driver, wait)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'mat-dialog-container')))
    log("🔐  Signing in...")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Sign In')]"))).click()
    wait.until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys(user)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
    pwd_field = wait.until(EC.element_to_be_clickable((By.ID, 'mat-input-2')))
    driver.execute_script("arguments[0].value = arguments[1];", pwd_field, password)
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
        pwd_field
    )
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
    log("✅  Logged in.")
    clear_overlays(driver, wait)

# ─── WAIT UNTIL BOOKING ───────────────────────────────────────────────────────
def wait_until_booking(driver, wait):
    today = date.today()
    date_of_play = datetime(today.year, int(month_and_day[:2]), int(month_and_day[3:]))
    booking_time = (date_of_play - timedelta(days=7)).replace(hour=19, minute=0, second=0, microsecond=0)

    log(f"📅  Play date:      {date_of_play.strftime('%A, %B %d %Y')}")
    log(f"⏰  Booking opens:  {booking_time.strftime('%A, %B %d at 7:00 PM')}")

    BOOKING_URL = 'https://bergencountygolf.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23'

    if booking_time < datetime.now():
        log("⚠️   Booking window already open — refreshing page...")
        driver.get(BOOKING_URL)
        clear_overlays(driver, wait)
        return False

    while True:
        seconds_left = (booking_time - datetime.now()).total_seconds()
        dismiss_popup(driver, wait)
        if seconds_left <= 10:
            log("⏱️   Final countdown — locking in...")
            break
        elif seconds_left > 300:
            mins = int(seconds_left // 60)
            log(f"⏳  {mins} min until booking opens...")
            time.sleep(60)
        else:
            log(f"⏳  {int(seconds_left)}s remaining...")
            time.sleep(5)

    while datetime.now() < booking_time:
        time.sleep(0.05)

    log("🚀  Booking window reached — refreshing page...")
    driver.get(BOOKING_URL)
    log("🔄  Page refreshed — selecting course...")

    try:
        clear_overlays(driver, wait)

        if desired_courses:
            dropdown = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//mat-select[@name='course']"
            )))
            driver.execute_script("arguments[0].click();", dropdown)

            deselect = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//span[contains(@class,'mat-option-text') and normalize-space(text())='Deselect All']"
            )))
            driver.execute_script("arguments[0].click();", deselect)

            for cname in desired_courses:
                course_opt = wait.until(EC.element_to_be_clickable((By.XPATH,
                    f"//span[contains(@class,'mat-option-text') and normalize-space(text())='{cname}']"
                )))
                driver.execute_script("arguments[0].click();", course_opt)
                log(f"✅  Course '{cname}' added.")

            done_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//button[.//span[normalize-space(text())='Done']]"
            )))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", done_btn)
            driver.execute_script("arguments[0].click();", done_btn)
            clear_overlays(driver, wait)
        else:
            log("ℹ️   Searching across all courses.")

        return True

    except TimeoutException as e:
        log(f"❌  Course selection failed: {e}")
        return False

# ─── SELECT DATE ──────────────────────────────────────────────────────────────
def select_date(driver, wait):
    log(f"📆  Selecting date {month_and_day}...")
    day = str(int(month_and_day.split('/')[1]))
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "day-background-upper")))
    xpath = f"//span[contains(@class,'day-background-upper') and text()='{day}']"
    try:
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        el.click()
    except ElementClickInterceptedException:
        el = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].click();", el)
    except TimeoutException:
        log(f"❌  Date {month_and_day} not found on calendar.")
        raise
    log("✅  Date selected.")

# ─── SELECT TIME ──────────────────────────────────────────────────────────────
def select_time(driver, wait):
    log(f"⏰  Finding tee time {tee_time} (±{tee_range} min)...")

    booking_date = datetime.strptime(
        f"{date.today().year}-{month_and_day[:2]}-{month_and_day[3:]}", "%Y-%m-%d"
    ).strftime("%Y-%m-%d")

    target_dt = datetime.strptime(f"{booking_date} {tee_time}", "%Y-%m-%d %I:%M %p")
    window_start = target_dt - timedelta(minutes=tee_range)
    window_end   = target_dt + timedelta(minutes=tee_range)

    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'teetimetable')]")))
    log("✅  Tee time grid loaded.")

    # Expand any "Show more" buttons
    try:
        for btn in driver.find_elements(By.XPATH,
                "//span[contains(normalize-space(.),'Show more')]/ancestor::button"):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
    except Exception:
        pass

    # Collect all available slots with their datetime values
    all_time_els = driver.find_elements(By.XPATH, "//time[@datetime]")
    requested_players = int(player)
    candidates = []
    for tel in all_time_els:
        dt_str = tel.get_attribute("datetime")
        try:
            slot_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue
        if not (window_start <= slot_dt <= window_end):
            continue
        try:
            ancestor = tel.find_element(By.XPATH,
                "ancestor::div[contains(@class,'teetimetableDateTime')]")
        except NoSuchElementException:
            continue

        slot_text = ""
        try:
            slot_text = ancestor.text
        except Exception:
            pass

        # Detect max available players from slot text (e.g. "4 Players" or "2 spots")
        import re as _re
        avail_players = requested_players  # assume enough if we can't detect
        m = _re.search(r'\b([1-4])\s*(?:player|spot|golfer)', slot_text, _re.IGNORECASE)
        if m:
            avail_players = int(m.group(1))

        # Skip slots that can't fit the requested group size
        if avail_players < requested_players:
            log(f"⏭️  Skipping {slot_dt.strftime('%I:%M %p').lstrip('0')} — only {avail_players} spot(s) available")
            continue

        delta = abs((slot_dt - target_dt).total_seconds())
        priority = len(desired_courses)  # worst priority by default
        if desired_courses:
            slot_text_lower = slot_text.lower()
            for i, cname in enumerate(desired_courses):
                if cname.lower() in slot_text_lower:
                    priority = i
                    break
        log(f"   Found slot {slot_dt.strftime('%I:%M %p').lstrip('0')} | course_priority={priority} | text={slot_text[:60].strip()!r}")
        candidates.append((priority, delta, slot_dt, ancestor))

    if not candidates:
        msg = (f"exact slot {tee_time}" if tee_range == 0
               else f"any slot within ±{tee_range} min of {tee_time}")
        log(f"❌  No available tee time found for {msg}.")
        raise TimeoutException("No matching tee time slot found.")

    # Sort: course priority first, then closest time
    candidates.sort(key=lambda c: (c[0], c[1]))
    best_priority, best_delta, best_dt, el = candidates[0]
    booked_label = best_dt.strftime("%I:%M %p").lstrip("0")
    course_note = f" (course priority #{best_priority + 1})" if desired_courses and best_priority < len(desired_courses) else ""
    log(f"🎯  Best slot: {booked_label}{course_note}")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)
    log(f"✅  Tee time {booked_label} selected.")

# ─── SELECT PLAYERS ───────────────────────────────────────────────────────────
def select_player(driver, wait):
    log(f"👥  Selecting {player} player(s)...")
    # Click the Edit button/span inside the booking detail page
    edit = wait.until(EC.element_to_be_clickable((By.XPATH,
        "//button[.//span[normalize-space(text())='Edit']] | //span[normalize-space(text())='Edit']"
    )))
    driver.execute_script("arguments[0].click();", edit)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mat-bottom-sheet-container")))

    # Find all available player toggle buttons and pick best match
    all_btns_xpath = (
        "//mat-bottom-sheet-container"
        "//button[contains(@class,'mat-button-toggle-button')]"
        "[.//span[normalize-space(text()) >= '1' and normalize-space(text()) <= '4']]"
    )
    wait.until(EC.presence_of_element_located((By.XPATH, all_btns_xpath)))
    avail_btns = driver.find_elements(By.XPATH, all_btns_xpath)
    avail_counts = []
    for b in avail_btns:
        try:
            label = b.find_element(By.XPATH, ".//span").text.strip()
            if label.isdigit():
                avail_counts.append((int(label), b))
        except Exception:
            pass

    avail_counts.sort(key=lambda x: x[0])
    log(f"   Available player options: {[c for c, _ in avail_counts]}")

    requested = int(player)
    chosen_count, btn_to_click = avail_counts[-1]  # default to max available
    for cnt, btn in avail_counts:
        if cnt == requested:
            chosen_count, btn_to_click = cnt, btn
            break

    if chosen_count != requested:
        log(f"⚠️  Requested {requested} players but only {chosen_count} available — booking {chosen_count}.")
    else:
        log(f"✅  Selecting {chosen_count} player(s).")

    driver.execute_script("arguments[0].click();", btn_to_click)

    # Confirm aria-pressed is set
    btn_xpath = (
        f"//mat-bottom-sheet-container"
        f"//button[contains(@class,'mat-button-toggle-button')]"
        f"[.//span[normalize-space(text())='{chosen_count}']]"
    )

    elapsed = 0
    while elapsed < 10:
        try:
            btn = driver.find_element(By.XPATH, btn_xpath)
            # aria-pressed lives on the button itself
            if btn.get_attribute("aria-pressed") == "true":
                log(f"✅  {player} player(s) confirmed.")
                break
        except Exception:
            pass
        time.sleep(0.2); elapsed += 0.2
    else:
        raise TimeoutException("Player selection not confirmed.")

    submit = wait.until(EC.element_to_be_clickable((By.XPATH,
        "//mat-bottom-sheet-container//span[contains(text(),'Submit')]/ancestor::button"
    )))
    driver.execute_script("arguments[0].click();", submit)
    log("✅  Player selection submitted.")

    cont_xpath = "//button[.//span[contains(text(),'Continue')]]"
    cont = wait.until(EC.presence_of_element_located((By.XPATH, cont_xpath)))
    elapsed = 0
    while elapsed < 30:
        cont = driver.find_element(By.XPATH, cont_xpath)
        if not cont.get_attribute("disabled") and 'disabled' not in cont.get_attribute("class"):
            break
        time.sleep(0.3); elapsed += 0.3
    else:
        raise TimeoutException("'Continue' button never enabled.")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cont)
    driver.execute_script("arguments[0].click();", cont)
    log("✅  Proceeding to checkout...")

# ─── FINALIZE ─────────────────────────────────────────────────────────────────
def finalize_booking(driver, wait):
    log("🏁  Finalizing reservation...")
    fin_xpath = "//span[contains(text(),'Finalize Reservation')]"
    fin = wait.until(EC.presence_of_element_located((By.XPATH, fin_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", fin)

    parent = fin.find_element(By.XPATH, "./ancestor::button")
    elapsed = 0
    while elapsed < 10:
        fin = driver.find_element(By.XPATH, fin_xpath)
        parent = fin.find_element(By.XPATH, "./ancestor::button")
        if not parent.get_attribute("disabled") and 'disabled' not in parent.get_attribute("class"):
            break
        time.sleep(0.2); elapsed += 0.2
    else:
        raise TimeoutException("Finalize button never enabled.")

    driver.execute_script("arguments[0].click();", parent)
    log("🎉  Booking confirmed!")
    pause.minutes(1)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    global _booking_result
    _booking_result = {"success": None, "error": None}
    log("─" * 42)
    log(f"  BergenBook  ·  {datetime.now().strftime('%b %d %Y  %I:%M %p')}")
    log("─" * 42)
    try:
        driver, wait = setup_driver()
    except Exception as e:
        log(f"❌  Driver setup failed: {e}")
        _booking_result["error"] = str(e)
        return
    try:
        login(driver, wait)
        wait_until_booking(driver, wait)
        clear_overlays(driver, wait)
        select_date(driver, wait)
        clear_overlays(driver, wait)
        select_time(driver, wait)
        select_player(driver, wait)
        if os.environ.get("DRY_RUN"):
            log("🧪  DRY RUN — skipping finalize. Inspect the browser, then close it.")
            pause.minutes(2)
        else:
            finalize_booking(driver, wait)
        _booking_result["success"] = True
    except Exception as e:
        log(f"❌  {e}")
        _booking_result["error"] = str(e)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

# ─── UI ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':

    # Session state
    for key, val in [('logs', []), ('running', False), ('status', 'idle'), ('errors', {})]:
        if key not in st.session_state:
            st.session_state[key] = val

    def ferr(field):
        """Render an inline error message for a field if one exists."""
        msg = st.session_state.errors.get(field)
        if msg:
            st.markdown(
                f"<div class='field-error'>"
                f"<span class='field-error-icon'>⚠</span>{msg}"
                f"</div>",
                unsafe_allow_html=True
            )

    def validate(user, password, play_date, courses):
        errs = {}
        if not user.strip():
            errs['user'] = "User ID is required."
        if not password:
            errs['password'] = "Password is required."
        if play_date is None:
            errs['date'] = "Play date is required."
        elif play_date < date.today():
            errs['date'] = "Play date must be today or in the future."
        if not courses:
            errs['courses'] = "Select at least one course."
        return errs

    # Header
    st.markdown("# ⛳ BergenBook")
    st.markdown(
        "<p style='color:#546e54;margin-top:-0.8rem;font-size:0.9rem'>"
        "Bergen County Golf &nbsp;·&nbsp; Automated Tee Time Booker</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Default date = 7 days from today
    default_play_date = date.today() + timedelta(days=7)

    left, right = st.columns([1, 1.7], gap="large")

    # ── LEFT: FORM ────────────────────────────────────────────────────────────
    with left:
        st.markdown("### Booking Config")

        # Validation summary banner
        if st.session_state.errors:
            n = len(st.session_state.errors)
            st.markdown(
                f"<div class='validation-banner'>"
                f"<span class='validation-banner-icon'>⛔</span>"
                f"Fix {n} error{'s' if n > 1 else ''} below before booking."
                f"</div>",
                unsafe_allow_html=True
            )

        user_in = st.text_input("User ID *", value="9094566")
        ferr('user')

        password_in = st.text_input("Password *", value="", type="password")
        ferr('password')

        date_in = st.date_input(
            "Play Date *",
            value=default_play_date,
            min_value=date.today(),
            format="MM/DD/YYYY",
        )
        ferr('date')

        col_a, col_b = st.columns(2)
        with col_a:
            player_in = st.selectbox("Players", ["1","2","3","4"], index=3)
        with col_b:
            tee_in = st.selectbox("Tee Time", TEE_TIMES, index=TEE_TIMES.index("12:00 PM"))

        tee_range_in = st.slider(
            "Time Flexibility  (± minutes)",
            min_value=0, max_value=120, value=30, step=5,
            help="Book the closest available tee time within this window around your target. 0 = exact match only."
        )
        parsed_tee = datetime.strptime(tee_in, "%I:%M %p")
        lo = (parsed_tee - timedelta(minutes=tee_range_in)).strftime("%-I:%M %p")
        hi = (parsed_tee + timedelta(minutes=tee_range_in)).strftime("%-I:%M %p")
        if tee_range_in > 0:
            st.markdown(
                f"<div style='font-size:0.78rem;color:#81c784;margin-top:-0.4rem;margin-bottom:0.6rem'>"
                f"🕐 Will book any slot between <b>{lo}</b> and <b>{hi}</b>, closest to {tee_in}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='font-size:0.78rem;color:#ff9800;margin-top:-0.4rem;margin-bottom:0.6rem'>"
                "⚠️ Exact match only — will fail if that slot isn't available</div>",
                unsafe_allow_html=True
            )

        courses_in = st.multiselect(
            "Courses * — select in priority order (1st = preferred)",
            COURSES,
            help="The bot searches all selected courses and books from your top priority down."
        )
        ferr('courses')
        if courses_in:
            pills = " ".join(
                f"<span class='info-pill'>{i+1}. {c}</span>"
                for i, c in enumerate(courses_in)
            )
            st.markdown(
                f"<div style='margin-top:0.3rem;line-height:2'>{pills}</div>",
                unsafe_allow_html=True
            )

        # Booking opens info
        if date_in:
            opens = datetime.combine(date_in - timedelta(days=7), datetime.min.time()).replace(hour=19)
            st.markdown(
                f"<div style='margin-top:0.5rem'>"
                f"<span class='info-pill'>⏰ Booking opens {opens.strftime('%b %d at 7:00 PM')}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        run_btn = st.button("🚀 Start Booking", disabled=st.session_state.running)

    # ── RIGHT: LOG PANEL ──────────────────────────────────────────────────────
    with right:
        st.markdown("### Live Process")

        status_ph = st.empty()
        log_ph    = st.empty()

        def render_log(dot_cls, label_cls, label_txt):
            escaped = "<br>".join(html_lib.escape(m) for m in st.session_state.logs) \
                      if st.session_state.logs \
                      else "<span class='dim'>Waiting to start…\nConfigure your booking and hit Start.</span>"
            status_ph.markdown(
                f"<div class='status-bar'>"
                f"<span class='dot {dot_cls}'></span>"
                f"<span class='status-label {label_cls}'>{label_txt}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            log_ph.markdown(
                f"<div class='log-panel'>{escaped}</div>",
                unsafe_allow_html=True
            )

        if st.session_state.status == 'idle':
            render_log('dot-idle', 'idle-label', 'Idle')
        elif st.session_state.status == 'running':
            render_log('dot-running', 'running-label', 'Running…')
        elif st.session_state.status == 'done':
            render_log('dot-done', 'done-label', 'Completed')
        elif st.session_state.status == 'error':
            render_log('dot-error', 'error-label', 'Error')

    # ── RUN ───────────────────────────────────────────────────────────────────
    if run_btn:
        errs = validate(user_in, password_in, date_in, courses_in)
        st.session_state.errors = errs
        if errs:
            st.rerun()

        st.session_state.errors  = {}
        st.session_state.running = True
        st.session_state.status  = 'running'
        st.session_state.logs    = []

        # Set globals
        globals().update(dict(
            user=user_in, password=password_in,
            month_and_day=date_in.strftime("%m/%d"), player=player_in,
            tee_time=tee_in, tee_range=tee_range_in, desired_courses=courses_in
        ))

        # Drain stale queue entries
        while not _log_queue.empty():
            _log_queue.get_nowait()

        render_log('dot-running', 'running-label', 'Running…')

        t = threading.Thread(target=main, daemon=True)
        t.start()

        while t.is_alive() or not _log_queue.empty():
            updated = False
            while not _log_queue.empty():
                st.session_state.logs.append(_log_queue.get_nowait())
                updated = True
            if updated:
                render_log('dot-running', 'running-label', 'Running…')
            time.sleep(0.1)

        # Final drain
        while not _log_queue.empty():
            st.session_state.logs.append(_log_queue.get_nowait())

        st.session_state.running = False

        if _booking_result.get("success"):
            st.session_state.status = 'done'
            render_log('dot-done', 'done-label', 'Booked!')
            st.success("🎉 Tee time booked successfully!")
        else:
            st.session_state.status = 'error'
            render_log('dot-error', 'error-label', 'Error')
            if _booking_result.get("error"):
                st.error(f"❌ {_booking_result['error']}")
