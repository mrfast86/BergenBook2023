import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pause
from datetime import datetime
from datetime import date

#  ---------- EDIT ----------
user = '9094566\n'  # replace user
password = 'Cp4iJ30z\n'  # replace password
#month = '11' # future month currently not supported
month_and_day = '04/22' # MM/DD
player = '1'
# course 
# DarlingtonGCV3/DarlingtonGCV3/(S(rg3vqwjursy2tgg3xhm0reyj))/Account/nLogOn - darlington
# 2 - orchard hills
# 3 - overpeck
# 4 - rockleigh
# 5 - soldier hill
# 6 - valley brook
course = 'DarlingtonGCV3/(S(rg3vqwjursy2tgg3xhm0reyj))/Account/nLogOn'
teeTime = '5:00 PM'
#  ---------- EDIT ----------
driver = uc.Chrome(use_subprocess=True)
wait = WebDriverWait(driver, 20)
driver.get('https://e.cps.golf/' + course)
todays_date = date.today()
# --- LOGIN ---
wait.until(EC.visibility_of_element_located(
    (By.NAME, 'Password'))).send_keys(password)
wait.until(EC.visibility_of_element_located(
    (By.ID, 'UserName'))).send_keys(user)

# --- WAIT UNTIL TIME ---
date_to_book = datetime(todays_date.year, int(month_and_day[:2]), int(month_and_day[3:]), 19, 00) 
if date_to_book < datetime.now():
    print("Date must be in the future: ", date_to_book)
    exit()

print("Current date: ", todays_date)

#If more than 5 minutes away to 7PM, refresh after 5 minutes to keep session alive
booking_attempt_initiation_time = datetime(datetime.now().year, datetime.now().month, int(month_and_day[3:])-7, 19, 00)
print("Booking initiation time: ", booking_attempt_initiation_time)
total_time_until_initiation_time_in_mins = (booking_attempt_initiation_time - datetime.now()).total_seconds()/60
total_hours_left = int(total_time_until_initiation_time_in_mins/60)
total_minutes_left = total_time_until_initiation_time_in_mins % 60

while total_time_until_initiation_time_in_mins > 5:
    print("refreshing every 5 mins, " + str(total_hours_left) + " hours and " + str(total_minutes_left) + " more minutes til 7PM of initiation time")
    pause.minutes(5)
    driver.refresh()
pause.until(booking_attempt_initiation_time)
# --- SELECT DATE ---
driver.execute_script("TabClick('"+month_and_day+"/2023')")

# --- SELECT TIME ---
wait.until(EC.visibility_of_element_located(
    (By.XPATH, "//div[@teetime='"+teeTime+"']/div/a/div/div/div/h3/span"))).click()

# --- SELECT PLAYER ---
wait.until(EC.visibility_of_element_located(
    (By.XPATH, "//a[@value='"+player+"']"))).click()
wait.until(EC.visibility_of_element_located(
    (By.XPATH, "//div[3]/button[2]"))).click()

# --- BOOK ---
wait.until(EC.visibility_of_element_located(
    (By.ID, "btnBook"))).click()

print("Booking Success!")
