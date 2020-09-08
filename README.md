Concourse Google Hangouts Resource
======================

A [Concourse](http://concourse.ci/) resource to post to notification to Google Hangouts room using webhooks, the notification includes the pipeline name, The job name and build number which the resource is running under, and an optional message.

Listed in Concourse [community resources](https://concourse-ci.org/community-resources.html)

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

* `webhook_url`: _Required - (String)_. The webhook generated for Hangouts channel. (i.e. "https://chat.googleapis.com/v1/spaces/ABC/messages?key=DEF)
* `post_url`: _Optional - (Boolean)_. Include link to the current job, this is pipeline wide setting in all jobs using resource, can be overridden in `params` in each step. (*Default:* `true`)

### Example

```yaml
resources:
- name: hangouts
  type: hangouts-resource
  source:
    webhook_url: {{pipeline_alerts_webhook}}
    post_url: true
```

## Behaviour

### `check`: Non-functional

### `in`: Non-functional

### `out`: Post message to Hangouts chat room

Posts the given message to Google Hangouts channel that is corresponding to the webhook. It additionally includes information from the current running build as `$BUILD_PIPELINE_NAME` which is the **pipeline name**, `$BUILD_NAME` which reflects the **build id** shown in Concourse Web UI, and `$BUILD_JOB_NAME` which is the **job name** as defined in the pipeline, both build id and job name belongs to the current build for the job the resource is used under.

#### Parameters

* `message`: _Optional - (String)_. The message to post along the other information to Hangouts room.
* `message_file` _Optional - (String)_. Path to file containing text to append to `message`)
* `post_url` _Optional - (Boolean)_. Include link to the current job, if set this will override `post_url` in `source` for the current step. (*Default:* Fall back to `post_url` in `source`)

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
            post_url: true

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
          post_url: false
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
      post_url: true

resources:
- name: hangouts
  type: hangouts-resource
  source:
    webhook_url: ((hangouts_webhook))
    post_url: true

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
