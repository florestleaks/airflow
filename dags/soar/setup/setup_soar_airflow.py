from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from soar.config.soar_config import SoarConfiguration
from airflow.models import Variable

# Define the Python function
def update_airflow_vars():
    soar_config = SoarConfiguration()
    soar_config.update_airflow_variables()

# Define default arguments for the DAG
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
    'SOAR_SETUP_UPDATE_AIRFLOW_VARIABLES_1',
    default_args=default_args,
    description='DAG to update Airflow variables from SoarConfiguration',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 30),
    catchup=False
)

# Define the PythonOperator
update_vars_operator = PythonOperator(
    task_id='update_airflow_variables_dag',
    python_callable=update_airflow_vars,
    dag=dag,
)

# Set the task sequence
update_vars_operator
