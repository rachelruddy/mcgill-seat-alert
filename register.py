from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from pushover_complete import PushoverAPI
from tenacity import retry, stop_after_attempt, wait_fixed
import os
import time
import json
import argparse
import logging
from requests.exceptions import RequestException

# Use environment variables for Pushover credentials
PUSHOVER_USER_KEY = os.environ.get('PUSHOVER_USER_KEY')
PUSHOVER_API_TOKEN = os.environ.get('PUSHOVER_API_TOKEN')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_config():
    parser = argparse.ArgumentParser(description='Check course availability at McGill')
    parser.add_argument('--config', default='config.json', help='Path to the configuration file')
    args = parser.parse_args()

    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Config file not found: {args.config}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error reading config file: {args.config}")
        return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def load_webpage(driver, url):
    driver.get(url)
    logging.info("Webpage loaded successfully.")

def send_notification(title, message):
    try:
        pushover = PushoverAPI(PUSHOVER_API_TOKEN)
        pushover.send_message(PUSHOVER_USER_KEY, message, title=title)
        logging.info(f"Notification sent: {title}")
    except Exception as e:
        logging.error(f"Failed to send notification: {str(e)}")

def scroll_to_element(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()

def get_course_availability(driver, course):
    try:
        course_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//div[contains(@class, 'course_box') and contains(., '{course}')]"))
        )
        scroll_to_element(driver, course_box)
        
        sections = course_box.find_elements(By.XPATH, ".//div[contains(@class, 'selection_row')]")
        
        available_sections = []
        
        for section in sections:
            if "Lec" in section.text:
                crn = section.find_element(By.XPATH, ".//span[@class='crn_value']").text
                
                seats_element = section.find_element(By.XPATH, ".//span[contains(@class, 'leftnclear') and contains(., 'Seats:')]")
                if "Full" not in seats_element.text:
                    available_sections.append((crn, "Open seats"))
                    continue
                
                waitlist_element = section.find_element(By.XPATH, ".//span[contains(@class, 'legend_waitlist')]")
                if "None" not in waitlist_element.text:
                    available_sections.append((crn, "Waitlist"))
        
        return available_sections
    except Exception as e:
        logging.error(f"Error checking availability for {course}: {str(e)}")
        return []

def perform_web_task():
    logging.info("Starting web task...")
    
    config = get_config()
    if not config:
        return

    courses = config.get('courses', [])
    term = config.get('term', '202409')  # Default to Fall 2024 if not specified

    if not courses:
        logging.info("No courses to check. Exiting.")
        return

    logging.info(f"Checking availability for courses: {courses}")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        logging.info("Creating Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(800, 1080)
        logging.info("Chrome WebDriver created successfully.")
        
        load_webpage(driver, "https://vsb.mcgill.ca/vsb/criteria.jsp?access=0&lang=en&tip=1&page=results&scratch=0&term=0&sort=none&filters=iiiiiiiii&bbs=&ds=&cams=Distance_Downtown_Macdonald_Off-Campus&locs=any&isrts=&course_0_0=&sa_0_0=&cs_0_0=--+All+--&cpn_0_0=&csn_0_0=&ca_0_0=&dropdown_0_0=al&ig_0_0=0&rq_0_0=")
        
        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Continue']")))
        scroll_to_element(driver, continue_button)
        continue_button.click()
        logging.info("Clicked the Continue button.")

        term_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//input[@name='radterm' and @data-term='{term}']")))
        scroll_to_element(driver, term_button)
        term_button.click()
        logging.info(f"Selected term: {term}")

        time.sleep(2)  # Wait for the page to update

        for course in courses:
            logging.info(f"Entering course: {course}")
            
            course_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "code_number")))
            scroll_to_element(driver, course_input)
            course_input.clear()
            course_input.send_keys(course)
            
            select_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "addCourseButton")))
            scroll_to_element(driver, select_button)
            select_button.click()
            
            logging.info(f"Selected course: {course}")
            time.sleep(2)  # Wait for the course to be added

        logging.info("All courses entered and selected.")

        generate_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "do_search")))
        scroll_to_element(driver, generate_button)
        generate_button.click()
        logging.info("Clicked 'Generate Schedules' button.")

        time.sleep(10)  # Wait for the schedules to be generated

        logging.info("Checking course availability...")
        available_courses = {}
        for course in courses:
            available_sections = get_course_availability(driver, course)
            if available_sections:
                available_courses[course] = available_sections
                logging.info(f"Course {course} is available:")
                for crn, availability_type in available_sections:
                    logging.info(f"  CRN: {crn}, Availability: {availability_type}")
            else:
                logging.info(f"Course {course} is not available")

        if available_courses:
            notification_title = "Course Availability Alert"
            notification_body = "The following courses are available:\n"
            for course, sections in available_courses.items():
                notification_body += f"{course}:\n"
                for crn, availability_type in sections:
                    notification_body += f"  CRN: {crn}, Availability: {availability_type}\n"
            send_notification(notification_title, notification_body)
        else:
            logging.info("No courses are currently available.")

        logging.info("All courses have been checked for availability.")

    except RequestException as e:
        logging.error(f"Network error occurred: {str(e)}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        send_notification("Course Check Error", f"An error occurred while checking course availability: {str(e)}")
    finally:
        if 'driver' in locals():
            logging.info("Closing browser...")
            driver.quit()
            logging.info("Browser closed.")

if __name__ == "__main__":
    perform_web_task()