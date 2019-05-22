FROM python:2-alpine

RUN pip install elasticsearch certifi && mkdir /modsecurity-to-elasticsearch

ADD modsec_parser.py /modsecurity-to-elasticsearch

CMD ["python","/modsecurity-to-elasticsearch/modsec_parser.py","--log-directory","/logs"]
