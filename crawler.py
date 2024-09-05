from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CustomCrawler:
    def __init__(self, search_term):
        self.search_term = search_term
        self.base_url = 'https://www.icama.cn/BasicdataSystem/pesticideRegistrationEn/queryselect_en.do'
        self.total_items_scraped = 0
        self.driver = None
        self.current_page = 1

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

    def run(self, progress_callback=None):
        self.setup_driver()
        try:
            self.driver.get(self.base_url)
            self.search_and_submit()
            
            all_data = []
            while True:
                items_scraped, page_data = self.scrape_page()
                all_data.extend(page_data)
                self.total_items_scraped += items_scraped
                
                if progress_callback:
                    progress_callback(f"Scraped page {self.current_page}, total items: {self.total_items_scraped}")
                
                if not self.next_page():
                    logging.info("No more pages. Scraping completed.")
                    break
            
            logging.info(f"Total items scraped across all pages: {self.total_items_scraped}")
            return all_data
        except Exception as e:
            logging.error(f"An error occurred during crawling: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def search_and_submit(self):
        try:
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#searchForm > div.search_table > table > tbody > tr:nth-child(3) > td.t1 > input[type=text]"))
            )
            search_input.send_keys(self.search_term)
            
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "#btnSubmit")
            submit_button.click()
        except Exception as e:
            logging.error(f"Error in search_and_submit: {str(e)}")
            raise

    def scrape_item(self, link_selector):
        try:
            link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, link_selector))
            )
            self.driver.execute_script("arguments[0].click();", link)
            
            iframe = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#jbox-iframe"))
            )
            self.driver.switch_to.frame(iframe)
            
            data = {}
            data['registered_number'] = self.get_table_data("Registered number：")
            data['first_prove'] = self.get_table_data("FirstProve：")
            data['period'] = self.get_table_data("Period：")
            data['product_name'] = self.get_table_data("ProductName：")
            data['toxicity'] = self.get_table_data("Toxicity：")
            data['formulation'] = self.get_table_data("Formulation：")
            data['registration_certificate_holder'] = self.get_table_data("Registration certificate holder：")
            data['remark'] = self.get_table_data("Remark：")

            active_ingredients = []
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table:nth-of-type(2) tr")
            for row in rows[2:]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) == 2:
                    active_ingredients.append({
                        "ingredient": cols[0].text.strip(),
                        "content": cols[1].text.strip()
                    })
            data['active_ingredients'] = active_ingredients
            
            self.driver.switch_to.default_content()
            
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#jbox > table > tbody > tr:nth-child(2) > td:nth-child(2) > div > a"))
            )
            self.driver.execute_script("arguments[0].click();", close_button)
            
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "#jbox-iframe"))
            )
            
            return data
        except Exception as e:
            logging.error(f"Error scraping item: {str(e)}")
            return None

    def get_table_data(self, label):
        try:
            element = self.driver.find_element(By.XPATH, f"//td[contains(text(), '{label}')]/following-sibling::td")
            return element.text.strip()
        except NoSuchElementException:
            return ""

    def scrape_page(self):
        items_scraped = 0
        page_data = []
        for i in range(2, 22):
            link_selector = f"#tab > tbody > tr:nth-child({i}) > td.t3 > span > a"
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, link_selector))
                )
            except TimeoutException:
                logging.info(f"No more items found after item {i-2}")
                break

            logging.info(f"Scraping item {i-1}")
            data = self.scrape_item(link_selector)
            if data:
                page_data.append(data)
                items_scraped += 1
            else:
                logging.warning(f"Failed to scrape item {i-1}")
        
        logging.info(f"Total items scraped on this page: {items_scraped}")
        return items_scraped, page_data

    def next_page(self):
        try:
            logging.info("Attempting to navigate to the next page")
            
            pagination = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.web_ser_body_right_main_search > div"))
            )
            logging.info("Pagination element found")
            
            next_page_links = self.driver.find_elements(By.XPATH, ".//a[contains(text(), '下一页')]")
            if not next_page_links or "disabled" in next_page_links[0].get_attribute("class"):
                logging.info("Next page link is not available or disabled. This is the last page.")
                return False
            
            next_page_link = next_page_links[0]
            logging.info("Next page link found")
            
            current_page = int(pagination.find_element(By.XPATH, ".//li[@class='active']/a").text)
            logging.info(f"Current page: {current_page}")
            
            self.driver.execute_script("arguments[0].click();", next_page_link)
            logging.info("Clicked next page link")
            
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda d: int(d.find_element(By.XPATH, "//li[@class='active']/a").text) > current_page
                )
                logging.info("Page change detected")
                
                self.current_page += 1
                logging.info(f"Successfully moved to page {self.current_page}")
                return True
            except TimeoutException:
                logging.info("Page did not change. This might be the last page.")
                return False
            
            time.sleep(5)
        
        except Exception as e:
            logging.error(f"Unexpected error in next_page function: {str(e)}")
            return False

def main(search_term, progress_callback=None):
    crawler = CustomCrawler(search_term)
    return crawler.run(progress_callback)

if __name__ == "__main__":
    main('Dimethoate')