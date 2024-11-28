import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pause
from datetime import datetime, date

# Replace these values with your actual ones
user = '9094566\n'
password = 'Cp4iJ30z\n'
month_and_day = '05/07'  # MM/DD
player = '1'
course = 'DarlingtonGCV3/(S(rg3vqwjursy2tgg3xhm0reyj))/Account/nLogOn'
teeTime = '5:00 PM'

# Initialize Chrome driver with undetected_chromedriver
driver = uc.Chrome()

try:
    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run Chrome in headless mode

    driver.get('https://e.cps.golf/' + course)
    todays_date = date.today()

    # --- LOGIN ---
    wait = WebDriverWait(driver, 20)
    wait.until(EC.visibility_of_element_located((By.NAME, 'Password'))).send_keys(password)
    wait.until(EC.visibility_of_element_located((By.ID, 'UserName'))).send_keys(user)

    # --- WAIT UNTIL TIME ---
    date_to_book = datetime(todays_date.year, int(month_and_day[:2]), int(month_and_day[3:]), 19, 00)
    if date_to_book < datetime.now():
        print("Date must be in the future: ", date_to_book)
        exit()

    print("Current date: ", todays_date)

    # If more than 5 minutes away to 7PM, refresh after 5 minutes to keep session alive
    booking_attempt_initiation_time = datetime(datetime.now().year, datetime.now().month, int(month_and_day[3:])-7, 19, 00)
    print("Booking initiation time: ", booking_attempt_initiation_time)
    total_time_until_initiation_time_in_mins = (booking_attempt_initiation_time - datetime.now()).total_seconds() / 60
    total_hours_left = int(total_time_until_initiation_time_in_mins / 60)
    total_minutes_left = total_time_until_initiation_time_in_mins % 60

    while total_time_until_initiation_time_in_mins > 5:
        print("refreshing every 5 mins, " + str(total_hours_left) + " hours and " + str(
            total_minutes_left) + " more minutes til 7PM of initiation time")
        pause.minutes(5)
        driver.refresh()
        total_time_until_initiation_time_in_mins -= 5
        total_hours_left = int(total_time_until_initiation_time_in_mins / 60)
        total_minutes_left = total_time_until_initiation_time_in_mins % 60

    pause.until(booking_attempt_initiation_time)

    # --- SELECT DATE ---
    driver.execute_script("TabClick('" + month_and_day + "/2023')")

    # --- SELECT TIME ---
    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//div[@teetime='" + teeTime + "']/div/a/div/div/div/h3/span"))).click()

    # --- SELECT PLAYER ---
    wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@value='" + player + "']"))).click()
    wait.until(EC.visibility_of_element_located((By.XPATH, "//div[3]/button[2]"))).click()

    # --- BOOK ---
    wait.until(EC.visibility_of_element_located((By.ID, "btnBook"))).click()

    print("Booking Success!")
except Exception as e:
    print("An error occurred:", e)
finally:
    # Quit Chrome driver manually
    try:
        driver.quit()
    except Exception as e:
        print("An error occurred while quitting Chrome driver:", e)
