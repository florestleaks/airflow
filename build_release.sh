#!/bin/bash

# Cores para a saída
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

# Nome da imagem Docker
IMAGE_NAME="registry.florestleaks.com/florestleaks/soar/infra/airflow/florestleaks_airflow"

# Diretório do Dockerfile

# Função para registrar mensagens
log() {
    echo -e "${GREEN}[+]${RESET} $1"
}

# Função para registrar erros
error() {
    echo -e "${RED}[-] ERROR:${RESET} $1"
}

# Função para o Git commit e push
git_commit_push() {
    find .  -type d -name '__pycache__' -exec rm -rf {} +
    git add . -v || { error "Erro ao adicionar alterações ao Git. Abortando."; exit 1; }
    log "Adicionando alterações ao Git"
    
    git commit -m "Atualização do Airflow" || { error "Erro ao realizar commit. Abortando."; exit 1; }
    log "Realizando commit no Git"
    
    git push || { error "Erro ao enviar alterações para o repositório remoto. Abortando."; exit 1; }
    log "Enviando alterações para o repositório remoto"
}

# Função para construir e enviar a imagem Docker
docker_build_push() {
    docker build -t  $IMAGE_NAME:latest . || { error "Erro ao construir a imagem Docker. Abortando."; exit 1; }
    log "Construindo a imagem Docker"
    
    docker push $IMAGE_NAME:latest || { error "Erro ao enviar a imagem Docker. Abortando."; exit 1; }
    log "Enviando a imagem para o registro Docker"
}

# Menu de seleção
echo "Selecione uma opção:"
echo "1. Git Commit e Push"
echo "2. Docker Build e Push"
read -p "Escolha uma opção: " OPTION

case $OPTION in
    1) git_commit_push;;
    2) docker_build_push;;
    *) echo "Opção inválida"; exit 1;;
esac

# Finaliza o script
log "Script de deploy do Airflow concluído com sucesso"
