FROM python:3.9-alpine as base

# Install dependencies
FROM base as dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Run tests
FROM dependencies as test
RUN pip install pytest
COPY ./ /testdir/
WORKDIR /testdir
RUN pytest -vv && touch /test-success

# Copy assets
FROM dependencies as production
COPY --from=test /test-success /
COPY ./assets/ /opt/resource/
