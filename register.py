from selenium import webdriver
from selenium.webdriver.safari.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

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

        # Wait for the schedules to be generated (you may need to adjust this time)
        time.sleep(10)

        print("Schedules generated.")
        
        # Wait for user input before closing the browser
        input("Press Enter to close the browser...")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            print("Closing browser...")
            driver.quit()
            print("Browser closed.")

if __name__ == "__main__":
    perform_web_task()
