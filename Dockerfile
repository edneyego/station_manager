FROM python:3.13-slim

WORKDIR /app

# Criar usuário não-root
RUN useradd -m appuser

# Copiar primeiro o requirements para aproveitar cache do Docker
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar restante do código
COPY . .

# Ajustar permissões para o usuário
RUN chown -R appuser:appuser /app

# Rodar como usuário não-root
USER appuser

# Variável de ambiente para facilitar imports
ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 8000

CMD ["python", "main.py"]
