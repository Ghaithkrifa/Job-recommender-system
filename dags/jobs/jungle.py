from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import requests
import time

def get_links(keyword="data engineer"):
    links=[]
    options = Options()
    options.headless = True
    # options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    try:
        url = f'https://www.welcometothejungle.com/fr/jobs?&query={keyword}&sortBy=mostRecent'
        driver.get(url)
        time.sleep(5)
        nb_page = int(driver.find_elements(By.CLASS_NAME, 'jCRLMV')[-2].text)
        
        for page in range(nb_page):
            items = driver.find_elements(By.CLASS_NAME, 'ais-Hits-list-item')
            for item in items:
                try:
                    date = item.find_element(By.TAG_NAME,'time').get_attribute('datetime')
                    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                    current_date = datetime.utcnow()
                    date_difference = current_date - date_obj
                    
                    if date_difference <= timedelta(days=1):
                        links.append(item.find_element(By.CLASS_NAME, 'iPeVkS').get_attribute("href"))
                except:
                    pass
                
            if(date_difference > timedelta(days=1)):
                break
            
            driver.find_elements(By.CSS_SELECTOR, 'a.sc-IqJVf.evElzU')[-1].click()
            time.sleep(5)
    except:
        print("Error Keyword ..")
    print(len(links),"Jobs for",keyword)
    
    return links

def get_data(keyword="data engineer"):
    List_job = []
    links = get_links(keyword)

    print(keyword, 'Job extraction ...')
    
    for i in range(len(links)):
        job = {}
        resp = requests.get(links[i])
        soup = BeautifulSoup(resp.text,'html.parser')

        try:
            job['job_link'] = links[i]
        except:
            job['job_link'] = None
            
        try:
            job["job_name"] = soup.find('h2', {'class':"sc-gvZAcH lodDwl wui-text"}).text.strip()
        except:
            job["job_name"] = keyword

        try: 
            ul = soup.find('div',{'class':'fhzEMX'}).find_all('ul')
            job_text = ''
            for li in ul:
                job_text += ' '+li.text
            if job_text=='':
                job_text = soup.find('div',{'class':'kqgROr'}).text
            job["job_text"] = job_text
        except:
            job["job_text"] = None

        try:
            job["job_company"] = soup.find('span',{'class':'sc-gvZAcH lpuzVS wui-text'}).text.strip()
        except:
            job["job_company"] = "Not found"

        
        try:
            job_villes = soup.find_all('div',{'class':'sc-bOhtcR eDrxLt'})[1].find_all('span',{'class':'dhOyPm'})
            job_ville=''
            for ville in job_villes:
                job_ville += ville.text.strip()
            
            job["job_location"] = job_ville
        except:
            job["job_location"] = None

        try:
            job["job_type"] = soup.find_all('div',{'class':'sc-bOhtcR eDrxLt'})[0].text
        except:
            job["job_type"] = None

        try:
            date = soup.find('time').get('datetime')
            dt_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")

            date = dt_obj.date().isoformat()
            job["job_date"] = date
        except:
            now = datetime.now()
            job["job_date"] = now.strftime("%Y-%m-%d")
        
        
        List_job.append(job)
        
        print(i,'Jobs read',end="\r")

    return pd.DataFrame(List_job)


def get_datas(Keywords):
    data = pd.DataFrame()
    for key in Keywords:
        df = get_data(key)
        data = pd.concat([data,df], axis=0)
    print('Done')
    
    return data