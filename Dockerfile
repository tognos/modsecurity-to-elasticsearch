FROM python:2-alpine

RUN apk add --update-cache git  && pip install elasticsearch certifi && mkdir /modsecurity-to-elasticsearch

ADD modsec_parser.py /modsecurity-to-elasticsearch

CMD ["python","/modsecurity-to-elasticsearch/modsec_parser.py","--log-directory","/logs"]
