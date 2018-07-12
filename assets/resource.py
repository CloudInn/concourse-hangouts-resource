#!/usr/bin/env python3

from __future__ import print_function
import json
import os
import sys
import requests
import traceback


class GoogleChatNotifyResource:
    """Notify resource implementation."""

    def send(self, url, msg):
        """Construct the webhook request and send it."""
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        body = {'text': msg}

        response = requests.request("POST", url, json=body, headers=headers)

        if response.status_code != 200:
            print("Response from webhook: %s" % response.content, file=sys.stderr)
            raise Exception('Unexpected response {}'.format(response.status_code))

        return (response.status_code, response.text)

    def run(self, command_name, json_data, command_arguments):
        """Parse source/params, call the requested command and return the output."""
        data = json.loads(json_data)
        source = data.get('source', dict())
        params = data.get('params', dict())
        workspace = command_arguments[0]

        resource = {
            "in": self.in_res,
            "out": self.out_res,
            "check": self.check_res
        }.get(command_name)

        output = resource(source, params, workspace)
        print(json.dumps(output))

    def check_res(self, source, params, workspace):
        """Return empty version to keep Concourse happy."""
        return {"version": {}}

    def in_res(self, source, params, workspace):
        """Return empty version to keep Concourse happy."""
        return {"version": {}}

    def out_res(self, source, params, workspace):
        """Extract required params for out, construct message and send it."""
        url = source.get('webhook_url')
        message = params.get('message')
        message_file = params.get('message_file')
        build_uuid = os.getenv('BUILD_ID')
        build_id = os.getenv('BUILD_NAME')
        job_name = os.getenv('BUILD_JOB_NAME')
        pipeline_name = os.getenv('BUILD_PIPELINE_NAME')
        team_name = os.getenv('BUILD_TEAM_NAME')
        atc_url = os.getenv('ATC_EXTERNAL_URL')
        url_enabled_source = source['post_url'] if type(source.get('post_url')) is bool else True
        url_enabled_param = params['post_url'] if type(params.get('post_url')) is bool else None

        url_enabled = url_enabled_param if type(url_enabled_param) is bool else url_enabled_source
        build_url = "%s/teams/%s/pipelines/%s/jobs/%s/builds/%s" % (atc_url, team_name, pipeline_name, job_name, build_id)

        message_file_path = "%s/%s" % (workspace, message_file)
        message_from_file = ""
        if os.path.isfile(message_file_path):
            with open(message_file_path, 'r') as f:
                message_from_file = f.read()

        full_message = (message or '') + message_from_file.rstrip("\n")
        text = """\
Pipeline: {0}
Job: #{1} {2}
{3}\
""".format(pipeline_name, build_id, job_name, full_message) + ("\n" + build_url if url_enabled else "")

        response = {
            "version": {},
            "metadata": []
        }

        if not url:
            print("Missing 'webhock_url' under resource source.\nSkip posting to GoogleChat.", file=sys.stderr)
            response["metadata"] += [
                {"name": "status", "value": "Failed"},
                {"name": "error", "value": "Missing 'webhock_url' in source"}
            ]
            return json.dumps(response)

        status, text = self.send(url, text)
        api_res = json.loads(text)

        print("Successfully posted to GoogleChat!", file=sys.stderr)
        print("Message:-\n%s" % api_res.get('text'), file=sys.stderr)

        response["metadata"] = [
            {"name": "status", "value": "Posted"},
            {"name": "sender_name", "value": api_res.get('sender') and api_res['sender'].get('name')},
            {"name": "sender_display_name", "value": api_res.get('sender') and api_res['sender'].get('displayName')},
            {"name": "space_name", "value": api_res.get('space') and api_res['space'].get('name')},
            {"name": "space_type", "value":  api_res.get('space') and api_res['space'].get('type')},
            {"name": "space_display_name", "value": api_res.get('space') and api_res['space'].get('displayName')},
            {"name": "thread_name", "value": api_res.get('thread') and api_res['thread'].get('name')},
            {"name": "create_time", "value": api_res.get('createTime')},
        ]

        return response


if __name__ == '__main__':
    try:
        GoogleChatNotifyResource().run(os.path.basename(__file__), sys.stdin.read(), sys.argv[1:])
    except Exception as err:
        print(
            """\
Something wrong happened, skip posting to GoogleChat:

Error: %s
Stacktrace:
""" % err, file=sys.stderr
        )
        traceback.print_exc(file=sys.stderr)

        print(json.dumps({
            "version": {},
            "metadata": [
                {"name": "status", "value": "Failed"},
            ]
        }))
