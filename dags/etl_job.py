from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta,datetime
from jobs.sql import insert_data, create_jobDB
from jobs.traitement import processing
import jobs.indeed as indeed
import jobs.jungle as jungle
import jobs.linkedin as linkedin
import jobs.glassdoor as glassdoor


def get_indeed_data():
    Keywords = ["data Scientist","data analyst","data engineer","web developer",'mobile developer']
    indeed_path = '/home/amine/airflow/dags/jobs/indeed.csv'
    df = indeed.get_datas(Keywords)
    df.dropna(inplace=True)
    df.to_csv(indeed_path,index=False)
    print("Done!")

def get_jungle_data():
    jungle_path = '/home/amine/airflow/dags/jobs/jungle.csv'
    Keywords = ["data Scientist","data analyst","data engineer","web developer",'mobile developer']
    df = jungle.get_datas(Keywords)
    df.dropna(inplace=True)
    df.to_csv(jungle_path,index=False)
    print("Done!")


def get_glassdoor_data():
    glassdoor_path = '/home/amine/airflow/dags/jobs/glassdoor.csv'
    Keywords = ["data Scientist","data analyst","data engineer","web developer",'mobile developer']

    df = glassdoor.get_datas(Keywords)
    df.dropna(inplace=True)
    df.to_csv(glassdoor_path,index=False)
    print("Done!")

def get_linked_data():
    Keywords = ["data Scientist","data analyst","data engineer","web developer",'mobile developer']
    Locations = ["france","Tunisie"]
    linked_path = '/home/amine/airflow/dags/jobs/linkedIn.csv'

    driver = linkedin.connect()
    df = linkedin.get_datas(driver,Keywords,Locations)
    df.dropna(inplace=True)
    df.to_csv(linked_path,index=False)
    print("Done!")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 7, 15),
    'email': ['amyne095@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG('jobs_ingestion',
         default_args=default_args,
         schedule_interval='0 19 * * *',
         catchup=False
         ) as dag:

    task1 = PythonOperator(
        task_id='jungle_scraper',
        python_callable=get_jungle_data,
        provide_context=True,
    )
    task2= PythonOperator(
        task_id='indeed_scaper',
        python_callable=get_indeed_data,
        provide_context=True,
    )
    task3= PythonOperator(
        task_id='linkedIn_scraper',
        python_callable=get_linked_data,
        provide_context=True,
    )
    task4= PythonOperator(
        task_id='glassdoor_scraper',
        python_callable=get_glassdoor_data,
        provide_context=True,
    )
    task5= PythonOperator(
        task_id='Data_processing',
        python_callable=processing,
        provide_context=True,
    )
    task6= PythonOperator(
        task_id='Create_Job_Table',
        python_callable=create_jobDB,
        provide_context=True,
    )
    task7= PythonOperator(
        task_id='Loading_Data_to_DataBase',
        python_callable=insert_data,
        provide_context=True,
    )
    
    #Set task dependencies
    task1 >> task2 >> task3 >> task4 >> task5 >> task6 >> task7

print('DAG defined successfully')