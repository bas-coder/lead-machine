import logging
import random
import time
from fake_useragent import UserAgent

def setup_logger(name, log_file):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def get_random_user_agent():
    try:
        ua = UserAgent()
        return ua.random
    except:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def is_valid_email(email):
    return '@' in email and '.' in email

def is_personal_email_domain(domain):
    personal = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com']
    return domain in personal

def random_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def calculate_priority_score(data):
    score = 0
    if data.get('business_email'): score += 3
    if data.get('personal_email'): score += 1
    if data.get('contact_form'): score += 2
    return score
