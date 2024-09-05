import streamlit as st
import pandas as pd
import os
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

    # Define other methods (scrape_item, get_table_data, scrape_page, next_page) as before...

async def main(search_term, progress_callback=None):
    crawler = CustomCrawler(search_term)
    return await crawler.run(progress_callback)

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

            async def run_search():
                results = await main(search_term, update_progress)

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

            # Schedule async function within Streamlit
            asyncio.run(run_search())

        else:
            st.warning("Please enter a search term.")

    st.markdown("---")
    st.markdown("Note: This app fetches live data from the ICAMA database. Search times may vary depending on the number of results.")

if __name__ == "__main__":
    streamlit_app()
