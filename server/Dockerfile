# (1)
FROM python:3.9

# (2)
WORKDIR /server

# (3)
COPY ./* /server/

# (4)
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt # no-cache-dir is a pip option to always pull requirements, there is already a caching system with docker

# (5)
CMD ["uvicorn", "main:blockchain", "--host", "0.0.0.0", "--port", "80"]