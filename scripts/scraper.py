# -*- coding: utf8 -*-
import sys
import time
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException
from selenium.common.exceptions import TimeoutException
from .manager import DataManager

# Page elements class names
COMPANY_REVIEWS_BUTTON = 'section-rating-term-list'
USER_REVIEWS_BUTTON = 'section-tab-bar-tab-unselected'
REVIEW = 'section-review-content'
REVIEW_TITLE = 'section-review-title'
REVIEW_STARS = 'section-review-stars'
REVIEW_COMPANY_NAME = 'section-review-title-consistent-with-review-text'
REVIEW_COMPANY_ADDRESS = 'section-review-subtitle-nowrap'
SPINNER = 'section-loading-spinner'
SCROLLBOX = 'section-scrollbox'

# Scrollbox scrolling script
SCROLLING_SCRIPT = 'arguments[0].scrollTop = arguments[0].scrollHeight'

# Timeout params
SCROLL_TIMEOUT = 4
WAIT_TIMEOUT = 10

# Scraper process statuses
SUCCESS = 'SUCCESS'
ERROR = 'ERROR'
DRIVER_ERROR = 'DRIVER ERROR'
WEB_ELEMENT_ERROR = 'WEB ELEMENT ERROR'


def soup_parsing(driver: Chrome, class_name: str) -> list:
    response = BeautifulSoup(driver.page_source, 'html.parser')
    return response.find_all('div', class_=class_name)


def scroll(driver: Chrome, wait: WebDriverWait):
    scroll_div = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, SCROLLBOX)))
    reviews_count = len(driver.find_elements_by_class_name(REVIEW))
    timeout = time.time() + SCROLL_TIMEOUT

    while time.time() < timeout:
        driver.execute_script(SCROLLING_SCRIPT, scroll_div)
        time.sleep(1)

        scrolled_reviews_count = len(driver.find_elements_by_class_name(REVIEW))

        if reviews_count < scrolled_reviews_count:
            reviews_count = scrolled_reviews_count
            timeout = time.time() + SCROLL_TIMEOUT


class Scraper:
    def __init__(self, debug: bool):
        self.data_manager = DataManager()
        self.driver_options = Options()
        if not debug:
            self.driver_options.add_argument('--headless')

    def driver_tools(self) -> list:
        driver = Chrome(options=self.driver_options)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        return [driver, wait]

    def get_users_data(self) -> dict:
        data = {}
        urls = self.data_manager.get_urls()

        for url in urls:
            driver, wait = self.driver_tools()
            driver.get(url)

            try:
                reviews_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, COMPANY_REVIEWS_BUTTON)))
                reviews_button.click()

                spinner_offset = wait.until(
                    EC.visibility_of_element_located((By.CLASS_NAME, SPINNER))).get_property('offsetTop')

                if spinner_offset != 0:
                    scroll(driver, wait)

                reviews = soup_parsing(driver, REVIEW)

                for review in reviews:
                    user_link = review.find('a')['href']
                    user_name = review.find('div', class_=REVIEW_TITLE).find('span').text
                    data[user_link] = user_name

                process_status = SUCCESS

            except InvalidSessionIdException:
                process_status = DRIVER_ERROR

            except TimeoutException:
                process_status = WEB_ELEMENT_ERROR

            except Exception as ex:
                process_status = f'{ERROR}\n{ex}'

            finally:
                driver.close()
                print(f'users list extracting from {url} finished with {process_status}')

        return data

    def scrape_data(self):
        users_data = self.get_users_data()
        users_count = len(users_data)
        driver, wait = self.driver_tools()

        for i in enumerate(users_data.items(), 1):
            user_link = i[1][0]
            user_name = i[1][1]
            user_number = i[0]

            driver.get(user_link)

            try:
                reviews_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, USER_REVIEWS_BUTTON)))
                reviews_button.click()

                wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, REVIEW)))
                spinner_offset = driver.find_element_by_class_name(SPINNER).get_property('offsetTop')

                if spinner_offset != 0:
                    scroll(driver, wait)

                reviews = soup_parsing(driver, REVIEW)

                for review in reviews:
                    place_name = review.find('div', class_=REVIEW_COMPANY_NAME).find('span').text
                    place_address = review.find('div', class_=REVIEW_COMPANY_ADDRESS).find('span').text
                    stars_count = int(review.find('span', class_=REVIEW_STARS)['aria-label'][1])
                    self.data_manager.write_data([user_name, user_link, place_name, place_address, stars_count])

                process_status = SUCCESS

            except InvalidSessionIdException:
                driver, wait = self.driver_tools()
                process_status = DRIVER_ERROR

            except TimeoutException:
                process_status = WEB_ELEMENT_ERROR

            except Exception as ex:
                process_status = f'{ERROR}\n{ex}'

            finally:
                print(f'user({user_number}/{users_count}) {user_name} data processing finished with {process_status}')

        driver.close()
