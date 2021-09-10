import os
import asyncio
import time
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from enum_bot import BotStatus
from dotenv import load_dotenv


load_dotenv()


def get_headless_options():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                'like Gecko) Chrome/93.0.4577.63 Safari/537.36"')
    chrome_options.binary_location = os.getenv("GOOGLE_CHROME_BIN")
    return chrome_options


async def get_schedule(user_id, email, pwd):
    # Setting options
    chrome_options = get_headless_options()
    try:
        # Apply driver
        driver = webdriver.Chrome(executable_path=os.getenv("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    except RuntimeError:
        raise RuntimeError(BotStatus.START_FAILED)

    try:
        # 1. Do Google login
        driver.get("https://accounts.google.com/signin")
        element_present = EC.presence_of_element_located((By.ID, 'identifierNext'))
        WebDriverWait(driver, 15).until(element_present)
        # 2. Enter email
        x_path = '//*[@id="identifierId"]'
        input_box = driver.find_element_by_xpath(x_path)
        input_box.send_keys(email)
        # 3. Click next
        x_path = '//*[@id ="identifierNext"]'
        button = driver.find_element_by_xpath(x_path)
        button.click()
        # 4. Enter password
        element_present = EC.presence_of_element_located((By.ID, 'passwordNext'))
        WebDriverWait(driver, 15).until(element_present)
        x_path = '//*[@id ="password"]/div[1]/div / div[1]/input'
        input_box = driver.find_element_by_xpath(x_path)
        input_box.send_keys(pwd)
        # 5. Click login
        x_path = '//*[@id ="passwordNext"]'
        button = driver.find_element_by_xpath(x_path)
        button.click()
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'x7WrMb'))
        WebDriverWait(driver, 15).until(element_present)
        if 'myaccount.google.com' not in driver.current_url:
            raise RuntimeError(BotStatus.LOGIN_FAILED)
    except RuntimeError:
        driver.save_screenshot(f'{user_id}.png')
        driver.quit()
        raise RuntimeError(BotStatus.LOGIN_FAILED)
    except NoSuchElementException:
        driver.save_screenshot(f'{user_id}.png')
        driver.quit()
        raise RuntimeError(BotStatus.ELEMENT_CHANGED)
    except TimeoutException:
        driver.save_screenshot(f'{user_id}.png')
        driver.quit()
        raise RuntimeError(BotStatus.TIME_OUT)

    # 6. Navigate to FAP page
    driver.get("https://fap.fpt.edu.vn/")

    try:
        element_present = EC.presence_of_element_located((By.ID, 'ctl00_mainContent_ddlCampus'))
        WebDriverWait(driver, 15).until(element_present)
        # 8. Select campus
        select = Select(driver.find_element_by_id('ctl00_mainContent_ddlCampus'))
        select.select_by_visible_text('FU-Hồ Chí Minh')
        # 9. Click Google login
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'abcRioButtonIcon'))
        WebDriverWait(driver, 15).until(element_present)
        x_path = '/html/body/div/div[2]/div/form/table/tbody/tr[1]/td/div/div/div/div[2]/div/fieldset/div/center/div/div[2]/div/div/div'
        button = driver.find_elements_by_xpath(x_path)
        button[0].click()
        element_present = EC.presence_of_element_located((By.ID, 'ctl00_divUser'))
        WebDriverWait(driver, 15).until(element_present)
        # 10. Navigate to schedule page
        driver.get('https://fap.fpt.edu.vn/Report/ScheduleOfWeek.aspx')
        x_path = '/html/body/div/div[2]/div/form/table/tbody/tr[1]/td/div/table'
        element_present = EC.presence_of_element_located((By.XPATH, x_path))
        WebDriverWait(driver, 15).until(element_present)
        # 11. Set window size
        driver.set_window_size(1000, 1000)
        driver.fullscreen_window()
        element = driver.find_element_by_xpath(x_path)
        # 12. Save & exit
        name = f'{user_id}_{round(time.time() * 1000)}.png'
        png = element.screenshot_as_png
        img = Image.open(BytesIO(png))
        img.save(name)
    except RuntimeError:
        driver.save_screenshot(f'{user_id}.png')
        raise RuntimeError(BotStatus.LOGIN_FAILED)
    except NoSuchElementException:
        driver.save_screenshot(f'{user_id}.png')
        raise RuntimeError(BotStatus.ELEMENT_CHANGED)
    except TimeoutException:
        driver.save_screenshot(f'{user_id}.png')
        raise RuntimeError(BotStatus.TIME_OUT)
    finally:
        driver.quit()
    return BotStatus.END_SUCCESS, name


async def get_schedule_by_token(user_id, access_token):
    if access_token is None or access_token == '':
        raise RuntimeError(BotStatus.LOGIN_FAILED)
    # Setting options
    chrome_options = get_headless_options()
    try:
        # Apply driver
        driver = webdriver.Chrome(executable_path=os.getenv("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    except RuntimeError:
        raise RuntimeError(BotStatus.START_FAILED)

    # 1. Navigate to FAP page
    driver.get("https://fap.fpt.edu.vn/")
    driver.implicitly_wait(15)
    await asyncio.sleep(1)
    # 2. Select campus
    select = Select(driver.find_element_by_id('ctl00_mainContent_ddlCampus'))
    select.select_by_visible_text('FU-Hồ Chí Minh')
    driver.implicitly_wait(15)
    await asyncio.sleep(1)
    # 3. Navigate to page with token
    driver.get("https://fap.fpt.edu.vn/Default.aspx?token=" + access_token)
    driver.implicitly_wait(15)
    await asyncio.sleep(2)
    # 4. Check if token is valid
    if driver.current_url != 'https://fap.fpt.edu.vn/Student.aspx':
        raise RuntimeError(BotStatus.LOGIN_FAILED)
    # 5. Navigate to schedule page
    driver.get('https://fap.fpt.edu.vn/Report/ScheduleOfWeek.aspx')
    driver.implicitly_wait(15)
    # 6. Set window size
    driver.set_window_size(1000, 1000)
    driver.fullscreen_window()
    # 7. Save & exit
    name = f'{user_id}_{round(time.time() * 1000)}.png'
    driver.save_screenshot(name)
    driver.quit()
    return BotStatus.END_SUCCESS, name


async def request_wolfram_alpha(user_id, query):
    # Setting options
    chrome_options = get_headless_options()
    try:
        # Apply driver
        driver = webdriver.Chrome(executable_path=os.getenv("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    except RuntimeError:
        raise RuntimeError(BotStatus.START_FAILED)
    # 1. Navigate to wolfram alpha page
    driver.get("https://www.wolframalpha.com/")
    driver.implicitly_wait(15)

    try:
        # Enter query
        x_path_selector = '/html/body/div/div/div[1]/div/div/div[1]/section/form/div/div/input'
        input_box = driver.find_element_by_xpath(x_path_selector)
        input_box.send_keys(query)

        # Press search
        x_path_selector = '/html/body/div/div/div[1]/div/div/div[1]/section/form/span/button'
        button = driver.find_elements_by_xpath(x_path_selector)
        button[0].click()

        # Click accept cookies
        x_path_selector = '/html/body/div/div/section/button'
        button = driver.find_elements_by_xpath(x_path_selector)
        button[0].click()
    except NoSuchElementException:
        driver.save_screenshot(f'{user_id}.png')
        driver.quit()
        raise RuntimeError(BotStatus.ELEMENT_CHANGED)
    # Set full screen
    driver.set_window_size(1000, 1000)
    driver.fullscreen_window()

    # Get result
    try:
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'Ugj72'))
        WebDriverWait(driver, 15).until(element_present)
        await asyncio.sleep(5)
        x_path_selector = '_2z545'
        elements = driver.find_elements_by_class_name(x_path_selector)
        count = 0
        len_elm = len(elements)
        while len_elm > 0 and count < len_elm:
            element = elements[count]
            png = element.screenshot_as_png
            img = Image.open(BytesIO(png))  # uses PIL library to open image in memory
            name = f'screenshot-{count}.png'
            img.save(name)
            count += 1
            # Do find again
            new_elements = driver.find_elements_by_class_name(x_path_selector)
            if len(new_elements) > len_elm:
                len_elm = len(new_elements)
                elements = new_elements
            yield name
    except TimeoutException:
        driver.save_screenshot(f'{user_id}.png')
        raise RuntimeError(BotStatus.TIME_OUT)
    finally:
        driver.quit()
