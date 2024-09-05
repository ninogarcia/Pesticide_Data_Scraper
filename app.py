import streamlit as st
import pandas as pd
from crawler import main as run_crawler

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

        def update_progress(message):
            status_text.text(message)
        
        try:
            results = run_crawler(search_term, progress_callback=update_progress)
            
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