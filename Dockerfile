# Imagem que roda o Test Harness do TaskAnalyzer em um ambiente isolado (Fase 3).
FROM python:3.11-slim

# Não grava arquivos .pyc e mostra a saída do pytest na hora.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Usuário sem privilégios de administrador para rodar os testes.
RUN useradd --create-home tester \
    && mkdir /app \
    && chown tester:tester /app
WORKDIR /app

# Instala primeiro as dependências, para aproveitar o cache das camadas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o contrato, o código e os testes.
COPY --chown=tester:tester . .
USER tester

# Comando principal: roda a suíte inteira.
CMD ["pytest", "tests/test_harness.py", "-v"]
