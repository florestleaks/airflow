#!/usr/bin/bash

# Cores para saída
RED="\033[01;31m"
GREEN="\033[01;32m"
YELLOW="\033[01;33m"
BLUE="\033[01;34m"
BOLD="\033[01;01m"
RESET="\033[00m"

# Rastreamento de etapas
STAGE=0
TOTAL=5  # Número total de etapas

# Atualiza o progresso
function update_progress() {
    STAGE=$((STAGE+1))
    echo -e "${BLUE}Etapa (${STAGE}/${TOTAL}):${RESET} $1"
}

# Definição de variáveis
IMAGE_NAME="registry.florestleaks.com/florestleaks/soar/infra/airflow/florestleaks_airflow"
USER_FILE="usuarios_airflow.json"  # Nome do arquivo JSON atualizado

# Etapa 1: Verificar e inicializar o banco de dados do Airflow
update_progress "Verificando e inicializando o banco de dados do Airflow se necessário..."

# Verificar se o banco de dados precisa ser inicializado
db_check=$(docker-compose run -T airflow-cli db check 2>&1)
if [[ $db_check == *"Connection successful"* ]]; then
    echo -e "${YELLOW}Inicializando o banco de dados do Airflow...${RESET}"
    docker-compose run -T airflow-cli db migrate
    echo -e "${GREEN}Banco de dados do Airflow inicializado.${RESET}"
else
    echo -e "${GREEN}Banco de dados do Airflow já está inicializado.${RESET}"
fi

# Etapa 2: Verificar a última versão da imagem Docker
update_progress "Verificando a última versão da imagem Docker..."
if [[ "$(docker images -q $IMAGE_NAME:latest 2> /dev/null)" == "" ]]; then
    echo -e "${YELLOW}Construindo a última versão da imagem Docker...${RESET}"
    docker build -t $IMAGE_NAME:latest . > /dev/null 2>&1
else
    echo -e "${GREEN}A última versão da imagem Docker já está disponível.${RESET}"
fi

# Etapa 2: Verificar a existência do arquivo CSV
update_progress "Verificando a existência do arquivo CSV de usuários..."
if [ ! -f "$USER_FILE" ]; then
    echo -e "${RED}Arquivo de usuários não encontrado: $USER_FILE${RESET}"
    exit 1
else
    echo -e "${GREEN}Arquivo de usuários encontrado.${RESET}"
fi

# Etapa 3: Verificar a existência dos usuários no Airflow e criar com senha aleatória
update_progress "Verificando usuários existentes no Airflow e criando novos usuários..."

existing_users=$(docker-compose run -T airflow-cli users list 2> /dev/null | awk '{print $1}' | sort)

# Obter a contagem de usuários no arquivo JSON
user_count=$(jq '. | length' "$USER_FILE")

# Iterar sobre cada usuário no arquivo JSON
for ((i = 0 ; i < user_count ; i++)); do
    username=$(jq -r ".[$i].username" "$USER_FILE")
    firstname=$(jq -r ".[$i].firstname" "$USER_FILE")
    lastname=$(jq -r ".[$i].lastname" "$USER_FILE")
    email=$(jq -r ".[$i].email" "$USER_FILE")
    role=$(jq -r ".[$i].role" "$USER_FILE")

    if ! [[ $existing_users =~ $username ]] && [ "$username" != "username" ]; then
        echo -e "${YELLOW}Criando usuário: $username...${RESET}"
        docker-compose run -T airflow-cli users create --username "$username" --firstname "$firstname" --lastname "$lastname" --role "$role" --email "$email" --use-random-password 
        echo -e "${GREEN}Usuário criado: $username${RESET}"
    else
        echo -e "${BLUE}Usuário já existe: $username${RESET}"
    fi
done
# Etapa 4: Verificar e definir as variáveis de ambiente no Airflow
update_progress "Verificando e definindo variáveis de ambiente no Airflow..."

declare -A vars
vars["EMAIL_SOAR_MONITORING"]="email_monitoring@example.com"
vars["EMAIL_SETUP_MANAGER"]="email_manager@example.com"

existing_vars=$(docker-compose run -T airflow-cli variables list 2> /dev/null | awk '{print $1}' | sort)

for var in "${!vars[@]}"
do
    if ! [[ $existing_vars =~ $var ]]; then
        docker-compose run -T airflow-cli variables set "$var" "${vars[$var]}"
        echo -e "${YELLOW}Variável definida: $var${RESET}"
    else
        echo -e "${GREEN}Variável já existe: $var${RESET}"
    fi
done

# Finalização
echo -e "${GREEN}Configuração do Airflow concluída.${RESET}"
