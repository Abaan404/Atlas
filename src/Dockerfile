FROM python

WORKDIR /usr/src/app
COPY . .

RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt
RUN if [[ ! -d logs ]]; then mkdir logs; fi; 

ENTRYPOINT ["python3", "main.py"]
