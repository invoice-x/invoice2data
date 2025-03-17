FROM python:slim

RUN apt update\
    && apt install -y tesseract-ocr poppler-utils imagemagick ghostscript\
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

RUN  pip install --no-cache-dir -U invoice2data ocrmypdf pip

RUN groupadd -r invoice2data && useradd -m -r -g invoice2data invoice2data

USER invoice2data
WORKDIR /home/invoice2data

ENTRYPOINT [ "invoice2data" ]
