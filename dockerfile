# Dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Install dependencies into Lambda task root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    mangum  # adapts FastAPI to Lambda event format

# Copy entire project
COPY . ${LAMBDA_TASK_ROOT}

# Lambda handler entrypoint
CMD ["api.lambda_handler.handler"]