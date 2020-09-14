#!/usr/bin/env python3
import json
import os
import sys
import requests
import pathlib


# Construct the webhook request and send it.
def send(url, msg):
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    body = {"text": msg}
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    return (response.status_code, response.text)


# Parse source/params, call the requested command and return the output.
def run_resource(command_name, json_data, command_arguments):
    try:
        data = json.loads(json_data)
        source = data.get("source", dict())
        params = data.get("params", dict())
        if command_arguments:
            workspace = pathlib.Path(command_arguments[0]).resolve()
        else:
            workspace = None

        action = {"in": in_res, "out": out_res, "check": check_res}.get(command_name)

        result = action(source, params, workspace)
        print(json.dumps(result))
        return result, True
    except Exception as err:
        result = {"version": {}, "metadata": [{"name": "status", "value": "Failed"}]}
        print("Something went wrong, not posting to Google Chat", file=sys.stderr)
        print(f"Error: {err}", file=sys.stderr)
        print(json.dumps(result))
        return result, False


# Return empty version to keep Concourse happy.
def check_res(source, params, workspace):
    return []


# Return empty version to keep Concourse happy.
def in_res(source, params, workspace):
    return {"version": {}}


# Extract required params for out, construct message and send it.
def out_res(source, params, workspace):
    url = source.get("webhook_url")
    if not url:
        raise Exception("Webhook URL missing from configuration")
    message = params.get("message")
    message_file = params.get("message_file")
    url_enabled = (
        params.get("post_url") if isinstance(params.get("post_url"), bool) else True
    )
    pipeline_name = os.getenv("BUILD_PIPELINE_NAME")
    job_name = os.getenv("BUILD_JOB_NAME")
    build_id = os.getenv("BUILD_NAME")

    build_url = ""
    if url_enabled:
        team_name = os.getenv("BUILD_TEAM_NAME")
        atc_url = os.getenv("ATC_EXTERNAL_URL")
        build_url = f"{atc_url}/teams/{team_name}/pipelines/{pipeline_name}/jobs/{job_name}/builds/{build_id}"

    message_from_file = ""
    if message_file:
        message_file_path = f"{workspace}/{message_file}"
        if os.path.isfile(message_file_path):
            with open(message_file_path, "r") as f:
                message_from_file = f.read().rstrip("\n")
        else:
            print(f"Message file {message_file} not found. Skipping", file=sys.stderr)

    message_text = f"""Pipeline: {pipeline_name}
Job: {job_name}
Build: #{build_id}
{build_url}
{message or ""}
{message_from_file}"""
    status, text = send(url, message_text)
    api_res = json.loads(text)

    print("Message sent to Google Chat!", file=sys.stderr)

    return {
        "version": {},
        "metadata": [
            {"name": "Status", "value": "Posted"},
            {"name": "Message", "value": str(message)},
            {"name": "Message File Name", "value": str(message_file)},
            {"name": "URL Sent", "value": str(url_enabled)},
            {"name": "Build URL", "value": str(build_url)},
            {"name": "Pipeline Name", "value": str(pipeline_name)},
            {"name": "Job Name", "value": str(job_name)},
            {"name": "Build Number", "value": str(build_id)},
            {
                "name": "Sender Name",
                "value": api_res.get("sender") and api_res["sender"].get("name"),
            },
            {
                "name": "Sender Display Name",
                "value": api_res.get("sender") and api_res["sender"].get("displayName"),
            },
            {
                "name": "Space Name",
                "value": api_res.get("space") and api_res["space"].get("name"),
            },
            {
                "name": "Space Display Name",
                "value": api_res.get("space") and api_res["space"].get("displayName"),
            },
            {
                "name": "Space Type",
                "value": api_res.get("space") and api_res["space"].get("type"),
            },
            {
                "name": "Thread Name",
                "value": api_res.get("thread") and api_res["thread"].get("name"),
            },
            {"name": "Time Created", "value": api_res.get("createTime")},
        ],
    }


if __name__ == "__main__":
    filename = os.path.basename(__file__)
    result, success = run_resource(filename, sys.stdin.read(), sys.argv[1:])
    if not success:
        sys.exit(1)
