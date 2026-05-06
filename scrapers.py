import requests
from bs4 import BeautifulSoup
import re
import time
import os
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import *
from utils import *

class BasicScraper:
    def __init__(self):
        self.logger = setup_logger("BasicScraper", f"{LOG_DIR}/basic_scraper.log")
        
    def extract_emails(self, soup, url, include_personal=True, include_business=True):
        emails = set()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        page_text = soup.get_text()
        found_emails = re.findall(email_pattern, page_text)
        
        for email in found_emails:
            if is_valid_email(email):
                domain = email.split('@')[1].lower()
                if include_business and not is_personal_email_domain(domain):
                    emails.add((email, "business"))
                elif include_personal and is_personal_email_domain(domain):
                    emails.add((email, "personal"))
        return list(emails)
    
    def extract_contact_forms(self, soup, url):
        contact_forms = []
        contact_links = soup.find_all('a', href=re.compile(r'contact', re.IGNORECASE))
        for link in contact_links:
            href = link.get('href', '')
            if not href.startswith('http'):
                href = urljoin(url, href)
            contact_forms.append(href)
        return list(set(contact_forms))

class SeleniumScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.logger = setup_logger("SeleniumScraper", f"{LOG_DIR}/selenium_scraper.log")
    
    def scrape_page(self, url):
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
            
            # --- TERMUX ANDROID FIX ---
            if os.path.exists("/data/data/com.termux/files/usr/bin/chromium-browser"):
                chrome_options.binary_location = "/data/data/com.termux/files/usr/bin/chromium-browser"
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            company = "Unknown"
            title_tag = soup.find('title')
            if title_tag:
                company = title_tag.get_text().strip().split(' - ')[0]
            
            basic_scraper = BasicScraper()
            emails = basic_scraper.extract_emails(soup, url)
            
            business_email = ""
            personal_email = ""
            for email, email_type in emails:
                if email_type == "business" and not business_email:
                    business_email = email
                elif email_type == "personal" and not personal_email:
                    personal_email = email
            
            contact_forms = basic_scraper.extract_contact_forms(soup, url)
            
            driver.quit()
            
            return {
                'company': company,
                'website': url,
                'business_email': business_email,
                'personal_email': personal_email,
                'contact_form': contact_forms[0] if contact_forms else "",
                'linkedin': '', 'twitter': ''
            }
        
        except Exception as e:
            self.logger.error(f"Error scraping {url} with Selenium: {str(e)}")
            return None

class GoogleScraper:
    def __init__(self, api_key=SERPAPI_KEY):
        self.api_key = api_key
        self.logger = setup_logger("GoogleScraper", f"{LOG_DIR}/google_scraper.log")
    
    def search(self, query, num_results=10):
        if not self.api_key:
            return self._basic_search(query, num_results)
        try:
            params = {"engine": "google", "q": query, "api_key": self.api_key, "num": num_results}
            response = requests.get('https://serpapi.com/search', params=params)
            response.raise_for_status()
            results = []
            for result in response.json().get('organic_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', '')
                })
            return results
        except Exception as e:
            self.logger.error(f"SerpAPI failed: {e}. Falling back to basic search.")
            return self._basic_search(query, num_results)
            
    def _basic_search(self, query, num_results=10):
        # Fallback method just in case SerpAPI runs out
        search_url = f"https://www.google.com/search?q={query}&num={num_results}"
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            if os.path.exists("/data/data/com.termux/files/usr/bin/chromium-browser"):
                chrome_options.binary_location = "/data/data/com.termux/files/usr/bin/chromium-browser"
                
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(search_url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            results = []
            for g in soup.find_all('div', class_='g'):
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    title = g.find('h3').text if g.find('h3') else ""
                    snippet = g.get_text(separator=' ')
                    results.append({'title': title, 'link': link, 'snippet': snippet})
            driver.quit()
            return results
        except Exception as e:
            return []
