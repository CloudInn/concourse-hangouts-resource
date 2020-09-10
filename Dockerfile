FROM python:3.8-alpine as base

# Lint source code
FROM base as lint
RUN apk add --no-cache --virtual .deps gcc musl-dev \
	&& pip install --upgrade pip --no-cache-dir \
	&& pip install black --no-cache-dir
COPY ./ /
RUN black --check --diff /assets && touch /lint-success

# Install dependencies
FROM base as dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Run tests
FROM dependencies as test
COPY ./ /
RUN /testing/test.sh && touch /test-success

# Copy assets
FROM dependencies as production
COPY --from=test /test-success /
COPY --from=lint /lint-success /
COPY ./assets/ /opt/resource/
