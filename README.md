
# Spotify to S3 Data Pipeline

This project sets up an Apache Airflow pipeline to fetch data from Spotify playlists and upload it to an S3 bucket. The environment is containerized using Docker Compose.

## Project Structure

- `upload_data_s3.py`: Airflow DAG definition to fetch Spotify data and upload to S3.
- `docker-compose.yml`: Docker Compose configuration to set up the necessary environment.

## Prerequisites

- Docker
- Docker Compose

## Setup and Running the Project

### Step 1: Clone the Repository

```sh
git clone <repository_url>
cd <repository_directory>
```

### Step 2: Create Environment Variables File

Create a `.env` file in the root directory with the following content:

```env
AIRFLOW_UID=50000
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow
AWS_ACCESS_KEY_ID=<your_aws_access_key_id> # Connection in airflow
AWS_SECRET_ACCESS_KEY=<your_aws_secret_access_key> # Connection in airflow
CLIENT_ID = <your-spotify-client-id> # Variable in airflow
SECRET_key = <your-spotify-secret-key> # Variable in airflow
S3_BUCKET_NAME=<your_s3_bucket_name>
```

### Step 3: Start the Docker Compose Services

```sh
docker-compose up -d
```

This command will start all the necessary services in the background.

### Step 4: Initialize Airflow

Run the following command to initialize the Airflow environment:

```sh
docker-compose run airflow-init
```

### Step 5: Access Airflow Web Interface

Open your web browser and go to `http://localhost:8080` to access the Airflow web interface.

### Step 6: Trigger the DAG

In the Airflow web interface, trigger the `spotify_to_s3` DAG to start fetching data from Spotify and uploading it to S3.

## Notes

- Ensure that your AWS credentials and S3 bucket name are correctly set in the `.env` file.
- Modify the playlist IDs in the `upload_data_s3.py` script as needed.
- You can check the logs in the `logs` directory to troubleshoot any issues.
