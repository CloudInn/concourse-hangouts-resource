FROM python:3.9.5-alpine3.13 as base

# Install dependencies
FROM base as dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Run tests
FROM dependencies as test
RUN pip install --no-cache-dir pytest
COPY ./ /testdir/
WORKDIR /testdir
RUN pytest -vv && touch /test-success

# Copy assets
FROM dependencies as production
COPY --from=test /test-success /
COPY ./assets/ /opt/resource/
