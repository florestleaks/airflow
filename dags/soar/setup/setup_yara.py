from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from pymongo import MongoClient
from soar.clientmanager.client_data_manager import ClientManager
from soar.config.soar_config import SoarConfiguration
from soar.frameworks_drivers.gitmanager import GitManager
from soar.frameworks_drivers.soar_yara.yara_import import YaraRulesImporter
from airflow.models import Variable

# Define the Python callable function
def import_yara_rules():
    git_repo_url = Variable.get("GIT_REPO_CLIENT_YARA_RULES_URL")
    access_token = Variable.get("GIT_REPO_TOKEN")
    git_manager = GitManager(git_repo_url, access_token)
    db_url = Variable.get("MONGODB_URL")
    client = MongoClient(db_url)
    client_manager = ClientManager(client)
    print(client_manager.list_all_clients())

    importer = YaraRulesImporter(
        directory=None,
        clients=client_manager.list_all_clients(),
        db_client=client,
        overwrite=True,
        git_manager=git_manager,
    )
    importer.import_rules(meta_update=True)

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
    'SOAR_SETUP_YARA_RULES_IMPORT_3',
    default_args=default_args,
    description='DAG for importing YARA rules from Git into MongoDB',
    schedule_interval=timedelta(days=1),
    catchup=False
)

# Define the PythonOperator
import_yara_rules_task = PythonOperator(
    task_id='import_yara_rules',
    python_callable=import_yara_rules,
    dag=dag,
)

# Set the task sequence
import_yara_rules_task
