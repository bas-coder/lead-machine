import pandas as pd
import time
import re
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local Ephemeral Storage
CACHE_FILE = "scraped_urls.txt"
LEADS_FILE = "master_leads_list.csv"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_to_cache(url):
    with open(CACHE_FILE, 'a') as f:
        f.write(f"{url}\n")

def extract_email_from_text(text):
    if not text:
        return None
    # Ruthless regex for extracting emails
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return emails[0] if emails else None

def save_to_csv(leads):
    if not leads:
        return
    df = pd.DataFrame(leads)
    
    # Format headers perfectly for GoHighLevel Import
    df = df.rename(columns={
        'business_email': 'Email',
        'company': 'Company Name',
        'website': 'Website',
        'niche': 'Tags'
    })
    
    columns_to_keep = ['Email', 'Company Name', 'Website', 'Tags']
    df = df[[col for col in columns_to_keep if col in df.columns]]
    
    if os.path.isfile(LEADS_FILE):
        df.to_csv(LEADS_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(LEADS_FILE, index=False)

def send_to_discord(lead, webhook_url):
    if not webhook_url:
        return
        
    data = {
        "content": f"🚨 **NEW INVESTOR LEAD** 🚨\n**Email:** {lead['business_email']}\n**Tag (Niche):** {lead['niche']}\n**Source:** {lead['company'][:50]}\n**URL:** <{lead['website']}>"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        requests.post(webhook_url, data=json.dumps(data), headers=headers)
    except Exception as e:
        print(f"⚠️ Discord Webhook Error: {e}")

def get_google_results(query, api_key, num_results=50):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num_results
    }
    try:
        response = requests.get(url, params=params)
        return response.json().get("organic_results", [])
    except Exception as e:
        print(f"⚠️ SerpAPI Error: {e}")
        return []

def main():
    print("🚀 Fly.io Lead Generation Engine Started!")
    print("🔥 INVESTOR SNIPER MODE ACTIVATED")
    print("🛡️ DISCORD FAILSAFE SECURED.")
    
    api_key = os.getenv("SERPAPI_KEY")
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not api_key:
        print("❌ ERROR: Missing SERPAPI_KEY in .env file or Fly Secrets!")
        return

    raw_niches = os.getenv("TARGET_NICHES", "angel investor")
    num_results = int(os.getenv("NUM_RESULTS", "50"))

    target_niches = [niche.strip().strip("'").strip('"') for niche in raw_niches.split(',')]
    processed_urls = load_cache()
    total_leads_found = 0

    for target_niche in target_niches:
        if not target_niche:
            continue
            
        print(f"\n==================================================")
        print(f"🎯 HUNTING: {target_niche.upper()}")
        print(f"==================================================")
        
        queries = [
            f'site:instagram.com "{target_niche}" "@gmail.com"',
            f'site:linkedin.com/in "{target_niche}" "@gmail.com"',
            f'site:twitter.com "{target_niche}" "@gmail.com"',
            f'"{target_niche}" "contact me" "@gmail.com"'
        ]

        for query in queries:
            print(f"\n🔍 Executing API Search: {query}")
            results = get_google_results(query, api_key, num_results)
            
            if not results:
                print("   ⚠️ No results found or API limit reached.")
                time.sleep(2)
                continue

            for result in results:
                url = result.get('link', '')
                snippet = result.get('snippet', '')
                title = result.get('title', 'Unknown')
                
                if not url or url in processed_urls:
                    continue

                fast_email = extract_email_from_text(snippet)
                
                if fast_email:
                    print(f"  --> ⚡ FAST HIT: {fast_email} | {title[:30]}...")
                    
                    single_lead = {
                        'niche': target_niche, 
                        'company': title, 
                        'website': url,
                        'business_email': fast_email
                    }
                    
                    save_to_csv([single_lead])
                    send_to_discord(single_lead, webhook_url)
                    
                    total_leads_found += 1
                    save_to_cache(url)
                    processed_urls.add(url)
            
            time.sleep(1)

    print(f"\n🎉 ALL DONE! Total new leads stashed: {total_leads_found}")
    print("⏸️ Scraping complete. Server staying awake...")
    
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
