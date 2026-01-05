# Step 1: Builder
FROM python:3.14-slim AS builder
WORKDIR /usr/local/app

COPY ./ ./

RUN apt-get update && apt-get install -y git build-essential libffi-dev libssl-dev python3-dev \
    && python -m venv /usr/local/venv \
    && /usr/local/venv/bin/pip install --upgrade pip wheel setuptools

# Install dependencies
RUN /usr/local/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /usr/local/venv/bin/pip install --no-cache-dir cryptography

# Step 2: Final image
FROM python:3.14-slim
WORKDIR /usr/local/app

ENV PATH="/usr/local/venv/bin:$PATH"
ENV USR=app
ENV GRP=$USR
ENV UID=1000
ENV GID=1000

RUN apt-get update && apt-get install -y netcat \
    && addgroup --gid "$GID" $GRP \
    && adduser --disabled-password --home "$(pwd)" --uid "$UID" --ingroup "$GRP" $USR

COPY --from=builder /usr/local/venv /usr/local/venv
COPY --from=builder /usr/local/app /usr/local/app

RUN chown -R $USR:$GRP .

COPY docker-entrypoint.sh /
RUN sed -i 's/\r$//' /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER $USR

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "main.py"]
