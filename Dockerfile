FROM python:2.7-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.cfg
EXPOSE 8003
CMD python __init__.py
