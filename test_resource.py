#!/usr/bin/env python3
import pytest
import random
import json
import os
from assets import resource


def test_send_no_thread():
    test_message = str(random.getrandbits(128))
    code, message = resource.send("https://httpbin.org/post", test_message, False)
    assert code == 200
    assert test_message in message


def test_send_thread():
    test_message = str(random.getrandbits(128))
    code, message = resource.send("https://httpbin.org/post", test_message, True)
    assert code == 200
    assert test_message in message


def test_run_resource_check(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("check", data, "") == ([], True)


def test_run_resource_in(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("in", data, "") == ({"version": {}}, True)


def test_run_resource_out_basic(basic_input, basic_output, env_vars):
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_no_message(basic_input, basic_output, env_vars):
    del basic_input["params"]["message"]
    basic_output["metadata"][1]["value"] = "None"
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_message_file(basic_input, basic_output, request, env_vars):
    basic_input["params"]["message_file"] = "message.txt"
    basic_output["metadata"][2]["value"] = "message.txt"
    data = json.dumps(basic_input)
    current_dir = request.fspath.dirname
    assert resource.run_resource("out", data, [current_dir]) == (basic_output, True)


def test_run_resource_out_missing_message_file(basic_input, basic_output, env_vars):
    basic_input["params"]["message_file"] = "not_a_message.txt"
    basic_output["metadata"][2]["value"] = "not_a_message.txt"
    data = json.dumps(basic_input)
    current_dir = os.getcwd()
    assert resource.run_resource("out", data, [current_dir]) == (basic_output, True)


def test_run_resource_out_add_url(basic_input, basic_output, env_vars):
    basic_input["params"]["post_url"] = True
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_no_url(basic_input, basic_output, env_vars):
    basic_input["params"]["post_url"] = False
    basic_output["metadata"][3]["value"] = "False"
    basic_output["metadata"][4]["value"] = ""
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_webhook_with_params(basic_input, basic_output, env_vars):
    basic_input["source"]["webhook_url"] = "https://httpbin.org/post?test=test"
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_bad_webhook(basic_input, failure_output):
    basic_input["source"]["webhook_url"] = "https://httpbin.org/get"
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (failure_output, False)


def test_run_resource_out_missing_webhook(basic_input, failure_output):
    del basic_input["source"]["webhook_url"]
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (failure_output, False)


@pytest.fixture
def env_vars():
    os.environ["BUILD_PIPELINE_NAME"] = "Test_Pipeline"
    os.environ["BUILD_JOB_NAME"] = "Test_Job"
    os.environ["BUILD_NAME"] = "1234"
    os.environ["BUILD_TEAM_NAME"] = "Test_Team"
    os.environ["ATC_EXTERNAL_URL"] = "https://not.a.site"
    yield True
    del os.environ["BUILD_PIPELINE_NAME"]
    del os.environ["BUILD_JOB_NAME"]
    del os.environ["BUILD_NAME"]
    del os.environ["BUILD_TEAM_NAME"]
    del os.environ["ATC_EXTERNAL_URL"]


@pytest.fixture
def basic_input():
    return {
        "source": {"webhook_url": "https://httpbin.org/post"},
        "params": {"message": "Test Message"},
    }


@pytest.fixture
def basic_output():
    return {
        "version": {},
        "metadata": [
            {"name": "Status", "value": "Posted"},
            {"name": "Message", "value": "Test Message"},
            {"name": "Message File Name", "value": "None"},
            {"name": "URL Sent", "value": "True"},
            {"name": "Build URL", "value": "https://not.a.site/teams/Test_Team/pipelines/Test_Pipeline/jobs/Test_Job/builds/1234"},
            {"name": "Pipeline Name", "value": "Test_Pipeline"},
            {"name": "Job Name", "value": "Test_Job"},
            {"name": "Build Number", "value": "1234"},
            {"name": "Sender Name", "value": None},
            {"name": "Sender Display Name", "value": None},
            {"name": "Space Name", "value": None},
            {"name": "Space Display Name", "value": None},
            {"name": "Space Type", "value": None},
            {"name": "Thread Name", "value": None},
            {"name": "Time Created", "value": None},
        ],
    }


@pytest.fixture
def failure_output():
    return {"version": {}, "metadata": [{"name": "status", "value": "Failed"}]}
