import tempfile
import pandas as pd
import streamlit as st
from cv_parser import (recommend_jobs, read_data, job_by_source, job_by_type, extract_source,
                 job_type_by_source, most_offered_company, top_skills,most_frequent_jobs)
from datetime import datetime, timedelta
import plotly.express as px 



st.set_page_config(page_title="Job Recommendation App", layout="wide")
st.markdown(
    """
        <style>
            .{
                margin:0;
                
            }
            .st-emotion-cache-6qob1r {
                position: relative;
                height: 100%;
                width: 100%;
                overflow: overlay;
            }   
            .st-emotion-cache-1gv3huu {
                position: relative;
                top: 2px;
                background-color: rgb(240, 242, 246);
                z-index: 999991;
                min-width: fit-content;
                max-width: fit-content;
                transform: none;
                transition: transform 300ms ease 0s, min-width 300ms ease 0s, max-width 300ms ease 0s;
            }

            .st-emotion-cache-1whx7iy p {
                word-break: break-word;
                margin-bottom: 0px;
                font-size: 20px;
                font-weight : bold;
            }
        </style>
        """,
        unsafe_allow_html=True
)

nav_options = {
    "Accueil": "🏠",
    "Job Recommender": "🔍",
    "Dashboard": "📊"
}
nav_selection = st.sidebar.radio(
    "Navigation",
    options=list(nav_options.keys()),
    format_func=lambda x: f"{nav_options[x]} {x}"
)

def accueil():
    st.title("Welcome to the Job Recommendation App")

    # Create a centered layout using columns
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(
            "The *Job Recommendation App* is designed to help you find the most relevant job opportunities based on your skills and preferences. Here's a brief overview of what you can do with this app:"
        )

        st.header("Features:")
        st.write(
            "- *Job Recommender*: Upload your CV and get personalized job recommendations based on your skills and experience. Adjust filters to refine your search based on the time period and the number of job recommendations you want to see."
        )
        st.write(
            "- *Dashboard*: Visualize job data with interactive charts. Explore various metrics such as the most frequent jobs, top skills, job sources, job types, and more."
        )

        st.header("How it Works:")
        st.write(
            "1. *Upload Your CV*: Start by uploading your CV in PDF format. The app will analyze your document to understand your skills and experience."
        )
        st.write(
            "2. *Set Filters*: Choose a time period to filter job postings (e.g., Last Day, Last Week, Last Month) and specify the number of job recommendations you want."
        )
        st.write(
            "3. *Get Recommendations*: The app will provide you with a list of job opportunities that match your profile. You can view details and apply directly through provided links."
        )
        st.write(
            "4. *Explore Data*: Navigate to the Dashboard to see visualizations of job trends, skills, and sources based on the available job data."
        )

        st.header("Benefits:")
        st.write(
            "- *Personalized Recommendations*: Get job suggestions tailored to your skills and experience."
        )
        st.write(
            "- *Interactive Visualizations*: Analyze job market trends and data through interactive charts and graphs."
        )
        st.write(
            "- *Easy to Use*: Simple and intuitive interface to quickly find and explore job opportunities."
        )

        st.write(
            "If you have any questions or need help using the app, feel free to reach out to our support team."
        )
def recommender():
    st.title("Job Recommender System")

    col1, _ = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Choose a CV (PDF only)", type="pdf")

    if uploaded_file is not None:
        
        x,y,z = st.columns([1,1,5])
        with x:
            time_filter = st.selectbox(
                'Select Time Period',
                options=['All Time', 'Last Day', 'Last Week', 'Last Month']
            )
        with y:
            # Number input field
            number = st.number_input(
                label="Enter a number",
                min_value=0,  # Minimum value
                max_value=100,  # Maximum value
                value=10,  # Default value
            )

        data = read_data()
        data = filter_data_by_time(data, time_filter)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        st.subheader("Best jobs found")
        df = recommend_jobs(data,pdf_path, number)

        num_columns = 3  # Adjust this number to change how many cards per row
        for i in range(0, len(df), num_columns):
            cols = st.columns(num_columns)
            for col, (_, row) in zip(cols, df.iloc[i:i + num_columns].iterrows()):
                with col:
                    st.markdown(
                        f"""
                        <div style="border: 1px solid #e6e6e6; 
                                    border-radius: 5px; padding: 15px; 
                                    margin-bottom: 10px; 
                                    box-shadow: 5px 8px 15px rgba(0,0,0,0.4);">
                            <h4 style="color:#4a90e2">{row['job_name']}</h4>
                            <p><b>Location:</b> {row['job_location']}</p>
                            <p>{row['job_text'][:150]}...</p>
                            <a href="{row['job_link']}">Read more</a>
                        </div>
                        """, unsafe_allow_html=True
                    )



# Filtering function based on selected time period
def filter_data_by_time(df, period):
    if period == 'Last Day':
        start_date = datetime.now() - timedelta(days=1)
    elif period == 'Last Week':
        start_date = datetime.now() - timedelta(weeks=1)
    elif period == 'Last Month':
        start_date = datetime.now() - timedelta(30)
    else:
        return df  # No filtering for 'All Time'

    df['job_date'] = pd.to_datetime(df['job_date'])
    return df[df['job_date'] >= start_date]

  
def dashbord_page():
    st.title("Dashboard")

    x, y, z = st.columns([1, 3, 3])
    with x:
        time_filter = st.selectbox(
            'Select Time Period',
            options=['All Time', 'Last Day', 'Last Week', 'Last Month']
        )

    df = read_data()

    # Apply time filter
    df = filter_data_by_time(df, time_filter)

    # Add job name categorization
    

    col1, col2 = st.columns(2)

    with col1:
        fig_pie = most_frequent_jobs(df,'job_name')
        st.plotly_chart(fig_pie)

    with col2:
        fig5 = top_skills(df, 'skills')
        st.plotly_chart(fig5)

    with col1:
        fig1 = job_by_source(df)
        st.plotly_chart(fig1)
        
    with col2:
        fig3 = job_by_type(df)
        st.plotly_chart(fig3)       

    with col1:
        fig2 = most_offered_company(df)
        st.plotly_chart(fig2)


    with col2:
        fig4 = job_type_by_source(df)
        st.plotly_chart(fig4)
    
    
# Display the selected page
if nav_selection == "Accueil":
    accueil()
elif nav_selection == "Job Recommender":
    recommender()
elif nav_selection == "Dashboard":
    dashbord_page()