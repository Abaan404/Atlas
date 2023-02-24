FROM python

WORKDIR /usr/src/app
COPY . .

RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "main.py"]
