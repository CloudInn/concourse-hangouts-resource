#!/usr/bin/env python3
import json
import os
import sys
import requests


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

    return action(source, params, workspace)


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
    url_enabled = (
        params.get("post_url") if isinstance(params.get("post_url"), bool) else True
    )
    build_id = os.getenv("BUILD_NAME")
    job_name = os.getenv("BUILD_JOB_NAME")
    pipeline_name = os.getenv("BUILD_PIPELINE_NAME")
    team_name = os.getenv("BUILD_TEAM_NAME")
    atc_url = os.getenv("ATC_EXTERNAL_URL")

    build_url = (
        f"\n{atc_url}/teams/{team_name}/pipelines/{pipeline_name}/jobs/{job_name}/builds/{build_id}"
        if url_enabled
        else ""
    )

    message_file_path = f"{workspace}/{message_file}"
    message_from_file = ""
    if os.path.isfile(message_file_path):
        with open(message_file_path, "r") as f:
            message_from_file = f.read().rstrip("\n")
    else:
        print(f"Message file {message_file} not found. Skipping", file=sys.stderr)

    message_text = f"""
Pipeline: {pipeline_name}
Job: {job_name}
Build: #{build_id}{build_url}
{message or ""}
{message_from_file}
"""
    status, text = send(url, message_text)
    api_res = json.loads(text)

    print("Message sent to Google Chat!")
    print(f"Message Content:\n{message_text}")
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
        result = run_resource(
            os.path.basename(__file__), sys.stdin.read(), sys.argv[1:]
        )
        print(json.dumps(result))
    except Exception as err:
        print("Something went wrong, not posting to Google Chat", file=sys.stderr)
        print(f"Error: {err}", file=sys.stderr)
        print(
            json.dumps(
                {"version": {}, "metadata": [{"name": "status", "value": "Failed"}]}
            )
        )
        sys.exit(1)
