from playwright.async_api import async_playwright
import time
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CustomCrawler:
    def __init__(self, search_term):
        self.search_term = search_term
        self.base_url = 'https://www.icama.cn/BasicdataSystem/pesticideRegistrationEn/queryselect_en.do'
        self.total_items_scraped = 0
        self.current_page = 1

    async def run(self, progress_callback=None):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(self.base_url)
                await self.search_and_submit(page)
                
                all_data = []
                while True:
                    items_scraped, page_data = await self.scrape_page(page)
                    all_data.extend(page_data)
                    self.total_items_scraped += items_scraped
                    
                    if progress_callback:
                        progress_callback(f"Scraped page {self.current_page}, total items: {self.total_items_scraped}")
                    
                    if not await self.next_page(page):
                        logging.info("No more pages. Scraping completed.")
                        break
                
                logging.info(f"Total items scraped across all pages: {self.total_items_scraped}")
                return all_data
            except Exception as e:
                logging.error(f"An error occurred during crawling: {str(e)}")
                return []
            finally:
                await browser.close()

    async def search_and_submit(self, page):
        try:
            await page.fill("#searchForm > div.search_table > table > tbody > tr:nth-child(3) > td.t1 > input[type=text]", self.search_term)
            await page.click("#btnSubmit")
            await page.wait_for_load_state('networkidle')
        except Exception as e:
            logging.error(f"Error in search_and_submit: {str(e)}")
            raise

    async def scrape_item(self, page, link_selector):
        try:
            await page.click(link_selector)
            await page.wait_for_selector("#jbox-iframe")
            
            frame = page.frame_locator("#jbox-iframe").first
            
            data = {}
            data['registered_number'] = await self.get_table_data(frame, "Registered number：")
            data['first_prove'] = await self.get_table_data(frame, "FirstProve：")
            data['period'] = await self.get_table_data(frame, "Period：")
            data['product_name'] = await self.get_table_data(frame, "ProductName：")
            data['toxicity'] = await self.get_table_data(frame, "Toxicity：")
            data['formulation'] = await self.get_table_data(frame, "Formulation：")
            data['registration_certificate_holder'] = await self.get_table_data(frame, "Registration certificate holder：")
            data['remark'] = await self.get_table_data(frame, "Remark：")

            active_ingredients = []
            rows = await frame.locator("table:nth-of-type(2) tr").all()
            for row in rows[2:]:
                cols = await row.locator("td").all()
                if len(cols) == 2:
                    active_ingredients.append({
                        "ingredient": await cols[0].inner_text().strip(),
                        "content": await cols[1].inner_text().strip()
                    })
            data['active_ingredients'] = active_ingredients
            
            await page.click("#jbox > table > tbody > tr:nth-child(2) > td:nth-child(2) > div > a")
            await page.wait_for_selector("#jbox-iframe", state="hidden")
            
            return data
        except Exception as e:
            logging.error(f"Error scraping item: {str(e)}")
            return None

    async def get_table_data(self, frame, label):
        try:
            return await frame.locator(f"//td[contains(text(), '{label}')]/following-sibling::td").inner_text().strip()
        except:
            return ""

    async def scrape_page(self, page):
        items_scraped = 0
        page_data = []
        for i in range(2, 22):
            link_selector = f"#tab > tbody > tr:nth-child({i}) > td.t3 > span > a"
            if await page.is_visible(link_selector):
                logging.info(f"Scraping item {i-1}")
                data = await self.scrape_item(page, link_selector)
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

    async def next_page(self, page):
        try:
            logging.info("Attempting to navigate to the next page")
            
            next_page_link = page.locator("//a[contains(text(), '下一页')]").first
            if not next_page_link or "disabled" in await next_page_link.get_attribute("class"):
                logging.info("Next page link is not available or disabled. This is the last page.")
                return False
            
            current_page = int(await page.locator("//li[@class='active']/a").inner_text())
            logging.info(f"Current page: {current_page}")
            
            await next_page_link.click()
            await page.wait_for_load_state('networkidle')
            
            new_page = int(await page.locator("//li[@class='active']/a").inner_text())
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

async def main(search_term, progress_callback=None):
    crawler = CustomCrawler(search_term)
    return await crawler.run(progress_callback)

if __name__ == "__main__":
    asyncio.run(main('Dimethoate'))
