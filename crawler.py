from playwright.async_api import async_playwright
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CustomCrawler:
    def __init__(self, search_term):
        self.search_term = search_term
        self.base_url = 'https://www.icama.cn/BasicdataSystem/pesticideRegistrationEn/queryselect_en.do'
        self.total_items_scraped = 0
        self.current_page = 1

    def run(self, progress_callback=None):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(self.base_url)
                self.search_and_submit(page)
                
                all_data = []
                while True:
                    items_scraped, page_data = self.scrape_page(page)
                    all_data.extend(page_data)
                    self.total_items_scraped += items_scraped
                    
                    if progress_callback:
                        progress_callback(f"Scraped page {self.current_page}, total items: {self.total_items_scraped}")
                    
                    if not self.next_page(page):
                        logging.info("No more pages. Scraping completed.")
                        break
                
                logging.info(f"Total items scraped across all pages: {self.total_items_scraped}")
                return all_data
            except Exception as e:
                logging.error(f"An error occurred during crawling: {str(e)}")
                return []
            finally:
                browser.close()

    def search_and_submit(self, page):
        try:
            page.fill("#searchForm > div.search_table > table > tbody > tr:nth-child(3) > td.t1 > input[type=text]", self.search_term)
            page.click("#btnSubmit")
            page.wait_for_load_state('networkidle')
        except Exception as e:
            logging.error(f"Error in search_and_submit: {str(e)}")
            raise

    def scrape_item(self, page, link_selector):
        try:
            page.click(link_selector)
            page.wait_for_selector("#jbox-iframe")
            
            frame = page.frame_locator("#jbox-iframe").first
            
            data = {}
            data['registered_number'] = self.get_table_data(frame, "Registered number：")
            data['first_prove'] = self.get_table_data(frame, "FirstProve：")
            data['period'] = self.get_table_data(frame, "Period：")
            data['product_name'] = self.get_table_data(frame, "ProductName：")
            data['toxicity'] = self.get_table_data(frame, "Toxicity：")
            data['formulation'] = self.get_table_data(frame, "Formulation：")
            data['registration_certificate_holder'] = self.get_table_data(frame, "Registration certificate holder：")
            data['remark'] = self.get_table_data(frame, "Remark：")

            active_ingredients = []
            rows = frame.locator("table:nth-of-type(2) tr").all()[2:]
            for row in rows:
                cols = row.locator("td").all()
                if len(cols) == 2:
                    active_ingredients.append({
                        "ingredient": cols[0].inner_text().strip(),
                        "content": cols[1].inner_text().strip()
                    })
            data['active_ingredients'] = active_ingredients
            
            page.click("#jbox > table > tbody > tr:nth-child(2) > td:nth-child(2) > div > a")
            page.wait_for_selector("#jbox-iframe", state="hidden")
            
            return data
        except Exception as e:
            logging.error(f"Error scraping item: {str(e)}")
            return None

    def get_table_data(self, frame, label):
        try:
            return frame.locator(f"//td[contains(text(), '{label}')]/following-sibling::td").inner_text().strip()
        except:
            return ""

    def scrape_page(self, page):
        items_scraped = 0
        page_data = []
        for i in range(2, 22):
            link_selector = f"#tab > tbody > tr:nth-child({i}) > td.t3 > span > a"
            if page.is_visible(link_selector):
                logging.info(f"Scraping item {i-1}")
                data = self.scrape_item(page, link_selector)
                if data:
                    page_data.append(data)
                    items_scraped += 1
                else:
                    logging.warning(f"Failed to scrape item {i-1}")
            else:
                logging.info(f"No more items found after item {i-2}")
                break
        
        logging.info(f"Total items scraped on this page: {items_scraped}")
        return items_scraped, page_data

    def next_page(self, page):
        try:
            logging.info("Attempting to navigate to the next page")
            
            next_page_link = page.locator("//a[contains(text(), '下一页')]").first
            if not next_page_link or "disabled" in next_page_link.get_attribute("class"):
                logging.info("Next page link is not available or disabled. This is the last page.")
                return False
            
            current_page = int(page.locator("//li[@class='active']/a").inner_text())
            logging.info(f"Current page: {current_page}")
            
            next_page_link.click()
            page.wait_for_load_state('networkidle')
            
            new_page = int(page.locator("//li[@class='active']/a").inner_text())
            if new_page > current_page:
                self.current_page += 1
                logging.info(f"Successfully moved to page {self.current_page}")
                return True
            else:
                logging.info("Page did not change. This might be the last page.")
                return False
        
        except Exception as e:
            logging.error(f"Unexpected error in next_page function: {str(e)}")
            return False

def main(search_term, progress_callback=None):
    crawler = CustomCrawler(search_term)
    return crawler.run(progress_callback)

if __name__ == "__main__":
    main('Dimethoate')
