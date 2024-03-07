FROM nvidia/cuda:11.1.1-cudnn8-runtime-ubuntu20.04

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update && apt-get -y install apt-utils

RUN apt-get update && \
    apt-get -y install software-properties-common curl build-essential npm python3 python3-pip pkg-config
RUN add-apt-repository ppa:swi-prolog/stable -y
RUN apt update
RUN apt-get install -y swi-prolog

RUN pip3 install uvicorn[standard] twilio\
    aiohttp scipy aiofiles SQLAlchemy psycopg2-binary fastapi[all] spacy==2.2.1
RUN pip3 install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_lg-0.5.1.tar.gz &\
    pip3 install scispacy ipython networkx
COPY discharge_instructions /app/discharge_instructions
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
RUN . ~/.nvm/nvm.sh && nvm install 17 && nvm use 17 && npm install \
    vue webpack webpack-cli vue-loader openapi-typescript-codegen\
     typescript ts-loader axios form-data vue-style-loader css-loader\
     primevue@latest primeicons primeflex
RUN pip3 install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_lg-0.5.1.tar.gz
COPY Dockerfile /app/
COPY *.pl /app/
RUN apt-get install -y git; git clone https://github.umn.edu/solin020/healthmarshall; cd healthmarshall; find . -maxdepth 1 -exec mv {} .. \; cd ..
CMD sleep infinity 
EXPOSE 8000/tcp
