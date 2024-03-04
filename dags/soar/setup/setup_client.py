from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from pymongo import MongoClient
from soar.clientmanager.client_data_import import ClientManagerImport
from soar.frameworks_drivers.gitmanager import GitManager
from airflow.models import Variable
from airflow.models import Variable

# Define the Python callable function
def import_client_data():


    git_repo_url = Variable.get("GIT_REPO_CLIENT_MONITORING_URL")
    access_token = Variable.get("GIT_REPO_TOKEN")
    db_url = Variable.get("MONGODB_URL")
    git_manager = GitManager(git_repo_url, access_token)

    db_real = MongoClient(db_url)
    manager = ClientManagerImport(db_client=db_real, git_manager=git_manager)
    manager.import_from_json(meta_update=True)

# Define default arguments for the DAG
default_args = {
    'owner': 'soar_setup',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 30),
    'email': Variable.get("EMAIL_SETUP_MANAGER"),
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'SOAR_SETUP_CLINT_DATA_IMPORT_2',
    default_args=default_args,
    description='DAG for importing client data from Git into MongoDB',
    schedule_interval=timedelta(days=1),
    catchup=False
)

# Define the PythonOperator
import_client_data_task = PythonOperator(
    task_id='import_client_data',
    python_callable=import_client_data,
    dag=dag,
)

# Set the task sequence
import_client_data_task
