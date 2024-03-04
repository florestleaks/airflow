from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from pymongo import MongoClient
from soar.frameworks_drivers.crawler.crawler_manager import CrawlerManager
from airflow.models import Variable

def mongo_crawler_task():

    db_url = Variable.get("MONGODB_URL")
    db_real = MongoClient(db_url)
    crawler_manager = CrawlerManager(db_real)
    crawler_manager.import_collections(meta_update=True)

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

dag = DAG(
    'SOAR_SETUP_UPDATE_CRAWLER_URLS_4',
    default_args=default_args,
    description='A simple DAG to interact with MongoDB',
    schedule_interval=timedelta(days=1),
)

t1 = PythonOperator(
    task_id='mongo_crawler_task',
    python_callable=mongo_crawler_task,
    dag=dag,
)

t1
