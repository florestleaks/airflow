from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from pymongo import MongoClient
from airflow.models import Variable
from pymongo import MongoClient
from airflow.operators.dummy_operator import DummyOperator

from soar.frameworks_drivers.crawler.crawler_manager import CrawlerManager
from soar.frameworks_drivers.crawler.base_crawler import BaseCrawler
from soar.frameworks_drivers.ticket_system.thehive.thehive_internal_mods_api.thehive_datatype import (
    CaseDataType,
)
from soar.frameworks_drivers.ticket_system.thehive.thehive_internal_mods_api.thehive_manager_case.create_case import (
    CreateCase,
)
from soar.frameworks_drivers.ticket_system.thehive.thehive_internal_mods_api.thehive_manager_case_comment_template import (
    CaseCommentTemplate,
)
from soar.frameworks_drivers.ticket_system.thehive.thehive_internal_mods_api.thehive_manager_case_comment_template.template_render import (
    TemplateRenderer,
)
from soar.frameworks_drivers.ticket_system.thehive.thehive_internal_mods_api.thehive_session import (
    SessionThehive,
)

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from pymongo import MongoClient

# Define default arguments for the DAG
default_args = {
    'owner': 'soar_monitoring',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 30),
    'email': Variable.get("EMAIL_SOAR_MONITORING"),
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'CTI_MONITORING_CRAWLER_WITHOUT_CREDENTIAL_WEB',
    default_args=default_args,
    description='A DAG for web crawling with dynamic tasks',
    schedule_interval=timedelta(days=1),
)


def current_unix_timestamp():
    from datetime import datetime, timezone
    # Obtendo a data e hora atual no fuso horário UTC
    data = datetime.now(timezone.utc)  # Use timezone.utc to represent UTC timezone
    timestamp_convertido = int(data.timestamp() * 1000)  # Multiplying by 1000 to get milliseconds

    return timestamp_convertido


def run_crawler(crawler_run):
    db_url = Variable.get("MONGODB_URL")
    db_real = MongoClient(db_url)
    print(crawler_run)
    crawler = BaseCrawler(base_url=crawler_run['url'], depth=crawler_run['depth'], timeout=crawler_run['timeout'], db_client=db_real)
    crawler.crawl(url=crawler_run["url"])

    def convert_matches_to_string(matches):
        string_matches = []
        for match in matches:
            string_match = {key: str(value) for key, value in match.items()}
            string_matches.append(string_match)
        return string_matches

    # Suponha que crawler.all_matches seja a sua lista de dicionários
    all_matches = crawler.get_yara_matches()
    stringified_matches = convert_matches_to_string(all_matches)
    return stringified_matches


def create_thehive_ticket(**kwargs):
    ti = kwargs['ti']
    index = kwargs['index']
    crawler_data = ti.xcom_pull(task_ids=f'run_crawler_{index}')
    for chamados in crawler_data:
        # Create an instance of the TemplateRenderer with the CASE_MONITORING_DNS_ALERT_YARA template
        dns_alert_yara_renderer = TemplateRenderer(
            CaseCommentTemplate.CASE_MONITORING_DNS_ALERT_YARA,
            dominio_suspeito=chamados["link_match"],
            regra_deteccao=chamados["rule_name"],
            cliente=chamados["client_match"],
        )
        # Render the template
        dns_alert_yara_comment = dns_alert_yara_renderer.render()
        # Create Case Data
        case_data = CaseDataType(
            title=f"Nome da Regra: {chamados['rule_name']} | Condição YARA: {chamados['yara_match_condition']} | Correspondência de Link: {chamados['link_match']} | Cliente: {chamados['client_match']} | Tipo de Regra: {chamados['rule_type']}",
            description=dns_alert_yara_comment,
            severity=3,
            tags=[chamados["client_match"], chamados["rule_type"]],
            createdAt=current_unix_timestamp(),
            startDate=current_unix_timestamp(),
        )
        # Retrieve TheHive configurations
        thehive_url = Variable.get("THEHIVE")
        thehive_api_key = Variable.get("THEHIVE_API_SERVICE")
        # Initialize TheHive session with API key
        session = SessionThehive(base_url=thehive_url)
        session.set_api_key(thehive_api_key)

        # Create a case using TheHive API
        case_creator = CreateCase(session)
        status_code = case_creator.create(case_data)


db_url = Variable.get("MONGODB_URL")
db_real = MongoClient(db_url)
crawler_manager = CrawlerManager(db_real)
crawler_without_credential_web = crawler_manager.get_all_documents_by_collection()['crawler_without_credential_web']

# Inicializa uma lista vazia para manter o controle das tarefas de rastreamento
crawl_tasks = []

# Cria o DummyOperator como ponto de partida
start_operator = DummyOperator(
    task_id='start_execution',
    dag=dag,
)

for index, crawler_run in enumerate(crawler_without_credential_web):
    crawl_task = PythonOperator(
        task_id=f'run_crawler_{index}',
        python_callable=run_crawler,
        op_kwargs={'crawler_run': crawler_run},
        dag=dag,
    )

    # Configura a tarefa de rastreamento para depender do start_operator
    crawl_task.set_upstream(start_operator)
    crawl_tasks.append(crawl_task)  # Adiciona cada tarefa de rastreamento à lista

    format_task = PythonOperator(
        task_id=f'create_thehive_ticket_{index}',
        python_callable=create_thehive_ticket,  # Certifique-se de que o nome da função está correto
        op_kwargs={'index': index},
        dag=dag,
    )

    # Define dependências usando instâncias de tarefa
    format_task.set_upstream(crawl_task)
