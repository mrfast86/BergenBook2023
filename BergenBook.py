import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, UnexpectedAlertPresentException
from selenium_stealth import stealth
from datetime import datetime, date, timedelta
import time
import streamlit as st
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import platform
import shutil
import base64
import pause

# --- STREAMLIT LOGGING SETUP ---
log_lines = []  # For download button later

def log(message):
    print(message) # still logs to terminal
    log_lines.append(message)

    # Color coding
    if '✅' in message or 'success' in message.lower():
        color = 'green'
    elif '⚠️' in message or 'warning' in message.lower():
        color = 'orange'
    elif '❌' in message or 'error' in message.lower():
        color = 'red'
    else:
        color = 'black'

    # Auto-scroll log display
    log_html = "".join(f'<div style="color:{color};">{line}</div>' for line in log_lines)
    log_container.markdown(f"""
        <div style="height:400px; overflow-y: auto;">{log_html}<div></div></div>
    """, unsafe_allow_html=True)

preferred_courses = [
    "Rockleigh R/W 18",
    "Darlington 18",
    "Overpeck 18",
    "Soldier Hill 18",
    "Valley Brook 18",
    "Orchard Hills",
    "Darlington Back 9",
    "Overpeck Back 9",
    "Rockleigh Back 9",
    "Rockleigh Blue 9",
    "Soldier Hill Back 9",
    "Valley Brook 9"
]

# --- DRIVER SETUP ---
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--metrics-recording-only')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--disable-translate')

    import subprocess

    if "STREAMLIT_SERVER_ENABLED" in os.environ:
        # ✅ Streamlit Cloud environment
        chrome_options.binary_location = "/usr/bin/chromium"
        chrome_options.add_argument('--headless')

        # Optional: Check version for debugging
        try:
            version = subprocess.check_output(['/usr/bin/chromium', '--version']).decode().strip()
            log(f"✅ Found Chromium version: {version}")
        except Exception as e:
            log(f"❌ Chromium not found or error getting version: {e}")

    else:
        # ✅ Local development environment
        system = platform.system()
        if system == "Windows":
            chrome_options.binary_location = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
        elif system == "Darwin":  # macOS
            chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        elif system == "Linux":
            binary_path = shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chromium")
            if binary_path:
                chrome_options.binary_location = binary_path
                try:
                    version = subprocess.check_output([binary_path, '--version']).decode().strip()
                    log(f"✅ Found Chrome/Chromium version: {version}")
                except Exception as e:
                    log(f"⚠️ Error getting Chrome version: {e}")
            else:
                log("⚠️ Chrome binary not found on Linux. Make sure Chrome or Chromium is installed.")

    # ✅ Create driver
    driver = uc.Chrome(
        options=chrome_options,
        driver_executable_path=ChromeDriverManager().install()
    )

    # ✅ Apply stealth mode
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver, WebDriverWait(driver, 20)

# --- POPUP HANDLER ---
def dismiss_popup(driver, wait):
    try:
        alert = driver.switch_to.alert
        log(f"[Popup] Native alert: {alert.text}")
        alert.accept()
        log("[Popup] Native alert dismissed.")
        return
    except Exception:
        pass

    try:
        alert_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, "btnAlertOk"))
        )
        alert_message = driver.find_element(By.CLASS_NAME, "modal-body").text
        log(f"[Popup] Old popup: {alert_message}")
        alert_button.click()
        log("[Popup] Old popup dismissed.")
        return
    except TimeoutException:
        pass

    try:
        overlay = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cdk-overlay-container"))
        )
        close_button = overlay.find_element(By.CSS_SELECTOR, "button[mat-dialog-close]")

        try:
            dialog_content = overlay.find_element(By.CSS_SELECTOR, "mat-dialog-content").text
            log(f"[Popup] MatDialog: {dialog_content}")
        except NoSuchElementException:
            log("[Popup] MatDialog appeared, no content found.")

        try:
            close_button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", close_button)

        log("[Popup] MatDialog dismissed.")
    except Exception:
        pass

# --- LOGIN FLOW ---
def login(driver, wait):
    log("Opening booking page...")
    driver.get('https://bergencountygolf.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23')

    dismiss_popup(driver, wait)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'mat-dialog-container')))

    log("Clicking Sign In...")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Sign In')]"))).click()

    log("Entering username...")
    wait.until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys(user)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    log("Entering password...")
    wait.until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    log("✅ Logged in successfully.")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    dismiss_popup(driver, wait)

# --- WAIT UNTIL BOOKING TIME ---
def wait_until_booking(driver, wait):
    today = date.today()
    date_of_play = datetime(today.year, int(month_and_day[:2]), int(month_and_day[3:]), 0, 0)
    booking_time = (date_of_play - timedelta(days=7)).replace(hour=19, minute=0, second=0, microsecond=0)

    log(f"📅 Date of play: {date_of_play}")
    log(f"🕖 Booking initiation time: {booking_time}")

    if booking_time < datetime.now():
        log(f"⚠️ Booking initiation time already passed: {booking_time}, trying right away...")

    # Step 1: Pre-wait loop until very close to booking time
    while True:
        now = datetime.now()
        seconds_left = (booking_time - now).total_seconds()
        dismiss_popup(driver, wait)

        if seconds_left <= 10:
            log("⏱️ Less than 10 seconds to go — entering tight wait...")
            break
        elif seconds_left > 300:
            mins = int(seconds_left // 60)
            secs = int(seconds_left % 60)
            log(f"🧩 Waiting: {mins} min {secs} sec remaining until booking...")
            time.sleep(60)
        else:
            log(f"🧩 Close: {int(seconds_left)} seconds left until booking...")
            time.sleep(5)

    # Step 2: Final tight wait
    while datetime.now() < booking_time:
        time.sleep(0.05)

    log(f"🚀 Booking time reached: {datetime.now()} — Starting course selection...")

    try:
        dismiss_popup(driver, wait)
        # Step 3: Open the course selection dropdown
        dropdown_xpath = "//div[contains(@class, 'mat-select-value') and .//span[contains(text(), 'Multiple Courses Selected')]]"
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)
        log("✅ Course dropdown opened.")

        # Step 4: Deselect all courses
        deselect_all_xpath = "//span[contains(@class, 'mat-option-text') and normalize-space(text())='Deselect All']"
        deselect_all_option = wait.until(EC.element_to_be_clickable((By.XPATH, deselect_all_xpath)))
        driver.execute_script("arguments[0].click();", deselect_all_option)
        log("✅ 'Deselect All' clicked.")

        # Step 5: Select your desired course
        course_option_xpath = f"//span[contains(@class, 'mat-option-text') and normalize-space(text())='{desired_course_name}']"
        course_option = wait.until(EC.element_to_be_clickable((By.XPATH, course_option_xpath)))
        driver.execute_script("arguments[0].click();", course_option)
        log(f"✅ Course '{desired_course_name}' selected.")

        # ✅ Step 6: Click the "Done" button to close dropdown
        done_button_xpath = "//button[.//span[normalize-space(text())='Done']]"
        done_button = wait.until(EC.element_to_be_clickable((By.XPATH, done_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", done_button)
        driver.execute_script("arguments[0].click();", done_button)
        log("✅ 'Done' button clicked to finalize course selection.")

        return True

    except TimeoutException as e:
        log(f"❌ Failed during course selection flow: {e}")
        return False

# --- BOOKING FLOW ---
def select_date(driver, wait):
    log(f"Selecting date: {month_and_day}")

    # Extract day number from month_and_day
    day = str(int(month_and_day.split('/')[1]))  # '04/15' -> '15'

    # Wait for the calendar to load
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "day-background-upper")))

    # Build XPath for the desired day
    date_xpath = f"//span[contains(@class, 'day-background-upper') and text()='{day}']"

    try:
        # Try normal click
        element = wait.until(EC.element_to_be_clickable((By.XPATH, date_xpath)))
        element.click()
        log(f"✅ Date {month_and_day} clicked normally.")
    except ElementClickInterceptedException:
        log(f"⚠️ Normal click blocked. Trying JavaScript click...")
        element = driver.find_element(By.XPATH, date_xpath)
        driver.execute_script("arguments[0].click();", element)
        log(f"✅ Date {month_and_day} clicked with JavaScript.")
    except TimeoutException:
        log(f"❌ Date {month_and_day} not found.")
        days = driver.find_elements(By.CLASS_NAME, "day-background-upper")
        for d in days:
            log(f" - Available day: {d.text}")
        raise

from datetime import datetime, timedelta

from datetime import datetime, timedelta

def select_time(driver, wait):
    log(f"🎯 Selecting time: {tee_time} (±{time_window_minutes} minutes)")

    # Parse desired target datetime
    hour, minute_ampm = tee_time.split(':')
    minute, ampm = minute_ampm.strip().split(' ')
    today = date.today()
    booking_date = f"{today.year}-{month_and_day[:2]}-{month_and_day[3:]}"
    booking_date = datetime.strptime(booking_date, "%Y-%m-%d")

    # Convert to 24-hour target datetime
    hour_24 = int(hour)
    if ampm.upper() == "PM" and hour_24 != 12:
        hour_24 += 12
    if ampm.upper() == "AM" and hour_24 == 12:
        hour_24 = 0
    target_datetime = datetime.combine(booking_date, datetime.min.time()).replace(hour=hour_24, minute=0, second=0)

    # Step 1: Wait for the tee time grid to load
    tee_time_grid_xpath = "//div[contains(@class, 'teetimetable')]"
    try:
        log("⏳ Waiting for tee time grid to load...")
        wait.until(EC.presence_of_element_located((By.XPATH, tee_time_grid_xpath)))
        log("✅ Tee time grid loaded.")
    except TimeoutException:
        log("❌ Tee time grid did not load in time.")
        raise

    # Step 2: Try clicking any "Show more" buttons (non-blocking)
    try:
        show_more_buttons = driver.find_elements(By.XPATH, "//span[contains(normalize-space(.), 'Show more')]/ancestor::button")
        for button in show_more_buttons:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            driver.execute_script("arguments[0].click();", button)
            log("✅ Clicked 'Show more' button.")
            time.sleep(0.5)
    except Exception as e:
        log(f"⚠️ Error while checking 'Show more' buttons: {e}")

    # Step 3: Find all available tee times
    try:
        all_tee_times = driver.find_elements(By.CSS_SELECTOR, "div.teetimetableDateTime")
        available_times = []

        for tee in all_tee_times:
            try:
                time_element = tee.find_element(By.TAG_NAME, "time")
                tee_time_str = time_element.get_attribute("datetime")  # e.g., '2025-04-10T11:30:00'
                tee_time_dt = datetime.strptime(tee_time_str, "%Y-%m-%dT%H:%M:%S")

                # Calculate time difference
                time_diff = abs((tee_time_dt - target_datetime).total_seconds()) / 60  # in minutes

                if time_diff <= time_window_minutes:  # use configurable window
                    available_times.append({
                        'element': tee,
                        'datetime': tee_time_dt,
                        'diff': time_diff
                    })

            except Exception as parse_error:
                log(f"⚠️ Error parsing tee time element: {parse_error}")

        if not available_times:
            log(f"❌ No available tee times within {time_window_minutes} minutes of target time {tee_time}.")
            raise TimeoutException()

        # Step 4: Sort by closest to target time
        available_times.sort(key=lambda x: x['diff'])
        log(f"🧩 Found {len(available_times)} tee times within {time_window_minutes} minutes. Attempting to select closest one.")

        # Step 5: Attempt to click the closest one
        for tee_option in available_times:
            try:
                tee_element = tee_option['element']
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tee_element)
                driver.execute_script("arguments[0].click();", tee_element)
                selected_time_str = tee_option['datetime'].strftime("%H:%M")
                log(f"✅ Tee time {selected_time_str} selected.")
                return  # Successfully selected, exit the function
            except Exception as click_error:
                log(f"⚠️ Failed to click tee time {tee_option['datetime'].strftime('%H:%M')}: {click_error}")

        # Step 6: If none could be clicked
        log("❌ All tee times within range were unclickable.")
        raise TimeoutException()

    except Exception as e:
        log(f"⚠️ Unexpected error while selecting tee time: {e}")
        raise

def select_player(driver, wait):
    log("🎯 Starting player selection flow...")

    try:
        # Step 1: Open player selection popup
        log("🧩 Clicking 'Edit' to open player selection...")
        edit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Edit')]")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_button)
        driver.execute_script("arguments[0].click();", edit_button)

        # Step 2: Wait for popup and player buttons to load
        log("⏳ Waiting for player selection popup to load...")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mat-bottom-sheet-container")))

        log("⏳ Waiting for player toggle buttons to load inside popup...")
        player_button_xpath = (
            f"//mat-bottom-sheet-container//button[contains(@class, 'mat-button-toggle-button')]//span[contains(text(), '{player}')]/ancestor::button"
        )
        wait.until(EC.presence_of_element_located((By.XPATH, player_button_xpath)))
        log("✅ Player selection popup is ready.")

        # Step 3: Select desired player
        log(f"🧩 Selecting player: {player}")
        player_button = wait.until(EC.element_to_be_clickable((By.XPATH, player_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", player_button)
        driver.execute_script("arguments[0].click();", player_button)
        log(f"✅ Player {player} clicked.")

        # Step 4: Confirm selection via aria-pressed
        log("⏳ Confirming player selection (aria-pressed='true')...")
        max_wait_time, poll_interval = 10, 0.2
        elapsed_time = 0

        player_button_xpath = f"//mat-bottom-sheet-container//button[contains(@class, 'mat-button-toggle-button')]//span[contains(text(), '{player}')]/ancestor::button"

        while elapsed_time < max_wait_time:
            try:
                # Refresh the button reference every time
                player_button_fresh = driver.find_element(By.XPATH, player_button_xpath)
                aria_pressed = player_button_fresh.get_attribute("aria-pressed")

                if aria_pressed == "true":
                    log(f"✅ Player {player} selection confirmed (aria-pressed='true').")
                    break

            except Exception as e:
                # Optionally log: element not found (can happen during re-render)
                log(f"🔄 Waiting for player button to re-appear... {e}")

            time.sleep(poll_interval)
            elapsed_time += poll_interval
        else:
            raise TimeoutException(f"❌ Player {player} selection not confirmed in time.")

        # Step 5: Click Submit
        log("🧩 Submitting player selection...")
        submit_button_xpath = "//mat-bottom-sheet-container//span[contains(text(), 'Submit')]/ancestor::button"
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, submit_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        driver.execute_script("arguments[0].click();", submit_button)
        log("✅ Player selection submitted.")

        # Step 6: Wait for 'Continue' button and ensure it's enabled
        log("⏳ Waiting for 'Continue' button to become enabled...")
        continue_button_xpath = "//button[.//span[contains(text(), 'Continue')]]"
        continue_button = wait.until(EC.presence_of_element_located((By.XPATH, continue_button_xpath)))

        wait_time, interval = 30, 0.3
        elapsed = 0

        while elapsed < wait_time:
            continue_button = driver.find_element(By.XPATH, continue_button_xpath)  # Refresh reference
            is_disabled = continue_button.get_attribute("disabled")
            button_classes = continue_button.get_attribute("class")
            if not is_disabled and 'disabled' not in button_classes:
                log("✅ 'Continue' button is enabled.")
                break
            time.sleep(interval)
            elapsed += interval
        else:
            raise TimeoutException("❌ 'Continue' button did not become enabled in time.")

        # Step 7: Click 'Continue' to proceed
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
        driver.execute_script("arguments[0].click();", continue_button)
        log("🚀 Proceeded to final booking page.")

    except TimeoutException as e:
        log(f"❌ Timeout in player selection flow: {e}")
        raise

    except Exception as e:
        log(f"❌ Unexpected error during player selection: {e}")
        raise

def finalize_booking(driver, wait):
    log("Attempting final booking...")

    try:
        # Target the final "Finalize Reservation" button by its text
        finalize_xpath = "//span[contains(text(), 'Finalize Reservation')]"

        finalize_button = wait.until(EC.presence_of_element_located((By.XPATH, finalize_xpath)))

        # Scroll to the button
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", finalize_button)

        # Optionally: ensure button is enabled (recommended)
        max_wait_time = 10  # seconds
        poll_interval = 0.2
        elapsed_time = 0

        parent_button = finalize_button.find_element(By.XPATH, "./ancestor::button")

        while elapsed_time < max_wait_time:
            is_disabled_attr = parent_button.get_attribute("disabled")
            button_classes = parent_button.get_attribute("class")

            if not is_disabled_attr and 'disabled' not in button_classes:
                log("✅ Finalize Reservation button is now enabled.")
                break

            log("⏳ Finalize Reservation button still disabled, waiting...")
            time.sleep(poll_interval)
            elapsed_time += poll_interval

            # Refresh reference in case of re-render
            finalize_button = driver.find_element(By.XPATH, finalize_xpath)
            parent_button = finalize_button.find_element(By.XPATH, "./ancestor::button")

        else:
            log("❌ Timeout waiting for Finalize Reservation button to become enabled.")
            raise TimeoutException("Finalize Reservation button did not become enabled in time.")

        # Click the finalize button, comment out for testing
        driver.execute_script("arguments[0].click();", parent_button)

        log("🎉 ✅ Booking Success!")

        # Optionally wait to see final confirmation page (optional)
        pause.minutes(1)

    except TimeoutException:
        log("❌ Final booking button not found.")
        raise

# --- MAIN EXECUTION ---
def main():
    driver, wait = setup_driver()

    try:
        login(driver, wait)

        if not wait_until_booking(driver, wait):
            driver.quit()
            return

        select_date(driver, wait)
        select_time(driver, wait)
        select_player(driver, wait)
        finalize_booking(driver, wait)

    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, UnexpectedAlertPresentException) as e:
        log(f"An error occurred during booking flow: {e}")

    except Exception as e:
        log(f"An unexpected error occurred: {e}")

    finally:
        try:
            driver.quit()
        except Exception as e:
            log("Error while quitting the browser: {e}")
        finally:
            driver.__del__ = lambda: None

if __name__ == '__main__':
    st.title('🏌️ Bergen Golf Book Tee Time')
    st.write('Fill in your booking details below:')

    preferred_courses = [
        "Rockleigh R/W 18",
        "Darlington 18",
        "Overpeck 18",
        "Soldier Hill 18",
        "Valley Brook 18",
        "Orchard Hills",
        "Darlington Back 9",
        "Overpeck Back 9",
        "Rockleigh Back 9",
        "Rockleigh Blue 9",
        "Soldier Hill Back 9",
        "Valley Brook 9"
    ]

    # Streamlit form for inputs
    with st.form("booking_form"):
        user = st.text_input('User ID', '9094566')
        password = st.text_input('Password', '', type='password')
        month_and_day = st.text_input('Date (MM/DD)', '04/16')
        player = st.selectbox('Number of Players', ['1', '2', '3', '4'])
        tee_time = st.text_input('Preferred Tee Time', '12:00 PM')
        time_window_minutes = st.text_input('Time Window in Minutes', '45')
        desired_course_name = st.selectbox('Course', preferred_courses)

        # Submit button inside the form — triggers on Enter or click
        run_script = st.form_submit_button('🚀 Run Booking')

    # Move log container to bottom — after inputs
    log_container = st.empty()

    if run_script:
        st.write('Booking in progress... please keep this tab open.')
        try:
            # Assign input values to the variables your script uses
            globals()['user'] = user
            globals()['password'] = password
            globals()['month_and_day'] = month_and_day
            globals()['player'] = player
            globals()['tee_time'] = tee_time
            globals()['desired_course_name'] = desired_course_name
            globals()['time_window_minutes'] = int(time_window_minutes)

            main()  # Run your automation function

            st.success('🎉 Done! Booking process completed. Check the output logs above.')

        except Exception as e:
            st.error(f'Error: {e}')

