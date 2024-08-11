#update
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.S3_hook import S3Hook
from airflow.models import Variable
from datetime import datetime, timedelta
import requests
import json

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Initialize the DAG
dag = DAG(
    'spotify_to_s3',
    default_args=default_args,
    description='Fetch Spotify data and upload to S3 sequentially',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Spotify API credentials
client_id = Variable.get('client_id')
client_secret = Variable.get('client_secret')

# Spotify playlist IDs
playlists = {
    'top_50_global': '37i9dQZEVXbMDoHDwVN2tF',
    'top_50_indonesia': '37i9dQZEVXbObFQZ3JLcXt',
    'top_50_viral_indo': '37i9dQZEVXbKpV6RVDTWcZ',
    'top_50_viral_global': '37i9dQZEVXbLiRSasKsNU9',
    'today_top_hits': '37i9dQZF1DXcBWIGoYBM5M'
}

def fetch_playlist_data(playlist_id, **kwargs):
    # Fetch access token
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']

    # Fetch playlist data
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    response = requests.get(playlist_url, headers=headers)
    playlist_data = response.json()

    # Push the data to XCom
    return playlist_data

def upload_to_s3(playlist_name, **kwargs):
    # Pull the playlist data from XCom
    ti = kwargs['ti']
    playlist_data = ti.xcom_pull(task_ids=f'fetch_data_{playlist_name}')
    
    # Convert playlist data to JSON
    json_data = json.dumps(playlist_data, indent=4)

    # Define S3 bucket and file name
    s3_bucket = <'your-s3-bucket'>
    s3_key = f'spotify_data/{playlist_name}.json'

    # Upload to S3
    s3 = S3Hook(aws_conn_id='aws_default')
    s3.load_string(string_data=json_data, key=s3_key, bucket_name=s3_bucket, replace=True)

# Create tasks for fetching and uploading each playlist
previous_task = None
for playlist_name, playlist_id in playlists.items():
    fetch_task = PythonOperator(
        task_id=f'fetch_data_{playlist_name}',
        python_callable=fetch_playlist_data,
        op_args=[playlist_id],
        provide_context=True,
        dag=dag,
    )

    upload_task = PythonOperator(
        task_id=f'upload_{playlist_name}_to_s3',
        python_callable=upload_to_s3,
        op_args=[playlist_name],
        provide_context=True,
        dag=dag,
    )

    if previous_task:
        previous_task >> fetch_task
    
    fetch_task >> upload_task
    previous_task = upload_task
