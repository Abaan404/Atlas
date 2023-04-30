FROM python

WORKDIR /usr/src/app

COPY ./requirements.txt ./requirements.txt 
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY . .
ENTRYPOINT ["python3", "-u", "main.py"]
