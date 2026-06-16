# Dockerfile
FROM python:3.12

WORKDIR /app

# Install dependencies into Lambda task root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Patches ragas to use the correct modern package import
RUN sed -i 's/from langchain_community.chat_models.vertexai import ChatVertexAI/from langchain_google_vertexai import ChatVertexAI/g' /usr/local/lib/python3.12/site-packages/ragas/llms/base.py
# Copy entire project
COPY . .

# Cloud Run requires port 8080
EXPOSE 8080

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]