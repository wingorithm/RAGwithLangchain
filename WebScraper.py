from dotenv import load_dotenv
import os
from collections import deque
import requests
from bs4 import BeautifulSoup

load_dotenv()

def scrape_all(starting_url, product_name):

    for i in range(len(starting_url)):
        response = requests.get(starting_url[i])
        soup = BeautifulSoup(response.content, "html.parser")
        target_file = "./Bank Product Data/"
        target_div = soup.find(id="skipmaincontent") #check commonwealth html structure

        if target_div:
            print("check point: " + product_name[i])
            
            file_addr = target_file + product_name[i] + ".txt"

            if os.path.exists(file_addr):
                os.remove(file_addr)

            with open(file_addr, "w", encoding="utf-8", errors="ignore") as f:
                f.write("This Article discuss about: " + product_name[i] + "\n")
                for element in target_div.children:
                    text = element.text.strip()
                    if text:
                        f.write(text + "\n")
                        
            remove_excess_empty_lines(file_addr)

def remove_excess_empty_lines(file_path):
    lines = []
    empty_line_count = 0
    with open(file_path, 'r') as in_file:
        for line in in_file:
            stripped_line = line.strip()
            if stripped_line:
                lines.append(line)
                empty_line_count = 0
            elif empty_line_count < 2:
                lines.append(line)
                empty_line_count += 1

    with open(file_path, 'w') as out_file:
        out_file.writelines(lines)


# Cover Bank Account
# WEB_SOURCE_PHASE_1 = ["https://www.commbank.com.au/banking/everyday-accounts", "https://www.commbank.com.au/banking/everyday-account-smart-access", "https://www.commbank.com.au/banking/students", "https://www.commbank.com.au/banking/pensioner-security", "https://www.commbank.com.au/banking/streamline-basic", "https://www.commbank.com.au/banking/smart-access-account-for-youth", "https://www.commbank.com.au/business/bank-accounts"]
# WEB_NAME_PHASE_1 = ["EVERYDAY ACCOUNT", "Everyday Account Smart Access", "Student account", "Pensioner Security Account", "Streamline Basic Account","Smart Access Account for Youth","Business bank accounts"]

# Cover Personal Loan and its variety
# WEB_SOURCE_PHASE_2 = ["https://www.commbank.com.au/credit-cards", "https://www.commbank.com.au/credit-cards/tools/credit-card-compare", "https://www.commbank.com.au/personal-loans","https://www.commbank.com.au/personal-loans/secured-personal-loan", "https://www.commbank.com.au/personal-loans/variable-rate-loan", "https://www.commbank.com.au/personal-loans/fixed-rate-loan"]
# WEB_NAME_PHASE_2 = ["Credit cards", "Credit cards Compare", "Personal loans","Secured Personal Loan","Variable Rate Personal Loan", "Fixed Rate Personal Loans"]
#ERROR =>  "Car Loans", "electric-vehicle-loan", "Debt consolidation loans", "Home Improvement Loan"

# Cover About Company and Saving account
WEB_SOURCE_PHASE_3 = ["https://www.commbank.com.au/about-us/our-company", "https://www.commbank.com.au/about-us", "https://www.commbank.com.au/savings-accounts", "https://www.commbank.com.au/banking/netbank-saver", "https://www.commbank.com.au/banking/goal-saver", "https://www.commbank.com.au/banking/term-deposits", "https://www.commbank.com.au/banking/youthsaver"] 
WEB_NAME_PHASE_3 = ["CommonWealth Our company", "Commonwealth Bank of Australia", "Saving Account & Term Deposit", "NetBank Saver", "GoalSaver","Term Deposits","Youthsaver"]

scrape_all(WEB_SOURCE_PHASE_3, WEB_NAME_PHASE_3)
