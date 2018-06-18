Concourse Google Hangouts Resource
======================

A [Concourse](http://concourse.ci/) resource to post to notification to Google Hagouts room using webhooks, the notification includes the pipeline name, The job name and build number which the resource is running under, and an optional message.

## Resource Type Configuration

```yaml
resource_types:
  - name: hangouts-resource
    type: docker-image
    source:
      repository: cloudinn/concourse-hangouts-resource
      tag: latest
```

## Source Configuration

* `webhook_url`: _Required_. The webhook generated for Hagouts channel. (i.e. "https://chat.googleapis.com/v1/spaces/ABC/messages?key=DEF)

### Example

```yaml
resources:
- name: hangouts
  type: hangouts-resource
  source:
    webhook_url: {{pipeline_alerts_webhook}}
```

## Behaviour

### `check`: Nonfunctional

### `in`: Nonfunctional

### `out`: Post message to pipeline

Posts the given message to Google Hangouts channel that is corresponding to the webhook. It additionally includes information from the current running build as `$BUILD_PIPELINE_NAME` which is the **pipeline name**, `$BUILD_NAME` which reflects the **build id** shown in Concourse Web UI, and `$BUILD_JOB_NAME` which is the **job name** as defined in the pipeline, both build id and job name belongs to the current build for the job the resource is used under.

#### Parameters

* `message`: _Optional_. The message to post along the other information to Hangouts room.
* `message_file` _Optional_. File contains some text to post (will he appended to `message` if both are set)

### Example

You're suggested to use it under `try:` step, you don't want your build to fail if the resource failed

```yaml
jobs:
  - name: some-job
    plan:
      - try:
          put: hangouts
          params:
            message: "Successfully released version: "
            message_file: project/version.txt
```

## Suggested Use Case:

```yaml
jobs:
  - name: some-job
    plan:
      - try:
          put: hangouts
          params:
            message: Job Started !

      # .
      # .
      # .
      # Some steps to execute
      # .
      # .
      # .

    on_failure:
      try:
        put: hangouts
        params:
          message: Job Failed !

    on_success:
      try:
        put: hangouts
        params:
          message: Job Succeeded !
```

## Full example:
This is a working example of a pipeline file that does absolutely nothing other then posting to Hangouts.

You can test it as is after passing `hangouts_webhook` while setting up the pipeline or replacing `((hangouts_webhook))` in place with the webhook URL.

```yaml
resource_types:
  - name: hangouts-resource
    type: docker-image
    source:
      repository: cloudinn/concourse-hangouts-resource
      tag: latest

resources:
- name: hangouts
  type: hangouts-resource
  source:
    webhook_url: ((hangouts_webhook))

  # .
  # .
  # .
  # Some other resources
  # .
  # .
  # .


jobs:
  - name: some-job
    serial: true
    plan:
      - try:
          put: hangouts
          params:
            message: Build Started !

      # .
      # .
      # .
      # Some steps to execute
      # .
      # .
      # .

    on_failure:
      try:
        put: hangouts
        params:
          message: Build Failed !

    on_success:
      try:
        put: hangouts
        params:
          message: Build Successed !
```

## License

BSD 2-Clause
