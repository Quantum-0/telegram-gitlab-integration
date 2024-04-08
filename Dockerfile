FROM python:3.11.2-slim-bullseye

WORKDIR /

ENV PYTHONUNBUFFERED=1

ADD pyproject.toml .
ADD tggl /tggl

# RUN pip install --upgrade pip wheel \
#  && pip install -e '.'

RUN pip install --upgrade pip wheel
RUN pip install -e '.'

CMD ["start-bot"]
