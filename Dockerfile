# syntax=docker/dockerfile:1

# Imagem base
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Cria diretório para as imagens dos produtos
RUN mkdir -p app/static/img/produtos

# Expõe a porta que a aplicação usa
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["python", "route.py"]
