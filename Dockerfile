# (1)
FROM python:3.9

# (2)
WORKDIR /code

# (3)
COPY ./requirements.txt /code/requirements.txt

# (4)
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt # no-cache-dir is a pip option to always pull requirements, there is already a caching system with docker

# (5)
COPY ./app /code/app

# (6)
CMD ["uvicorn", "app.main:blockchain", "--host", "0.0.0.0", "--port", "80"]