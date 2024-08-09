from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import pandas as pd
import time
from time import  sleep

def scroll_down(driver, scroll_step=800, scroll_pause_time=0.25):
    # Get the current scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down by a small step
        driver.execute_script(f"window.scrollBy(0, {scroll_step});")

        # Wait to load the page
        time.sleep(scroll_pause_time)

        # Calculate new scroll position and compare with last scroll height
        new_scroll_position = driver.execute_script("return window.pageYOffset + window.innerHeight")
        if new_scroll_position >= last_height:
            break

def get_links(keyword):
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.glassdoor.co.in/Job/index.htm")  
        time.sleep(5)
        
        search_key = driver.find_element(By.ID,'searchBar-jobTitle')
        search_key.send_keys(keyword)
        search_location = driver.find_element(By.ID,'searchBar-location')
        search_location.send_keys("France")
        sleep(3)
        
        search_location.send_keys(Keys.RETURN)
        sleep(3)
        fromage_button = driver.find_elements(By.CLASS_NAME,'SearchFiltersBar_labelButton__gF32h')[-1]
        fromage_button.click()
        sleep(3)
        
        last_day = driver.find_elements(By.CLASS_NAME,'SearchFiltersBar_dropdownOptionLabel___af5z')[1]
        last_day.click()
        time.sleep(2)
        
        scroll_down(driver)
        
        Links = []
        posts = driver.find_element(By.CLASS_NAME,'TwoColumnLayout_columnLeft__oyj9i')
        posts = posts.find_elements(By.CLASS_NAME,'JobsList_jobListItem__wjTHv')
        
        for post in posts:
            try:
                Links.append(post.find_element(By.CLASS_NAME,'JobCard_jobTitle___7I6y').get_attribute('href'))
                if len(Links) == 20:
                    break
            except:
                pass
        print(f'{len(Links)} jobs found for {keyword}')
    except:
        print("Keyword error")
    driver.quit()
    return Links

def get_data(links):
    list_job=[]
    for i in range(len(links)):
        try:
            options = Options()
            driver = webdriver.Chrome(options=options)
            options.add_argument("--headless")  # Add headless mode
            driver.get(links[i])
            
            try:
                sleep(2)
                plus = driver.find_element(By.CLASS_NAME,'JobDetails_showMore___Le6L')
                plus.click()
            except:
                print("No more")
        
            job={}
            sleep(1.5)
            soup = BeautifulSoup(driver.page_source,"html.parser")

            try:
                job['job_link'] = links[i]
            except:
                job['job_link'] = None
            try:
                job['job_name'] = soup.find('h1',{'class':"heading_Heading__BqX5J"}).text
            except:
                job['job_name'] = None
                
            try:
                job['job_text'] = soup.find('div',{'class':"JobDetails_jobDescription__uW_fK JobDetails_showHidden__C_FOA"}).text
            except:
                job['job_text'] = None
                
            try:
                job['job_company'] = soup.find('h4',{'class':'heading_Heading__BqX5J heading_Subhead__Ip1aW'}).text.split('\n')[0]
            except:
                job['job_company'] = None 

            try:
                job['job_location'] = soup.find('div',{'class':'JobDetails_location__mSg5h'}).text
            except:
                job['job_location'] = None
                
            try:
                if "alternance" in  soup.find('div',{'class':"JobDetails_jobDescription__uW_fK JobDetails_showHidden__C_FOA"}).text.lower():
                    job['job_type'] = "Alternance"
                elif "cdi" in  soup.find('div',{'class':"JobDetails_jobDescription__uW_fK JobDetails_showHidden__C_FOA"}).text.lower():
                    job['job_type'] = "CDI"
                elif "cdd" in  soup.find('div',{'class':"JobDetails_jobDescription__uW_fK JobDetails_showHidden__C_FOA"}).text.lower():
                    job['job_type'] = "CDD"
                elif "stage" in  soup.find('div',{'class':"JobDetails_jobDescription__uW_fK JobDetails_showHidden__C_FOA"}).text.lower():
                    job['job_type'] = "STAGE"
                elif "freelance" in soup.find('div',{'class':"JobDetails_jobDescription__uW_fK JobDetails_showHidden__C_FOA"}).text.lower() or "indépendant" in soup.find('div',{'class':"JobDetails_jobDescription__uW_fK JobDetails_showHidden__C_FOA"}).text.lower():
                    job['job_type']  = "freelance"
                else:
                    job['job_type'] = "autre"
            except:
                job['job_type'] = "autre"
                
            now = datetime.now()
            job['job_date'] = now.strftime("%Y-%m-%d")
            print(i+1,"Jobs extracted",end="\r")
            list_job.append(job)
        except:
            pass
        driver.quit()
    return pd.DataFrame(list_job)

def get_datas(Keywords):
    data = pd.DataFrame()
    for key in Keywords:
        links = get_links(key)
        df = get_data(links)
        data = pd.concat([data,df],axis=0)
    return data