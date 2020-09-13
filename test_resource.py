#!/usr/bin/env python3
import pytest
import random
import json
import os
from assets import resource


def test_send():
    test_message = str(random.getrandbits(128))
    code, message = resource.send("https://httpbin.org/post", test_message)
    assert code == 200
    assert test_message in message


def test_run_resource_check(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("check", data, "") == ([], True)


def test_run_resource_in(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("in", data, "") == ({"version": {}}, True)


def test_run_resource_out_basic(basic_input, basic_output):
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_no_message(basic_input, basic_output):
    del basic_input["params"]["message"]
    basic_output["metadata"][1]["value"] = None
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_message_file(basic_input, basic_output, request):
    basic_input["params"]["message_file"] = "message.txt"
    data = json.dumps(basic_input)
    current_dir = request.fspath.dirname
    assert resource.run_resource("out", data, [current_dir]) == (basic_output, True)


def test_run_resource_out_add_url(basic_input, basic_output):
    basic_input["params"]["post_url"] = True
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_no_url(basic_input, basic_output):
    basic_input["params"]["post_url"] = False
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
            {"name": "status", "value": "Posted"},
            {"name": "message", "value": "Test Message"},
            {"name": "sender_name", "value": None},
            {"name": "sender_display_name", "value": None},
            {"name": "space_name", "value": None},
            {"name": "space_type", "value": None},
            {"name": "space_display_name", "value": None},
            {"name": "thread_name", "value": None},
            {"name": "create_time", "value": None},
        ],
    }


@pytest.fixture
def failure_output():
    return {"version": {}, "metadata": [{"name": "status", "value": "Failed"}]}
