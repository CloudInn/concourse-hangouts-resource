#!/usr/bin/env python3
import json
import os
import sys
import requests
import pathlib
import urllib


# Construct the webhook request and send it.
def send(url, msg, create_thread):
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    body = {"text": msg}
    if not create_thread:
        params = {"threadKey": "concoursethreadkey"}
        url_parts = list(urllib.parse.urlparse(url))
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urllib.parse.urlencode(query)
        url = urllib.parse.urlunparse(url_parts)
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    return (response.status_code, response.text)


# Return data if it's a boolean, otherwise return the default
def get_bool(data, default):
    if not isinstance(default, bool):
        raise Exception("Default for get_bool was not set to a bool")
    return (data if isinstance(data, bool) else default)


# Return content of message file as a string
def read_message_file(message_file, workspace):
    if message_file:
        message_file_path = f"{workspace}/{message_file}"
        if os.path.isfile(message_file_path):
            with open(message_file_path, "r") as f:
                return f.read().rstrip("\n")
        else:
            print(f"Message file {message_file} not found. Skipping", file=sys.stderr)
    return ""


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
        print(json.dumps(result, indent=2))
        return result, True
    except Exception as err:
        result = {"version": {}, "metadata": [{"name": "status", "value": "Failed"}]}
        print("Something went wrong, not posting to Google Chat", file=sys.stderr)
        print(f"Error: {err}", file=sys.stderr)
        print(json.dumps(result, indent=2))
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
    message_file = params.get("message_file")
    create_thread = get_bool(params.get("create_thread"), False)
    pipeline_name = os.getenv("BUILD_PIPELINE_NAME")
    job_name = os.getenv("BUILD_JOB_NAME")
    build_id = os.getenv("BUILD_NAME")

    job_info = ""
    if info_enabled := get_bool(params.get("post_info"), True):
        job_info = f"Pipeline: {pipeline_name}\nJob: {job_name}\nBuild: #{build_id}\n"

    message_out = ""
    if message := params.get("message"):
        message_out = f"{message}\n"

    build_url = ""
    message_url = ""
    if get_bool(params.get("post_url"), True):
        team_name = os.getenv("BUILD_TEAM_NAME")
        atc_url = os.getenv("ATC_EXTERNAL_URL")
        build_url = f"{atc_url}/teams/{team_name}/pipelines/{pipeline_name}/jobs/{job_name}/builds/{build_id}"
        message_url = f"{build_url}\n"

    message_from_file = read_message_file(message_file, workspace)

    message_text = f"{job_info}{message_url}{message_out}{message_from_file}"
    status, text = send(url, message_text, create_thread)
    api_res = json.loads(text)
    sender_name = api_res.get("sender") and api_res["sender"].get("name")
    sender_disp_name = api_res.get("sender") and api_res["sender"].get("displayName")
    space_name = api_res.get("space") and api_res["space"].get("name")
    space_disp_name = api_res.get("space") and api_res["space"].get("displayName")
    space_type = api_res.get("space") and api_res["space"].get("type")
    thread_name = api_res.get("thread") and api_res["thread"].get("name")
    create_time = api_res.get("createTime")

    print("Message sent to Google Chat!", file=sys.stderr)

    return {
        "version": {},
        "metadata": [
            {"name": "Status", "value": "Posted"},
            {"name": "Message", "value": str(message)},
            {"name": "Message File Name", "value": str(message_file)},
            {"name": "Build URL", "value": str(build_url)},
            {"name": "Thread Created", "value": str(create_thread)},
            {"name": "Pipeline Name", "value": str(pipeline_name)},
            {"name": "Job Name", "value": str(job_name)},
            {"name": "Build Number", "value": str(build_id)},
            {"name": "Info Sent", "value": str(info_enabled)},
            {"name": "Sender Name", "value": sender_name},
            {"name": "Sender Display Name", "value": sender_disp_name},
            {"name": "Space Name", "value": space_name},
            {"name": "Space Display Name", "value": space_disp_name},
            {"name": "Space Type", "value": space_type},
            {"name": "Thread Name", "value": thread_name},
            {"name": "Time Created", "value": create_time},
        ],
    }


if __name__ == "__main__":
    filename = os.path.basename(__file__)
    result, success = run_resource(filename, sys.stdin.read(), sys.argv[1:])
    if not success:
        sys.exit(1)
