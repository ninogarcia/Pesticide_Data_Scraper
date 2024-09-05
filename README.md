# Pesticide Registration Data Scraper

## Overview

This project is a web application that scrapes and displays pesticide registration data from the ICAMA (Institute for the Control of Agrochemicals, Ministry of Agriculture) database. It allows users to search for pesticide products by their active ingredient names and view detailed registration information.

Created by: Niño Garcia

## Features

- Search for pesticide products by active ingredient name
- Live data scraping from the ICAMA database
- Display of comprehensive product information including:
  - Registered Number
  - Product Name
  - Active Ingredients
  - Toxicity
  - Formulation
  - Registration Certificate Holder
  - First Prove Date
  - Registration Period
  - Remarks
- Real-time progress updates during the search process

## Technologies Used

- Python
- Streamlit
- Selenium
- Pandas

## Setup and Installation

1. Clone this repository:
   ```
   git clone https://github.com/ninogarcia/pesticide-registration-scraper.git
   cd pesticide-registration-scraper
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install the appropriate WebDriver for Selenium:
   - For Chrome: Download ChromeDriver from the [official website](https://sites.google.com/a/chromium.org/chromedriver/downloads) and add it to your system PATH.

4. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## Usage

1. Enter the name of an active ingredient in the search box.
2. Click the "Search" button to initiate the scraping process.
3. Wait for the results to be displayed in the table.
4. View additional information about the scraper creator in the sidebar.

## Important Notes

- This application scrapes live data from the ICAMA website. Search times may vary depending on the number of results and the responsiveness of the ICAMA server.
- Ensure you have a stable internet connection for the best performance.
- Use responsibly and in accordance with the ICAMA website's terms of service.

## Contact

For any questions or collaborations, please reach out to Niño Garcia:

- LinkedIn: [https://www.linkedin.com/in/ninogarci/](https://www.linkedin.com/in/ninogarci/)
- Upwork: [https://www.upwork.com/freelancers/~01dd78612ac234aadd](https://www.upwork.com/freelancers/~01dd78612ac234aadd)
