from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time

def connect():
    options = webdriver.ChromeOptions()
    options.add_argument('--log-level=1')
    options.add_argument('--log-level=3')
    # options.add_argument("--headless")
    #options.add_argument('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(options=options)
    return driver


def get_links(keyword = "hadoop"):

    Links = []
    Posted = []

    driver = connect()
    url = f'https://fr.indeed.com/jobs?q={keyword}&l=France&fromage=1'
    
    while True:
        try:
            time.sleep(3)
            driver.get(url)
            time.sleep(2)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            td = soup.find_all('td',{'class':'resultContent'})
            link = []
            posted = []
            for i in td:
                link.append("https://fr.indeed.com/"+i.find('a',{'class':'jcs-JobTitle css-jspxzf eu4oa1w0'}).get('href'))
                posted.append(i.find('span',{'data-testid':'myJobsStateDate'}).text)
            Links.extend(link)
            Posted.extend(posted)
            try:
                url = 'https://fr.indeed.com' + soup.find('a', {'aria-label':'Next Page'}).get('href')
            except:
                break
        except:
            print("Error URL")
            break
    
    print(len(Links),"Jobs found for",keyword)
            
    driver.quit()
    return Links,Posted


def get_all_links(Keywords):
    Links = []
    Posted = []
    for key in Keywords:
        links, posted = get_links(key)
        Links.extend(links)
        Posted.extend(posted)
    return Links, Posted


def get_datas(Keywords):
    List_job = []
    Links, Posted = get_all_links(Keywords)
    for i in range(len(Links)):
        try:
            job = {}
            driver = connect()
            driver.get(Links[i])
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source,'html.parser')
            try:
                job['job_link'] = Links[i]
            except:
                job['job_link'] = None

            try:
                job['job_name'] = soup.find('h1',{'class':'jobsearch-JobInfoHeader-title'}).text.strip()
            except:
                job['job_name'] = Keywords
                
            try:
                job['job_text'] = soup.find('div',{'id':'jobDescriptionText'}).text.strip().replace('\n','')
            except:
                job['job_text'] = None
                
            try:
                job['job_company'] = soup.find('div',{'data-testid' : 'inlineHeader-companyName'}).find('span').text.strip()
            except:
                job['job_company'] = "Not found"
                
            try:
                job['job_location'] = soup.find('div',{'id':'jobLocationText'}).text.strip()
            except:
                job['job_location'] = None
            try:
                job['job_type'] =  soup.find('div',{'id':"salaryInfoAndJobType"}).find('span',{'class':'css-k5flys eu4oa1w0'}).text.replace('-','').strip()
            except:
                job['job_type'] = None
                
            try:
                date = Posted[i]
                now = datetime.now()
                if 'instant' in date:
                    formatted_date = now.strftime("%Y-%m-%d")
                    job['job_date'] = formatted_date
                elif '1jour' in date.replace('\xa0', ''):
                    date = now - timedelta(days=1)
                    formatted_date = date.strftime("%Y-%m-%d")
                    job['job_date'] = formatted_date
            except:
                job['job_date'] = now.strftime("%Y-%m-%d")
                
        except:
            print("Error link")
            pass
        
        List_job.append(job)
        driver.quit()
        time.sleep(2)

        
        print(i+1,"jobs extracted!",end='\r')
    return pd.DataFrame(List_job)