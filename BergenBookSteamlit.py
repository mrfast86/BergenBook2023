import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, UnexpectedAlertPresentException
from selenium_stealth import stealth
import pause
from datetime import datetime, date, timedelta
import time
import streamlit as st
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
user = '9094566'
password = 'Cp4iJ30z'
month_and_day = '04/16'  # MM/DD format
player = '4'
tee_time = '12:00 PM'
desired_course_name = "Rockleigh R/W 18"  # Replace with your course!
preferred_courses = [
    "Rockleigh R/W 18",      # 🥇 Top priority
    "Darlington 18",         # 🥈 Second choice
    "Overpeck 18",           # Good 18-hole
    "Soldier Hill 18",
    "Valley Brook 18",
    "Orchard Hills",         # Assuming full course
    # --- Now 9-hole courses ---
    "Darlington Back 9",
    "Overpeck Back 9",
    "Rockleigh Back 9",
    "Rockleigh Blue 9",
    "Soldier Hill Back 9",
    "Valley Brook 9"
]
# --- SETUP CHROME DRIVER ---

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-features=NetworkService')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.binary_location = '/usr/bin/chromium'  # Notice: correct path in Streamlit Cloud

    driver = uc.Chrome(
        options=chrome_options,
        driver_executable_path=ChromeDriverManager().install()
    )

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
        print(f"[Popup] Native alert: {alert.text}")
        alert.accept()
        print("[Popup] Native alert dismissed.")
        return
    except Exception:
        pass

    try:
        alert_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, "btnAlertOk"))
        )
        alert_message = driver.find_element(By.CLASS_NAME, "modal-body").text
        print(f"[Popup] Old popup: {alert_message}")
        alert_button.click()
        print("[Popup] Old popup dismissed.")
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
            print(f"[Popup] MatDialog: {dialog_content}")
        except NoSuchElementException:
            print("[Popup] MatDialog appeared, no content found.")

        try:
            close_button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", close_button)

        print("[Popup] MatDialog dismissed.")
    except Exception:
        pass

# --- LOGIN FLOW ---
def login(driver, wait):
    print("Opening booking page...")
    driver.get('https://bergencountygolf.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23')

    dismiss_popup(driver, wait)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'mat-dialog-container')))

    print("Clicking Sign In...")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Sign In')]"))).click()

    print("Entering username...")
    wait.until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys(user)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    print("Entering password...")
    wait.until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    print("✅ Logged in successfully.")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    dismiss_popup(driver, wait)

# --- WAIT UNTIL BOOKING TIME ---
def wait_until_booking(driver, wait):
    today = date.today()
    date_of_play = datetime(today.year, int(month_and_day[:2]), int(month_and_day[3:]), 0, 0)
    booking_time = (date_of_play - timedelta(days=7)).replace(hour=19, minute=0, second=0, microsecond=0)

    print(f"📅 Date of play: {date_of_play}")
    print(f"🕖 Booking initiation time: {booking_time}")

    # (Optional) If testing, comment out
    if booking_time < datetime.now():
        print(f"⚠️ Booking initiation time already passed: {booking_time}")
        return False

    # Step 1: Pre-wait loop until very close to booking time
    while True:
        now = datetime.now()
        seconds_left = (booking_time - now).total_seconds()
        dismiss_popup(driver, wait)

        if seconds_left <= 10:
            print("⏱️ Less than 10 seconds to go — entering tight wait...")
            break
        elif seconds_left > 300:
            mins = int(seconds_left // 60)
            secs = int(seconds_left % 60)
            print(f"🧩 Waiting: {mins} min {secs} sec remaining until booking...")
            time.sleep(60)
        else:
            print(f"🧩 Close: {int(seconds_left)} seconds left until booking...")
            time.sleep(5)

    # Step 2: Final tight wait
    while datetime.now() < booking_time:
        time.sleep(0.05)

    print(f"🚀 Booking time reached: {datetime.now()} — Starting course selection...")

    try:
        dismiss_popup(driver, wait)
        # Step 3: Open the course selection dropdown
        dropdown_xpath = "//div[contains(@class, 'mat-select-value') and .//span[contains(text(), 'Multiple Courses Selected')]]"
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)
        print("✅ Course dropdown opened.")

        # Step 4: Deselect all courses
        deselect_all_xpath = "//span[contains(@class, 'mat-option-text') and normalize-space(text())='Deselect All']"
        deselect_all_option = wait.until(EC.element_to_be_clickable((By.XPATH, deselect_all_xpath)))
        driver.execute_script("arguments[0].click();", deselect_all_option)
        print("✅ 'Deselect All' clicked.")

        # Step 5: Select your desired course
        course_option_xpath = f"//span[contains(@class, 'mat-option-text') and normalize-space(text())='{desired_course_name}']"
        course_option = wait.until(EC.element_to_be_clickable((By.XPATH, course_option_xpath)))
        driver.execute_script("arguments[0].click();", course_option)
        print(f"✅ Course '{desired_course_name}' selected.")

        # ✅ Step 6: Click the "Done" button to close dropdown
        done_button_xpath = "//button[.//span[normalize-space(text())='Done']]"
        done_button = wait.until(EC.element_to_be_clickable((By.XPATH, done_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", done_button)
        driver.execute_script("arguments[0].click();", done_button)
        print("✅ 'Done' button clicked to finalize course selection.")

        return True

    except TimeoutException as e:
        print(f"❌ Failed during course selection flow: {e}")
        return False

# --- BOOKING FLOW ---
def select_date(driver, wait):
    print(f"Selecting date: {month_and_day}")

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
        print(f"✅ Date {month_and_day} clicked normally.")
    except ElementClickInterceptedException:
        print(f"⚠️ Normal click blocked. Trying JavaScript click...")
        element = driver.find_element(By.XPATH, date_xpath)
        driver.execute_script("arguments[0].click();", element)
        print(f"✅ Date {month_and_day} clicked with JavaScript.")
    except TimeoutException:
        print(f"❌ Date {month_and_day} not found.")
        days = driver.find_elements(By.CLASS_NAME, "day-background-upper")
        for d in days:
            print(f" - Available day: {d.text}")
        raise

def select_time(driver, wait):
    print(f"🎯 Selecting time: {tee_time}")

    # Parse the desired time
    hour, minute_ampm = tee_time.split(':')
    minute, ampm = minute_ampm.strip().split(' ')
    today = date.today()
    booking_date = f"{today.year}-{month_and_day[:2]}-{month_and_day[3:]}"
    booking_date = datetime.strptime(booking_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    # Format 24-hour time
    hour_24 = int(hour)
    if ampm.upper() == "PM" and hour_24 != 12:
        hour_24 += 12
    if ampm.upper() == "AM" and hour_24 == 12:
        hour_24 = 0
    time_attr = f"{booking_date}T{hour_24:02}:00:00"

    # Step 1: Wait for the tee time grid to load
    tee_time_grid_xpath = "//div[contains(@class, 'teetimetable')]"
    try:
        print("⏳ Waiting for tee time grid to load...")
        wait.until(EC.presence_of_element_located((By.XPATH, tee_time_grid_xpath)))
        print("✅ Tee time grid loaded.")
    except TimeoutException:
        print("❌ Tee time grid did not load in time.")
        raise

    # Step 2: Try clicking any "Show more" buttons (non-blocking)
    try:
        show_more_buttons = driver.find_elements(By.XPATH, "//span[contains(normalize-space(.), 'Show more')]/ancestor::button")
        for button in show_more_buttons:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            driver.execute_script("arguments[0].click();", button)
            print("✅ Clicked 'Show more' button.")
            time.sleep(0.5)  # Give DOM a moment to expand
    except Exception as e:
        print(f"⚠️ Error while checking 'Show more' buttons: {e}")

    # Step 3: Find the clickable parent of the desired time
    clickable_parent_xpath = f"//time[@datetime='{time_attr}']/ancestor::div[contains(@class, 'teetimetableDateTime')]"
    try:
        print(f"⏳ Waiting for tee time: {time_attr}")
        clickable_element = wait.until(EC.element_to_be_clickable((By.XPATH, clickable_parent_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable_element)
        driver.execute_script("arguments[0].click();", clickable_element)
        print(f"✅ Tee time {tee_time} selected.")
    except TimeoutException:
        print(f"❌ Desired time {tee_time} not found or not clickable.")
        raise

def select_player(driver, wait):
    print("🎯 Starting player selection flow...")

    try:
        # Step 1: Open player selection popup
        print("🧩 Clicking 'Edit' to open player selection...")
        edit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Edit')]")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_button)
        driver.execute_script("arguments[0].click();", edit_button)

        # Step 2: Wait for popup and player buttons to load
        print("⏳ Waiting for player selection popup to load...")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mat-bottom-sheet-container")))

        print("⏳ Waiting for player toggle buttons to load inside popup...")
        player_button_xpath = (
            f"//mat-bottom-sheet-container//button[contains(@class, 'mat-button-toggle-button')]//span[contains(text(), '{player}')]/ancestor::button"
        )
        wait.until(EC.presence_of_element_located((By.XPATH, player_button_xpath)))
        print("✅ Player selection popup is ready.")

        # Step 3: Select desired player
        print(f"🧩 Selecting player: {player}")
        player_button = wait.until(EC.element_to_be_clickable((By.XPATH, player_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", player_button)
        driver.execute_script("arguments[0].click();", player_button)
        print(f"✅ Player {player} clicked.")

        # Step 4: Confirm selection via aria-pressed
        print("⏳ Confirming player selection (aria-pressed='true')...")
        max_wait_time, poll_interval = 10, 0.2
        elapsed_time = 0

        player_button_xpath = f"//mat-bottom-sheet-container//button[contains(@class, 'mat-button-toggle-button')]//span[contains(text(), '{player}')]/ancestor::button"

        while elapsed_time < max_wait_time:
            try:
                # Refresh the button reference every time
                player_button_fresh = driver.find_element(By.XPATH, player_button_xpath)
                aria_pressed = player_button_fresh.get_attribute("aria-pressed")

                if aria_pressed == "true":
                    print(f"✅ Player {player} selection confirmed (aria-pressed='true').")
                    break

            except Exception as e:
                # Optionally print: element not found (can happen during re-render)
                print(f"🔄 Waiting for player button to re-appear... {e}")

            time.sleep(poll_interval)
            elapsed_time += poll_interval
        else:
            raise TimeoutException(f"❌ Player {player} selection not confirmed in time.")

        # Step 5: Click Submit
        print("🧩 Submitting player selection...")
        submit_button_xpath = "//mat-bottom-sheet-container//span[contains(text(), 'Submit')]/ancestor::button"
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, submit_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        driver.execute_script("arguments[0].click();", submit_button)
        print("✅ Player selection submitted.")

        # Step 6: Wait for 'Continue' button and ensure it's enabled
        print("⏳ Waiting for 'Continue' button to become enabled...")
        continue_button_xpath = "//button[.//span[contains(text(), 'Continue')]]"
        continue_button = wait.until(EC.presence_of_element_located((By.XPATH, continue_button_xpath)))

        wait_time, interval = 30, 0.3
        elapsed = 0

        while elapsed < wait_time:
            continue_button = driver.find_element(By.XPATH, continue_button_xpath)  # Refresh reference
            is_disabled = continue_button.get_attribute("disabled")
            button_classes = continue_button.get_attribute("class")
            if not is_disabled and 'disabled' not in button_classes:
                print("✅ 'Continue' button is enabled.")
                break
            time.sleep(interval)
            elapsed += interval
        else:
            raise TimeoutException("❌ 'Continue' button did not become enabled in time.")

        # Step 7: Click 'Continue' to proceed
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
        driver.execute_script("arguments[0].click();", continue_button)
        print("🚀 Proceeded to final booking page.")

    except TimeoutException as e:
        print(f"❌ Timeout in player selection flow: {e}")
        raise

    except Exception as e:
        print(f"❌ Unexpected error during player selection: {e}")
        raise

def finalize_booking(driver, wait):
    print("Attempting final booking...")

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
                print("✅ Finalize Reservation button is now enabled.")
                break

            print("⏳ Finalize Reservation button still disabled, waiting...")
            time.sleep(poll_interval)
            elapsed_time += poll_interval

            # Refresh reference in case of re-render
            finalize_button = driver.find_element(By.XPATH, finalize_xpath)
            parent_button = finalize_button.find_element(By.XPATH, "./ancestor::button")

        else:
            print("❌ Timeout waiting for Finalize Reservation button to become enabled.")
            raise TimeoutException("Finalize Reservation button did not become enabled in time.")

        # Click the finalize button, comment out for testing
        driver.execute_script("arguments[0].click();", parent_button)

        print("🎉 ✅ Booking Success!")

        # Optionally wait to see final confirmation page (optional)
        pause.minutes(1)

    except TimeoutException:
        print("❌ Final booking button not found.")
        raise

# --- MAIN EXECUTION ---
def main():
    log("✅ Starting main() function...")
    driver, wait = setup_driver()
    log("✅ Driver and wait object created.")

    try:
        log("🚀 Starting login flow...")
        login(driver, wait)

        if not wait_until_booking(driver, wait):
            driver.quit()
            return

        select_date(driver, wait)
        select_time(driver, wait)
        select_player(driver, wait)
        finalize_booking(driver, wait)

    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, UnexpectedAlertPresentException) as e:
        print("An error occurred during booking flow:", e)

    except Exception as e:
        print("An unexpected error occurred:", e)

    finally:
        try:
            driver.quit()
        except Exception as e:
            print("Error while quitting the browser:", e)
        finally:
            driver.__del__ = lambda: None

if __name__ == '__main__':
    st.title('🏌️ BergenBook Auto Tee Time')
    st.write('Fill in your booking details below:')

    user = st.text_input('User ID', '9094566')
    password = st.text_input('Password', '', type='password')
    month_and_day = st.text_input('Date (MM/DD)', '04/16')
    player = st.selectbox('Number of Players', ['1', '2', '3', '4'])
    tee_time = st.text_input('Preferred Tee Time', '12:00 PM')

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
    desired_course_name = st.selectbox('Course', preferred_courses)

    run_script = st.button('🚀 Run Booking')

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

            main()  # Run your existing automation function

            st.success('🎉 Done! Booking process completed. Check the output logs above.')

        except Exception as e:
            st.error(f'Error: {e}')
