#!/usr/bin/env python3

from __future__ import print_function
import json
import os
import sys
import requests
import traceback


# Construct the webhook request and send it.
def send(url, msg):
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    body = {"text": msg}
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    return (response.status_code, response.text)


# Parse source/params, call the requested command and return the output.
def run_resource(command_name, json_data, command_arguments):
    data = json.loads(json_data)
    source = data.get("source", dict())
    params = data.get("params", dict())
    if command_arguments:
        workspace = command_arguments[0]
    else:
        workspace = ""

    action = {"in": in_res, "out": out_res, "check": check_res}.get(command_name)

    output = action(source, params, workspace)
    print(json.dumps(output))


# Return empty version to keep Concourse happy.
def check_res(source, params, workspace):
    return []


# Return empty version to keep Concourse happy.
def in_res(source, params, workspace):
    return {"version": {}}


# Extract required params for out, construct message and send it.
def out_res(source, params, workspace):
    url = source.get("webhook_url")
    if url is None:
        raise Exception("Webhook URL missing from configuration")
    message = params.get("message")
    message_file = params.get("message_file")
    build_uuid = os.getenv("BUILD_ID")
    build_id = os.getenv("BUILD_NAME")
    job_name = os.getenv("BUILD_JOB_NAME")
    pipeline_name = os.getenv("BUILD_PIPELINE_NAME")
    team_name = os.getenv("BUILD_TEAM_NAME")
    atc_url = os.getenv("ATC_EXTERNAL_URL")
    url_enabled_source = (
        source["post_url"] if type(source.get("post_url")) is bool else True
    )
    url_enabled_param = (
        params["post_url"] if type(params.get("post_url")) is bool else None
    )

    url_enabled = (
        url_enabled_param if type(url_enabled_param) is bool else url_enabled_source
    )
    build_url = f"{atc_url}/teams/{team_name}/pipelines/{pipeline_name}/jobs/{job_name}/builds/{build_id}"

    message_file_path = f"{workspace}/{message_file}"
    message_from_file = ""
    if os.path.isfile(message_file_path):
        with open(message_file_path, "r") as f:
            message_from_file = f.read()

    full_message = (message or "") + message_from_file.rstrip("\n")
    message_text = f"""
Pipeline: {pipeline_name}
Job: {job_name}
Build: #{build_id}
{full_message}
{build_url if url_enabled else ''}
"""
    status, text = send(url, message_text)
    api_res = json.loads(text)

    print("Successfully posted to GoogleChat!")
    print(f"Sent Message:\n{message_text}")
    print(f"Confirmed Message:\n{api_res.get('text')}")

    return {
        "version": {},
        "metadata": [
            {"name": "status", "value": "Posted"},
            {
                "name": "sender_name",
                "value": api_res.get("sender") and api_res["sender"].get("name"),
            },
            {
                "name": "sender_display_name",
                "value": api_res.get("sender") and api_res["sender"].get("displayName"),
            },
            {
                "name": "space_name",
                "value": api_res.get("space") and api_res["space"].get("name"),
            },
            {
                "name": "space_type",
                "value": api_res.get("space") and api_res["space"].get("type"),
            },
            {
                "name": "space_display_name",
                "value": api_res.get("space") and api_res["space"].get("displayName"),
            },
            {
                "name": "thread_name",
                "value": api_res.get("thread") and api_res["thread"].get("name"),
            },
            {"name": "create_time", "value": api_res.get("createTime")},
        ],
    }


if __name__ == "__main__":
    try:
        run_resource(os.path.basename(__file__), sys.stdin.read(), sys.argv[1:])
    except Exception as err:
        print("Something went wrong, not posting to Google Chat", file=sys.stderr)
        print(f"Error: {err}", file=sys.stderr)
        print(f"Stacktrace:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(
            json.dumps(
                {"version": {}, "metadata": [{"name": "status", "value": "Failed"}]}
            )
        )
        sys.exit(1)
