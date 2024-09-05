import streamlit as st
import pandas as pd
from crawler import main as run_crawler
import plotly.express as px

@st.cache_data
def fetch_data(search_term):
    return run_crawler(search_term, progress_callback=update_progress)

st.set_page_config(page_title="Pesticide Registration Data Scraper", layout="wide")

st.title("Pesticide Registration Data Scraper")

st.markdown("Data source: [ICAMA Pesticide Registration Database](https://www.icama.cn/BasicdataSystem/pesticideRegistrationEn/queryselect_en.do)")

# Sidebar
st.sidebar.header("Data Scraper by: Niño Garcia")
st.sidebar.subheader("Contact Details:")
st.sidebar.markdown("[LinkedIn](https://www.linkedin.com/in/ninogarci/)")
st.sidebar.markdown("[Upwork](https://www.upwork.com/freelancers/~01dd78612ac234aadd)")

# Main
search_term = st.text_input("Enter Active Ingredient Name in English:")

if 'results' not in st.session_state:
    st.session_state.results = None

col1, col2, col3 = st.columns(3)
search_button = col1.button("Search")
clear_button = col2.button("Clear Results")
download_button = col3.button("Download Results")

if search_button:
    if search_term:
        st.info(f"Searching for: {search_term}")
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(message):
            status_text.text(message)
        
        try:
            st.session_state.results = fetch_data(search_term)
            
            if st.session_state.results:
                st.success(f"Found {len(st.session_state.results)} results")
            else:
                st.warning("No results found.")
        except Exception as e:
            st.error(f"An error occurred during the search: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()
    else:
        st.warning("Please enter a search term.")

if clear_button:
    st.session_state.results = None

if st.session_state.results:
    # Prepare data for display
    display_data = []
    for item in st.session_state.results:
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
    
    # Filters
    toxicity_filter = st.multiselect("Filter by Toxicity", options=df['Toxicity'].unique())
    if toxicity_filter:
        df = df[df['Toxicity'].isin(toxicity_filter)]
    
    # Display data
    st.dataframe(df, use_container_width=True)
    
    # Visualizations
    st.subheader("Data Visualizations")
    col1, col2 = st.columns(2)
    
    # Toxicity distribution
    fig1 = px.pie(df, names='Toxicity', title='Distribution of Toxicity Levels')
    col1.plotly_chart(fig1)
    
    # Top registration holders
    top_holders = df['Registration Holder'].value_counts().head(10)
    fig2 = px.bar(top_holders, x=top_holders.index, y=top_holders.values, title='Top 10 Registration Holders')
    col2.plotly_chart(fig2)

    if download_button:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="pesticide_data.csv",
            mime="text/csv",
        )

st.markdown("---")
st.markdown("Note: This app fetches live data from the ICAMA database. Search times may vary depending on the number of results.")
