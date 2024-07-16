from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.S3_hook import S3Hook
from datetime import datetime, timedelta
import requests
import json
import base64
import os
from dotenv import load_dotenv
load_dotenv()


# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Initialize the DAG
dag = DAG(
    'spotify_to_s3',
    default_args=default_args,
    description='Fetch Spotify data and upload to S3',
    schedule_interval=timedelta(days=1),
    catchup=False,
)
var_client_id = os.getenv('client_id')
var_client_secret = os.environ.get('client_secret')


# Spotify API credentials
client_id = var_client_id
client_secret = var_client_secret

# Spotify playlist IDs
playlists = {
    'top_50_global': '37i9dQZEVXbMDoHDwVN2tF',
    'top_50_indonesia': '37i9dQZEVXbObFQZ3JLcXt',
    'top_50_viral_indo': '37i9dQZEVXbKpV6RVDTWcZ',
    'top_50_viral_global': '37i9dQZEVXbLiRSasKsNU9',
    'today_top_hits': '37i9dQZF1DXcBWIGoYBM5M'
}

def get_access_token():
    token_url = 'https://accounts.spotify.com/api/token'
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()
    
    token_data = {"grant_type": "client_credentials"}
    token_headers = {"Authorization": f"Basic {client_creds_b64}"}
    
    token_response = requests.post(token_url, data=token_data, headers=token_headers)
    access_token = token_response.json()['access_token']
    
    return access_token

def fetch_spotify_data(playlist_id, **kwargs):
    access_token = get_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    response = requests.get(url, headers=headers)
    data = response.json()
    
    # Store data to XCom
    kwargs['ti'].xcom_push(key=f'spotify_data_{playlist_id}', value=data)

def upload_to_s3(**kwargs):
    combined_data = {}
    for playlist_name, playlist_id in playlists.items():
        data = kwargs['ti'].xcom_pull(key=f'spotify_data_{playlist_id}', task_ids=f'fetch_{playlist_name}')
        combined_data[playlist_name] = data
    
    # Convert data to JSON string
    data_json = json.dumps(combined_data)
    
    # Write JSON data to a temporary file
    temp_file = '/tmp/spotify_data.json'
    with open(temp_file, 'w') as f:
        f.write(data_json)
    
    # Initialize S3 hook
    s3 = S3Hook('aws_default')
    
    # Upload file to S3
    s3.load_file(temp_file, 'spotify_data/spotify_data.json', bucket_name='project-rachman-2024', replace=True)
    
    # Remove temporary file
    os.remove(temp_file)

# Define fetch tasks
for playlist_name, playlist_id in playlists.items():
    fetch_task = PythonOperator(
        task_id=f'fetch_{playlist_name}',
        provide_context=True,
        python_callable=fetch_spotify_data,
        op_kwargs={'playlist_id': playlist_id},
        dag=dag,
    )
    
    # Set task dependencies
    if 'upload_task' in locals():
        upload_task.set_upstream(fetch_task)
    else:
        upload_task = PythonOperator(
            task_id='upload_to_s3',
            provide_context=True,
            python_callable=upload_to_s3,
            dag=dag,
        )
        upload_task.set_upstream(fetch_task)

