can you fix the # Streamlit app part of the code:

import streamlit as st
import pandas as pd
from crawler import main as run_crawler
import os
import subprocess
import asyncio
from playwright.async_api import async_playwright
import logging

# Install Playwright and its dependencies
os.system('playwright install')
os.system('playwright install-deps')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CustomCrawler:
    def __init__(self, search_term):
        self.search_term = search_term
        self.base_url = 'https://www.icama.cn/BasicdataSystem/pesticideRegistrationEn/queryselect_en.do'
        self.total_items_scraped = 0
        self.page = None
        self.current_page = 1

    async def setup_browser(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        self.page = await context.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})

    async def run(self, progress_callback=None):
        await self.setup_browser()
        try:
            await self.page.goto(self.base_url)
            await self.search_and_submit()
            
            all_data = []
            while True:
                items_scraped, page_data = await self.scrape_page()
                all_data.extend(page_data)
                self.total_items_scraped += items_scraped
                
                if progress_callback:
                    await progress_callback(f"Scraped page {self.current_page}, total items: {self.total_items_scraped}")
                
                if not await self.next_page():
                    logging.info("No more pages. Scraping completed.")
                    break
            
            logging.info(f"Total items scraped across all pages: {self.total_items_scraped}")
            return all_data
        except Exception as e:
            logging.error(f"An error occurred during crawling: {str(e)}")
            return []
        finally:
            await self.page.context.close()
            await self.page.context.browser.close()

    async def search_and_submit(self):
        try:
            await self.page.fill("#searchForm > div.search_table > table > tbody > tr:nth-child(3) > td.t1 > input[type=text]", self.search_term)
            await self.page.click("#btnSubmit")
        except Exception as e:
            logging.error(f"Error in search_and_submit: {str(e)}")
            raise

    async def scrape_item(self, link_selector):
        try:
            await self.page.click(link_selector)
            
            iframe = await self.page.wait_for_selector("#jbox-iframe")
            frame = await iframe.content_frame()
            
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
            rows = await frame.query_selector_all("table:nth-of-type(2) tr")
            for row in rows[2:]:
                cols = await row.query_selector_all("td")
                if len(cols) == 2:
                    ingredient = await cols[0].inner_text()
                    content = await cols[1].inner_text()
                    active_ingredients.append({
                        "ingredient": ingredient.strip(),
                        "content": content.strip()
                    })
            data['active_ingredients'] = active_ingredients
            
            await self.page.click("#jbox > table > tbody > tr:nth-child(2) > td:nth-child(2) > div > a")
            await self.page.wait_for_selector("#jbox-iframe", state="hidden")
            
            return data
        except Exception as e:
            logging.error(f"Error scraping item: {str(e)}")
            return None

    async def get_table_data(self, frame, label):
        try:
            element = await frame.query_selector(f"//td[contains(text(), '{label}')]/following-sibling::td")
            return await element.inner_text()
        except:
            return ""

    async def scrape_page(self):
        items_scraped = 0
        page_data = []
        for i in range(2, 22):
            link_selector = f"#tab > tbody > tr:nth-child({i}) > td.t3 > span > a"
            try:
                await self.page.wait_for_selector(link_selector, timeout=5000)
            except:
                logging.info(f"No more items found after item {i-2}")
                break

            logging.info(f"Scraping item {i-1}")
            data = await self.scrape_item(link_selector)
            if data:
                page_data.append(data)
                items_scraped += 1
            else:
                logging.warning(f"Failed to scrape item {i-1}")
        
        logging.info(f"Total items scraped on this page: {items_scraped}")
        return items_scraped, page_data

    async def next_page(self):
        try:
            logging.info("Attempting to navigate to the next page")
            
            pagination = await self.page.wait_for_selector("body > div.web_ser_body_right_main_search > div")
            logging.info("Pagination element found")
            
            next_page_link = await self.page.query_selector("//a[contains(text(), '下一页')]")
            if not next_page_link or await next_page_link.get_attribute("class") == "disabled":
                logging.info("Next page link is not available or disabled. This is the last page.")
                return False
            
            logging.info("Next page link found")
            
            current_page = int(await (await pagination.query_selector("li.active > a")).inner_text())
            logging.info(f"Current page: {current_page}")
            
            await next_page_link.click()
            logging.info("Clicked next page link")
            
            try:
                await self.page.wait_for_function(
                    f"() => parseInt(document.querySelector('li.active > a').innerText) > {current_page}",
                    timeout=20000
                )
                logging.info("Page change detected")
                
                self.current_page += 1
                logging.info(f"Successfully moved to page {self.current_page}")
                return True
            except:
                logging.info("Page did not change. This might be the last page.")
                return False
            
            await self.page.wait_for_timeout(5000)
        
        except Exception as e:
            logging.error(f"Unexpected error in next_page function: {str(e)}")
            return False

async def main(search_term, progress_callback=None):
    crawler = CustomCrawler(search_term)
    return await crawler.run(progress_callback)

def run_async(coroutine):
    return asyncio.run(coroutine)

# Streamlit app
def streamlit_app():
    st.set_page_config(page_title="Pesticide Registration Data Scraper", layout="wide")

    st.title("Pesticide Registration Data Scraper")

    st.markdown("Data source: [ICAMA Pesticide Registration Database](https://www.icama.cn/BasicdataSystem/pesticideRegistrationEn/queryselect_en.do)")

    # Add creator information
    st.sidebar.header("Data Scraper by: Niño Garcia")
    st.sidebar.subheader("Contact Details:")
    st.sidebar.markdown("[LinkedIn](https://www.linkedin.com/in/ninogarci/)")
    st.sidebar.markdown("[Upwork](https://www.upwork.com/freelancers/~01dd78612ac234aadd)")

    search_term = st.text_input("Enter Active Ingredient Name in English:")

    if st.button("Search"):
        if search_term:
            st.info(f"Searching for: {search_term}")
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            async def update_progress(message):
                status_text.text(message)
                await asyncio.sleep(0)  # Allow Streamlit to update
            
            try:
                results = asyncio.run(main(search_term, update_progress))
                
                if results:
                    st.success(f"Found {len(results)} results")
                    
                    # Prepare data for display
                    display_data = []
                    for item in results:
                        active_ingredients = ", ".join([f"{ai['ingredient']} ({ai['content']})" for ai in item['active_ingredients']])
                        display_data.append({
                            "Registered Number": item['registered_number'],
                            "Product Name": item['product_name'],
                            "Active Ingredients": active_ingredients,
                            "Toxicity": item['toxicity'],
                            "Formulation": item['formulation'],
                            "Registration Holder": item['registration_certificate_holder'],
                            "First Prove": item['first_prove'],
                            "Period": item['period'],
                            "Remark": item['remark']
                        })
                    
                    df = pd.DataFrame(display_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No results found.")
            except Exception as e:
                st.error(f"An error occurred during the search: {str(e)}")
            finally:
                progress_bar.empty()
                status_text.empty()
        else:
            st.warning("Please enter a search term.")

    st.markdown("---")
    st.markdown("Note: This app fetches live data from the ICAMA database. Search times may vary depending on the number of results.")

if __name__ == "__main__":
    streamlit_app()
