# Imagem base oficial com Python. O projeto usa apenas a biblioteca padrao
# para sockets TCP/UDP, entao nao e necessario instalar frameworks de mensagens.
FROM python:3.11-slim

# Diretorio da aplicacao dentro do conteiner.
WORKDIR /app

# Configuracoes de ambiente:
# - PYTHONUNBUFFERED mostra logs imediatamente no terminal/Docker.
# - PYTHONDONTWRITEBYTECODE evita gravar __pycache__ em tempo de execucao.
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copia codigo-fonte, README, testes e arquivo de dependencias.
COPY . /app

# Instala bibliotecas declaradas. No momento o requirements.txt esta vazio,
# porque o sistema usa socket, threading, time e random da biblioteca padrao.
RUN pip install --no-cache-dir -r requirements.txt

# Etapa de "compilacao"/validacao para Python: verifica a sintaxe dos modulos e
# gera bytecode durante o build da imagem.
RUN python -m compileall broker sensors actuators client shared tests

# Comando padrao da imagem. O docker-compose sobrescreve esse comando para
# iniciar sensores, atuadores e cliente quando necessario.
CMD ["python", "-m", "broker.broker"]
