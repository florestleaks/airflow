
FROM apache/airflow:2.8.1-python3.11 as ci

RUN pip install --progress-bar off --user --upgrade pip
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         flex bison automake libtool make gcc pkg-config libssl-dev pkg-config libxml2-dev libxmlsec1-dev libxmlsec1-openssl git \
  && apt-get autoremove -y --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*


USER airflow

COPY  soar-1.13.0-py3-none-any.whl .
RUN pip install soar-1.13.0-py3-none-any.whl

RUN pip install connexion[swagger-ui] apache-airflow-providers-mongo apache-airflow-providers-mongo apache-airflow-providers-mysql apache-airflow-providers-neo4j apache-airflow-providers-slack apache-airflow-providers-telegram
