# crawler.py
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.icama.cn/BasicdataSystem/pesticideRegistrationEn/queryselect_en.do"

def scrape_data(search_term, progress_callback=None):
    session = requests.Session()
    
    # Initial request to get cookies
    session.get(BASE_URL)
    
    # Prepare the search payload
    payload = {
        "method": "queryList",
        "isproduct": "1",
        "isactive": "2",
        "activeEnameInput": search_term,
        "pageSize": "20",
        "currentPage": "1"
    }
    
    results = []
    current_page = 1
    total_pages = 1
    
    while current_page <= total_pages:
        if progress_callback:
            progress_callback(f"Scraping page {current_page} of {total_pages}", current_page / total_pages)
        
        payload["currentPage"] = str(current_page)
        response = session.post(BASE_URL, data=payload)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Update total pages
        if current_page == 1:
            pagination = soup.find('div', class_='pagination')
            if pagination:
                total_pages = int(pagination.find_all('a')[-2].text)
        
        # Extract data from the current page
        rows = soup.find_all('tr', class_=['listfirstTr', 'listSecondTr'])
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 9:
                item = {
                    'registered_number': cols[0].text.strip(),
                    'product_name': cols[1].text.strip(),
                    'active_ingredients': [],
                    'toxicity': cols[3].text.strip(),
                    'formulation': cols[4].text.strip(),
                    'registration_certificate_holder': cols[5].text.strip(),
                    'first_prove': cols[6].text.strip(),
                    'period': cols[7].text.strip(),
                    'remark': cols[8].text.strip()
                }
                
                # Parse active ingredients
                ai_text = cols[2].text.strip()
                ai_parts = ai_text.split(';')
                for part in ai_parts:
                    if '(' in part and ')' in part:
                        ingredient, content = part.split('(')
                        content = content.rstrip(')')
                        item['active_ingredients'].append({
                            'ingredient': ingredient.strip(),
                            'content': content.strip()
                        })
                
                results.append(item)
        
        current_page += 1
        time.sleep(1)  # Be nice to the server
    
    return results
