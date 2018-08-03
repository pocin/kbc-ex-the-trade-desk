FROM python:3.6-alpine
RUN apk add --no-cache git && pip3 install --no-cache-dir --upgrade \
      pytest \
      flake8 \
      requests \
      voluptuous \
      https://github.com/keboola/python-docker-application/tarball/master \
      git+https://github.com/pocin/thetradingdesk-python-client@0.1.4 \
      git+https://github.com/pocin/jsontangle@0.2.1 && apk del git

WORKDIR /code

COPY . /code/

# Run the application
CMD python3 -u /code/main.py

