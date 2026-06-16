# Dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Install dependencies into Lambda task root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . ${LAMBDA_TASK_ROOT}

# Lambda handler entrypoint
CMD ["api.lambda_handler.handler"]