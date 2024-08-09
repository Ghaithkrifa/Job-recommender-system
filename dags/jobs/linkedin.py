from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import requests
import math
import time


def connect():
    options = Options()
    options.headless = True
    options.add_argument('--log-level=1')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.linkedin.com/checkpoint/lg/sign-in-another-account")
    time.sleep(5)
    username = driver.find_element(By.ID, "username")
    username.send_keys("gaithkrifa123@gmail.com")
    pword = driver.find_element(By.ID, "password")
    pword.send_keys("hedimarzouk1230")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(10)
    return driver

def nb_of_page(driver,url):

    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # 1. Get number of jobs found and number of pages:
    try:
        div_number_of_jobs = soup.find("div",{"class":"jobs-search-results-list__subtitle"})
        list = div_number_of_jobs.find('span').get_text().strip().split()
        if (len(list)>2):
            number_of_jobs = int(str(list[0])+str(list[1]))
        else:
            number_of_jobs = int(list[0])
    except:
        number_of_jobs = 0
        
    number_of_pages=math.ceil(number_of_jobs/25)
    print("number_of_jobs:",number_of_jobs)
    print("number_of_pages:",number_of_pages)

    return  number_of_pages,soup

def find_Job_Ids(soup):

    Job_Ids_on_the_page = []
    try:
        soup = soup.find('ul',{'class':'scaffold-layout__list-container'})
        job_postings = soup.find_all('li', {'class': 'jobs-search-results__list-item'})
        for job_posting in job_postings:
            Job_ID = job_posting.get('data-occludable-job-id')
            Job_Ids_on_the_page.append(Job_ID)
    except:
        pass
    return Job_Ids_on_the_page

def get_data(driver, job_title = 'software',location = 'Tunisia'):
    List_Job_IDs = []

    url = f'https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}&f_TPR=r86400&sortBy=DD'
    url = requests.utils.requote_uri(url)

    number_of_pages, soup = nb_of_page(driver,url)


    if number_of_pages>=1:
        
        for page_num in range(0,number_of_pages):
            try:
                print(f"Scraping page: {page_num+1}")

                if(page_num == 0):
                    List_Job_IDs.extend(find_Job_Ids(soup))

                else:
                    url = f'https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}&f_TPR=r86400&sortBy=DD&start={25 * page_num}'
                    url = requests.utils.requote_uri(url)
                    driver.get(url)
                    time.sleep(5)           
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    List_Job_IDs.extend(find_Job_Ids(soup)) 
                    
                    if soup.find('ul',{'class':'scaffold-layout__list-container'}) is None:
                        print('End page')
                        break

                    if len(List_Job_IDs) > 200:
                        break                
                print("done!")
            except:
                print('Error links')
    
    job={}
    list_jobs=[]

    for j in range(0,len(List_Job_IDs)):
        try:

            job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{List_Job_IDs[j]}"
            resp = requests.get(job_url)    
            time.sleep(2)
            soup=BeautifulSoup(resp.text,'html.parser')

            try:
                job['job_link'] = soup.find('a',{'class':'topcard__link'}).get('href')
            except:
                job['job_link'] = None
            
            try:
                job["job_name"]=soup.find("h2",{"class":"top-card-layout__title"}).text.strip()
            except:
                job["job_name"]= job_title

            
            try: 
                job["job_text"] = soup.find('div',{'class':'description__text description__text--rich'}).text.strip().split("\n")[0]
            except:
                job["job_text"] = None
            
            try:
                job["job_company"]=soup.find("div",{"class":"top-card-layout__card"}).find("a").find("img").get('alt')
            except:
                job["job_company"]="Not found"

            try:
                job["job_location"]=soup.find("span",{"class":"topcard__flavor topcard__flavor--bullet"}).text.strip()
            except:
                job["job_location"]=None

            try:
                job["job_type"]=soup.find("ul",{"class":"description__job-criteria-list"}).find("li").text.replace("Seniority level","").strip()
            except:
                job["job_type"]=None

            try:
                date = soup.find("span",{"class":"posted-time-ago__text"}).text.strip()

                now = datetime.now()
                if 'hour' in date or 'hours' in date or 'minute' in date or 'minutes' in date :
                    formatted_date = now.strftime("%Y-%m-%d")
                    job['job_date'] = formatted_date
                elif '1 days' in date.replace('\xa0', ''):
                    date = now - timedelta(days=1)
                    formatted_date = date.strftime("%Y-%m-%d")
                    job['job_date'] = formatted_date
            except:
                job["job_date"]=None

            list_jobs.append(job)    
            print(f"{j+1} Jobs read", end="\r")

        except:
            print(f"{j+1} error read Job ID: {List_Job_IDs[j]}")
            
        
        job={}

    jobs_df = pd.DataFrame(list_jobs)
    return jobs_df


def get_datas(driver, Keywords, Locations):
    data = pd.DataFrame()
    for keyword in Keywords:
        for location in Locations:
            df = get_data(driver,keyword,location)
            data = pd.concat([data,df],axis=0)
    return data


def run():
    driver=connect()
    a=get_datas(driver,["big data"],["France"])
    if time.sleep(60):
        return a
    return a

if __name__== '__main__': 
    run()


