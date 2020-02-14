FROM python:3.7

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY startapp.sh ./
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY *.py ./

EXPOSE 5000

#CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]
CMD ["sh", "startapp.sh"]
