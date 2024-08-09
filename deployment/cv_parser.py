import cv2
import fitz 
import psycopg2
import pytesseract
import pandas as pd
from PIL import Image
from inference_sdk import InferenceHTTPClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px 
from collections import Counter
import re 

def pdf_to_jpg(pdf_path):
    pdf_document = fitz.open(pdf_path)
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        output_path = f"cv_{page_number + 1}.jpg"
        img.save(output_path, "JPEG")
        return output_path
    

def get_skills_cv(path):
    image_path = pdf_to_jpg(path)
    CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="BIrE2FC1DoCP2tdXB9MA"
    )
    
    # Define the model ID
    model_id = "resume-parser-bchlq/1"
    result = CLIENT.infer(image_path, model_id=model_id)
    
    image = cv2.imread(image_path)

    # Extract the 'Skills' section from the result
    skills_section = None
    for prediction in result['predictions']:
        if prediction['class'] == 'skills':
            x = int(prediction['x'] - prediction['width'] / 2)
            y = int(prediction['y'] - prediction['height'] / 2)
            width = int(prediction['width'])
            height = int(prediction['height'])
            
            skills_image = image[y:y+height, x:x+width]            
            skills_image_rgb = cv2.cvtColor(skills_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(skills_image_rgb)
            skills_text = pytesseract.image_to_string(pil_image)
            
            return skills_text
    else:
        print("No 'Skills' section found in the image.")


def connect():
    try:
        conn = psycopg2.connect("host=127.0.0.1 dbname=postgres user=postgres password=30051994")
        print('DB connected successfully')
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        raise
    return conn

def get_data():
    try:
        conn = connect()
        cursor = conn.cursor()

        fetch_data_sql = "SELECT job_link, job_name, job_text, job_company, job_location, job_type, job_date, skills FROM jobs_data;"

        try:
            cursor.execute(fetch_data_sql)
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=colnames)
            df.drop_duplicates(subset=['skills'],ignore_index=True)

            return df

        except Exception as ex:
            print(f"An error occurred while fetching data: {ex}")

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error connecting to the database: {e}")    
# cv_parser.py

import pandas as pd

def extract_source(url):
    if 'linkedin.com' in url:
        return 'LinkedIn'
    elif 'indeed.com' in url:
        return 'Indeed'
    elif 'glassdoor.com' in url:
        return 'Glassdoor'
    elif 'welcomejungle.com' in url:
        return 'Welcome Jungle'
    else:
        return 'Unknown'

    


def recommend_jobs(df,path, top_n=100):
    skills_cv = get_skills_cv(path)
    
    # Prepare the lists of skills
    job_skills_list = df['skills'].tolist()
    skills_cv_list = [skills_cv]
    all_skills = skills_cv_list + job_skills_list

    # Vectorize the skills
    vectorizer = TfidfVectorizer()
    vectorizer.fit(all_skills)
    cv_vector = vectorizer.transform(skills_cv_list)
    job_vectors = vectorizer.transform(job_skills_list)

    # Compute similarity scores
    similarity_scores = cosine_similarity(cv_vector, job_vectors).flatten()
    
    # Get the top N job indices based on similarity scores
    top_indices = similarity_scores.argsort()[-top_n:][::-1]
    
    # Extract the recommended job names and their corresponding scores
    recommendations = df.iloc[top_indices][['job_link','job_name', 'skills','job_location','job_text']].copy()
    recommendations['score'] = similarity_scores[top_indices]
    
    return recommendations       

def determine_source(url):
    if "linkedin" in url:
        return "LinkedIn"
    elif "indeed" in url:
        return "Indeed"
    elif "welcometothejungle" in url:
        return "Welcome to the Jungle"
    elif "glassdoor" in url:
        return "Glassdoor"
    else:
        return "Unknown"
    

def read_data():
    data = get_data()
    df = data.dropna()
    df['source'] = df['job_link'].apply(determine_source)
    df['job_type'] = df['job_type'].replace('AUTRE', 'Not Specified')
    return df

def job_by_source(df):
    fig = px.pie(df, 
                 names='source', 
                 title='Distribution of Jobs by Source',
                 color='source',  
                 color_discrete_sequence=px.colors.qualitative.Plotly, 
                 hole=0.3)  
    
    fig.update_layout(
        title_text='Distribution of Jobs by Source',
        title_font_size=24,
        title_x=0.5,
        title_xanchor='center',  
        legend_title_text='Source',
        legend=dict(
            orientation='v', 
            yanchor='bottom',
            y=-0.2,
            xanchor='right',
            x=1
        ),
        margin=dict(t=50, b=50, l=50, r=50)  
    )   
    
    fig.update_traces(
        textinfo='label+percent', 
        pull=[0.1] * len(df['source'])  
    )
    
    return fig

def job_by_type(df):
    fig = px.pie(df, 
                 names='job_type', 
                 title='Job Counts by Type',
                 color='job_type',  
                 color_discrete_sequence=px.colors.qualitative.Plotly, 
                 hole=0.3)  
    
    fig.update_layout(
        title_text='Job Counts by Type',
        title_font_size=24,
        title_x=0.5,
        title_xanchor='center',  
        legend_title_text='Job Type',
        legend=dict(
            orientation='v',  
            yanchor='bottom',
            y=-0.2,
            xanchor='left',
            x=1
        ),
        margin=dict(t=50, b=50, l=50, r=50)  
    )
    

    fig.update_traces(
        textinfo='label+percent',  
        pull=[0.05] * len(df['job_type'])
    )
    
    return fig
def cut_name(text):
    return text[:20]

def most_offered_company(df,top_n=10):
    data= df[df['job_company'] != 'Not found']
    company_counts = data['job_company'].value_counts().reset_index()
    company_counts.columns = ['job_company', 'count']
    top_companies = company_counts.head(top_n)
    top_companies['job_company'] = top_companies['job_company'].apply(cut_name)

    fig = px.bar(top_companies, x='job_company', y='count', title='Most Frequently Offered Companies',color='job_company')
    fig.update_layout(
        title_font_size=24,
    )
    
    return fig


def job_type_by_source(df):
    fig = px.histogram(df, 
                    x='source', 
                    color='job_type', 
                    color_discrete_sequence=px.colors.qualitative.Plotly, 
                    title='Job Types by Source Link',
                    labels={'source': 'Source Link', 'count': 'Job Count'},
                    category_orders={'job_type': df['job_type'].value_counts().index.tolist()})

    fig.update_layout(
        barmode='stack', 
        title_font_size=24,
        xaxis_title='Source Link',
        yaxis_title='Count',
        legend_title='Job Type',
    )
    return fig

def top_skills(df, skills_column, top_n=15):
    all_skills = df[skills_column].dropna().str.split(',').explode().str.strip()
    skill_counts = Counter(all_skills)
    
    skill_df = pd.DataFrame(skill_counts.items(), columns=['Skill', 'Count'])
    skill_df = skill_df.sort_values(by='Count', ascending=False)
    top_skills_df = skill_df.head(top_n)
    
    fig = px.bar(top_skills_df, 
                 x='Skill', 
                 y='Count', 
                 title=f'Top {top_n} Most Common Job Skills',
                 labels={'Skill': 'Skill', 'Count': 'Count'},
                 color='Count',
                 color_continuous_scale='Viridis')
    
    fig.update_layout(
        xaxis_title='Skill',
        yaxis_title='Count',
        title_font_size=24,
        xaxis_tickangle=-45,
        title_xanchor='center',
        title_x=0.5
    )
    
    return fig  


def most_frequent_jobs(df, job_column, top_n=10):
    KEYWORD_SYNONYMS = {
    'data analyst': [
        'data analyst', 'analyse de données', 'analyst', 'quantitative analyst', 'data analytics', 'data investigator',
        'data examiner', 'report analyst', 'data consultant', 'data researcher', 'data specialist', 'data evaluator',
        'information analyst', 'analytics consultant', 'performance analyst','analyste de données'
    ],
    'data scientist': [
        'data scientist', 'scientifique des données', 'data science', 'data science specialist', 'machine learning engineer',
        'ML scientist', 'statistician', 'quantitative researcher', 'data modeler', 'AI engineer', 'artificial intelligence engineer',
        'data researcher', 'predictive analyst', 'data strategist', 'data developer','sciences de données','power bi','powerbi'
    ],
    'data engineer': [
        'data engineer', 'ingénieur des données','ingénieur data', 'data engineering', 'ETL developer', 'data architect', 'data systems engineer',
        'data pipeline engineer', 'data warehouse engineer', 'big data engineer', 'data infrastructure engineer', 'data integration engineer',
        'data operations engineer', 'data operations specialist', 'data platform engineer'
    ],
    'web developer': [
        'web developer', 'développeur web', 'full stack','fullstack', 'front-end', 'back-end ', 'web',
        'web designer', 'UI developer', 'UX developer', 'site developer', 'application developer', 'software developer',
        'web application developer', 'web systems developer', 'web consultant', 'web architect','devops'
    ],
    'mobile developer': [
        'mobile developer', 'développeur mobile', 'iOS developer', 'Android developer', 'mobile app developer', 'mobile application developer',
        'mobile software engineer', 'mobile UI/UX designer', 'app developer', 'cross-platform developer', 'mobile engineer',
        'flutter developer', 'react native developer', 'mobile systems developer', 'mobile technology specialist'
    ],
    'project manager': [
        'project manager', 'chef de projet', 'senior project manager', 'project coordinator', 'project leader', 'project director',
        'program manager', 'project supervisor', 'project planner', 'project administrator', 'project executive', 'project controller'
    ],
    'software engineer': [
        'software engineer', 'logiciel', 'software', 'software architect', 'programmer', 'application developer',
        'system software engineer', 'software designer', 'software consultant', 'software development engineer', 'code developer',
        'software development specialist'
    ],
    'data architect': [
        'data architect', 'architecte de données', 'data modeler', 'data systems architect', 'information architect', 'data engineer',
        'data structure engineer', 'data strategy consultant', 'data infrastructure architect', 'data integration architect'
    ]
    }
    def categorize_job_name(job_name):
        job_name_lower = job_name.lower()
        for category, synonyms in KEYWORD_SYNONYMS.items():
            if any(re.search(r'\b' + re.escape(synonym) + r'\b', job_name_lower) for synonym in synonyms):
                return category
        return job_name

    job_titles = df[job_column].dropna()
    job_titles = df['job_name'].apply(categorize_job_name)
    
    job_counts = Counter(job_titles)
    
    job_df = pd.DataFrame(job_counts.items(), columns=['Job Title', 'Count'])
    job_df = job_df.sort_values(by='Count', ascending=False)
    
    # Select top N job titles
    top_jobs_df = job_df.head(top_n)
    
    # Create a bar chart for the most frequent job titles
    fig = px.bar(top_jobs_df, 
                 x='Job Title', 
                 y='Count', 
                 title=f'Top {top_n} Most Common Job Titles',
                 labels={'Job Title': 'Job Title', 'Count': 'Count'},
                 color='Count',
                 color_continuous_scale='Viridis')
    
    # Update layout for better design
    fig.update_layout(
        xaxis_title='Job Title',
        yaxis_title='Count',
        title_font_size=24,
        title_xanchor='center',  
        xaxis_tickangle=-15,  
        title_x=0.5
    )
    
    return fig
                                                                                                                               