import pandas as pd
import time
import re
import os
import socket
from dotenv import load_dotenv
from scrapers import GoogleScraper, SeleniumScraper

# Load environment variables from .env file immediately
load_dotenv()

CACHE_FILE = "scraped_urls.txt"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_to_cache(url):
    with open(CACHE_FILE, 'a') as f:
        f.write(f"{url}\n")

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def wait_for_internet():
    if not check_internet():
        print("\n🌐 INTERNET LOST: Script is pausing. Do not close the terminal.")
        while not check_internet():
            time.sleep(10)
        print("🌐 INTERNET RESTORED: Resuming scraping...\n")

def extract_email_from_text(text):
    if not text:
        return None
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return emails[0] if emails else None

def save_to_csv(leads, filename="master_leads_list.csv"):
    if not leads:
        return
    df = pd.DataFrame(leads)
    columns_to_keep = ['niche', 'company', 'website', 'business_email', 'personal_email', 'contact_form']
    df = df[[col for col in columns_to_keep if col in df.columns]]
    
    if os.path.isfile(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)

def main():
    print("🚀 Fly.io Cloud Lead Generation Engine Started!")
    
    # Read from environment variables instead of asking for input
    raw_niches = os.getenv("TARGET_NICHES", "local marketing agencies")
    num_results = int(os.getenv("NUM_RESULTS", "50"))

    target_niches = [niche.strip().strip("'").strip('"') for niche in raw_niches.split(',')]
    processed_urls = load_cache()

    google = GoogleScraper() 
    selenium_scraper = SeleniumScraper(headless=True)
    total_leads_found = 0

    for target_niche in target_niches:
        if not target_niche:
            continue
            
        print(f"\n🔥 TARGETING: {target_niche.upper()}")
        queries = [
            f'"{target_niche}" "contact us" "@gmail.com"',
            f'"{target_niche}" "email" "@yahoo.com"'
        ]

        niche_leads = []

        for query in queries:
            wait_for_internet()
            print(f"\n🔍 Searching: {query}")
            
            try:
                search_results = google.search(query, num_results=num_results) 
            except Exception as e:
                print(f"⚠️ Search failed: {e}")
                continue

            for result in search_results:
                url = result.get('link')
                snippet = result.get('snippet', '')
                title = result.get('title', 'Unknown')
                
                if not url or not url.startswith('http'): continue
                if url in processed_urls:
                    print(f"  --> ⏭️ SKIPPING (In memory): {url}")
                    continue

                wait_for_internet()
                fast_email = extract_email_from_text(snippet)
                
                if fast_email:
                    print(f"  --> ⚡ FAST HIT: {title} | {fast_email}")
                    niche_leads.append({
                        'niche': target_niche, 'company': title, 'website': url,
                        'business_email': fast_email, 'personal_email': '', 'contact_form': ''
                    })
                    total_leads_found += 1
                    save_to_cache(url)
                    processed_urls.add(url)
                    continue

                print(f"  --> 🐢 Deep Scraping: {url}")
                try:
                    data = selenium_scraper.scrape_page(url)
                    if data and (data.get('business_email') or data.get('personal_email') or data.get('contact_form')):
                        data['niche'] = target_niche 
                        niche_leads.append(data)
                        total_leads_found += 1
                        print(f"      ✅ Found data on site.")
                    else:
                        print("      ❌ No contact info found.")
                except Exception:
                    print(f"      ⚠️ Failed")

                save_to_cache(url)
                processed_urls.add(url)
                time.sleep(1.5) 

        if niche_leads:
            save_to_csv(niche_leads)
            print(f"\n💾 Saved {len(niche_leads)} leads to master_leads_list.csv")

    print(f"\n🎉 ALL DONE! Total new leads this session: {total_leads_found}")
    print("⏸️ Scraping complete. Server is staying awake so you can download your CSV...")
    
    # Keep the server running so it doesn't reboot


if __name__ == "__main__":
    main()
