from selenium import webdriver
from selenium.webdriver.safari.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pushover_complete import PushoverAPI
import time

# Replace with your Pushover user key and API token
PUSHOVER_USER_KEY = "u9irww7zqjphdivojqyftioch5qzsv"
PUSHOVER_API_TOKEN = "a3841qo2jienfonyfww5kha79g6t72"

def send_notification(title, message):
    try:
        pushover = PushoverAPI(PUSHOVER_API_TOKEN)
        pushover.send_message(PUSHOVER_USER_KEY, message, title=title)
        print(f"Notification sent: {title}")
    except Exception as e:
        print(f"Failed to send notification: {str(e)}")

def get_course_availability(driver, course):
    try:
        # Find the course box
        course_box = driver.find_element(By.XPATH, f"//div[contains(@class, 'course_box') and contains(., '{course}')]")
        
        # Find all sections (lecture sections)
        sections = course_box.find_elements(By.XPATH, ".//div[contains(@class, 'selection_row')]")
        
        available_sections = []
        
        for section in sections:
            # Check if it's a lecture section
            if "Lec" in section.text:
                crn = section.find_element(By.XPATH, ".//span[@class='crn_value']").text
                
                # Check for available seats
                seats_element = section.find_element(By.XPATH, ".//span[contains(@class, 'leftnclear') and contains(., 'Seats:')]")
                if "Full" not in seats_element.text:
                    available_sections.append((crn, "Open seats"))
                    continue
                
                # Check for waitlist
                waitlist_element = section.find_element(By.XPATH, ".//span[contains(@class, 'legend_waitlist')]")
                if "None" not in waitlist_element.text:
                    available_sections.append((crn, "Waitlist"))
        
        return available_sections
    except NoSuchElementException:
        print(f"Could not find course information for {course}")
        return []

def perform_web_task():
    print("Starting web task...")
    
    courses = ["COMP 202", "MATH 133", "COMP 250", "MATH 141"]
    
    try:
        print("Creating Safari WebDriver...")
        driver = webdriver.Safari()
        print("Safari WebDriver created successfully.")
        
        print("Loading webpage...")
        driver.get("https://vsb.mcgill.ca/vsb/criteria.jsp?access=0&lang=en&tip=1&page=results&scratch=0&term=0&sort=none&filters=iiiiiiiii&bbs=&ds=&cams=Distance_Downtown_Macdonald_Off-Campus&locs=any&isrts=&course_0_0=&sa_0_0=&cs_0_0=--+All+--&cpn_0_0=&csn_0_0=&ca_0_0=&dropdown_0_0=al&ig_0_0=0&rq_0_0=")
        print("Webpage loaded successfully.")

        # Wait for and click the 'Continue' button
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Continue']"))).click()
        print("Clicked the Continue button.")

        # Wait for and click the Fall 2024 radio button
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='radterm' and @data-term='202409']"))).click()
        print("Selected Fall 2024 term.")

        time.sleep(2)  # Wait for the page to update

        for course in courses:
            print(f"Entering course: {course}")
            
            # Find and clear the course input field
            course_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "code_number")))
            course_input.clear()
            course_input.send_keys(course)
            
            # Click the 'Select' button
            select_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "addCourseButton")))
            select_button.click()
            
            print(f"Selected course: {course}")
            time.sleep(2)  # Wait for the course to be added

        print("All courses entered and selected.")

        # Click the "Generate Schedules" button
        generate_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "do_search")))
        generate_button.click()
        print("Clicked 'Generate Schedules' button.")

        # Wait for the schedules to be generated
        time.sleep(10)  # Adjust this time as needed

        print("Checking course availability...")
        available_courses = {}
        for course in courses:
            available_sections = get_course_availability(driver, course)
            if available_sections:
                available_courses[course] = available_sections
                print(f"Course {course} is available:")
                for crn, availability_type in available_sections:
                    print(f"  CRN: {crn}, Availability: {availability_type}")
            else:
                print(f"Course {course} is not available")

        if available_courses:
            notification_title = "Course Availability Alert"
            notification_body = "The following courses are available:\n"
            for course, sections in available_courses.items():
                notification_body += f"{course}:\n"
                for crn, availability_type in sections:
                    notification_body += f"  CRN: {crn}, Availability: {availability_type}\n"
            send_notification(notification_title, notification_body)
        else:
            print("No courses are currently available.")

        print("All courses have been checked for availability.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        send_notification("Course Check Error", f"An error occurred while checking course availability: {str(e)}")
    finally:
        if 'driver' in locals():
            print("Closing browser...")
            driver.quit()
            print("Browser closed.")

if __name__ == "__main__":
    perform_web_task()
