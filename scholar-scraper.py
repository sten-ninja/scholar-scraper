from msilib import sequence
from selenium import webdriver
from selenium.webdriver.common.by import By # for selecting elements with Selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC # for waiting until expected conditions are met
import time
from bs4 import BeautifulSoup # for a more elegant way to find static elements on page
import requests #requesting & reading BibTeX
import re #regexp
import datetime #for timestamping the output file

# define a suitable starting URL
url = "https://scholar.google.com/scholar?q=cyber"
how_many_pages = 10
filename_prefix = 'Scraping-results'
filename_suffix = 'Pages 01-10'

# create an output file with timestamp in its name
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
filename = filename_prefix + " " + timestamp + " " + filename_suffix + ".csv"
with open(filename, 'a', encoding="utf-8") as f:
    f.write('"Year","Authors","Title","Journal","Citations","BibTeX","BibTeX_ID", Link\n')

# open browser in incognito (although Selenium already starts by default in a clean session)
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
browser = webdriver.Chrome(chrome_options=chrome_options)
wait = WebDriverWait(browser, 60) # general waiting time tolerance for EC

for i in range(0, how_many_pages): #looping through several search result pages, first page is 0. 
    url_current = f'{url}&start={i}0' # getting the proper search page
    browser.get(url_current)

    # Waiting for the page to load or potentially solve some wonderful CAPTCHA
    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'Cite')))
    # log the estimated number of total search results
    number_of_total_results = browser.find_element(By.XPATH, '//*[@id="gs_ab_md"]').text

    # Feeding the page source to BeautifulSoup
    soup = BeautifulSoup(browser.page_source, 'html.parser')

    # getting all the individual search results
    search_results = soup.find_all("div", class_="gs_r gs_or gs_scl")

    # start a counter for citation button clicking iterations (to get BibTeX info)
    c = 0

    for search_result in search_results:
        # find title
        title = re.sub(r'\[.*?\]\s+', '', search_result.h3.text) #remove [PDF], [BOOK] and other things in [] 
        print(title)
        
        # find cited by (if exists)
        citation_found = re.search(r'Cited by \d+',search_result.text)
        if citation_found:
            cited_by = citation_found.group(0).split(' ')[-1]
        else:
            cited_by = 0

        # find right-side link (if exists)
        source_link_found = search_result.find("div", class_="gs_or_ggsm")
        if source_link_found:
            source_link = source_link_found.a.get('href')
        else:
            source_link = "No_link"
        print(source_link + "\n")

        # find Bibtex button and link url
        cite_button = browser.find_elements(By.XPATH, '//*[@aria-controls="gs_cit"]')[c]
        c += 1 # increasing the cite button counter for the next iteration
        cite_button.click()
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'BibTeX'))) # wait until BibTeX link is visible
        bibtex_button = browser.find_element(By.LINK_TEXT, 'BibTeX')
        bibtex_link = bibtex_button.get_attribute('href')
        bibtex_source = requests.get(bibtex_link)
        bibtex_source = re.sub(r'\n', ' ', bibtex_source.text) #remove newlines from BiBteX source
        browser.implicitly_wait(1) # wait to make sure that BibTeX source is read
        cite_close_button = browser.find_element(By.ID, 'gs_cit-x')
        cite_close_button.click()

        # Parsing some info from the BibTeX
        author_found = re.search(r'(?<=author={)[\w,\s]+', bibtex_source)
        if author_found:
            author = author_found.group(0)
        else: 
            author = ""

        year_found = re.search(r'(?<=year={)[\w,\s]+', bibtex_source)
        if year_found:
            year = year_found.group(0)
        else: 
            year = "year_unknown"

        journal_found = re.search(r'(?<=journal={)[\w,\s]+', bibtex_source)
        if journal_found:
            journal = journal_found.group(0)
        else: 
            journal = "_journal_not_found"

        bibtex_id_found = re.search(r'^@\w+{\w+', bibtex_source)
        if bibtex_id_found:
            bibtex_id = bibtex_id_found.group(0).split('{')[-1] # removing article|book etc 
        else: bibtex_id = "bibtex_error"

        # Write the results to the file
        with open(filename, 'a', encoding="utf-8") as f:
            f.write(f'{year},"{author}","{title}","{journal}",{cited_by},"{bibtex_source}","{bibtex_id}","{source_link}"\n')
    

time.sleep(2) # just for a small-scale dramatic delay effect
browser.close()

print("----------------------------------------------")
print("(Last) page info: " + number_of_total_results)
with open(filename, 'r', encoding = "utf-8") as f:
    lines_in_file = len(f.readlines())
print(f"Total of {lines_in_file - 1} results written to {filename}")
print("Scraping completed!")