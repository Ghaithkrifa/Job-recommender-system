import psycopg2
import pandas as pd
import time

def connect():
    try:
        conn = psycopg2.connect("host=127.0.0.1 dbname=postgres user=postgres password=aminecss")
        print('DB connected successfully')
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        raise
    return conn



def create_jobDB():
    try:
        conn = psycopg2.connect("host=127.0.0.1 dbname=postgres user=postgres password=aminecss")
        conn.set_session(autocommit=True)
        time.sleep(3)
        cursor = conn.cursor()
        create_table_sql = '''
        CREATE TABLE jobs_data (
            id SERIAL PRIMARY KEY,
            job_link VARCHAR,
            job_name VARCHAR(255),
            job_text TEXT,
            job_company VARCHAR(255),
            job_location VARCHAR(255),
            job_type VARCHAR(50),
            job_date DATE,
            skills VARCHAR
        );
        '''
        try:
            cursor.execute(create_table_sql)
            print('Table created successfully')
        except:
            print('Table exists')
        conn.close()
    except Exception as e:
        print(f"Error creating table: {e}")
        raise


def insert_data():
    path = '/home/amine/airflow/dags/jobs/jobs_daily.csv'
    df = pd.read_csv(path)
    df = df.dropna()
    
    
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(path)
        df = df.dropna()
        conn = connect()
        cursor = conn.cursor()
        
        # Iterate through the DataFrame and insert each row into the table
        i = 0
        for _, row in df.iterrows():
            insert_sql = '''
            INSERT INTO jobs_data (job_link, job_name, job_text, job_company, job_location, job_type, job_date, skills)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            '''
            cursor.execute(insert_sql, (
                row['job_link'], row['job_name'], row['job_text'], row['job_company'],
                row['job_location'], row['job_type'], row['job_date'], row['skills']
            ))
            print(i+1,"Jobs inserted",end='\r')
        conn.commit()
        print('Data inserted successfully from CSV')
        conn.close()
    except Exception as e:
        print(f"Error inserting data from CSV: {e}")
        raise