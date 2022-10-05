FROM python:3.10

ENV DEBIAN_FRONTEND=noninteractive
ENV LANGUAGE=en


# set working directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY gunicorn.conf.py /gunicorn.conf.py

# install environment dependencies
RUN apt-get update -yqq \
  && apt-get install -yqq --no-install-recommends \
  build-essential autoconf libssl-dev libffi-dev \
  openssl libgl1-mesa-dev libglib2.0-0 libsm6 libxrender1 libxext6 \
  libavdevice-dev libavfilter-dev libopus-dev libvpx-dev libopencv-dev \
  && apt-get -q clean

# add requirements (to leverage Docker cache)
COPY Pipfile ./
COPY Pipfile.lock ./

# install requirements
RUN pip install -U --no-cache-dir pipenv
RUN pipenv install

COPY ./app /usr/src/app/app

CMD pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8080 reload