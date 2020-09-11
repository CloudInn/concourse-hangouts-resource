#!/usr/bin/env python3
import pytest
import random
import json
from assets import resource


def test_send():
    test_message = str(random.getrandbits(128))
    code, message = resource.send("https://httpbin.org/post", test_message)
    assert code == 200
    assert test_message in message


def test_run_resource_check(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("check", data, "") == []


def test_run_resource_in(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("in", data, "") == {"version": {}}


def test_run_resource_out(basic_input, blank_output):
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == blank_output


@pytest.fixture
def basic_input():
    return {
        "source": {"webhook_url": "https://httpbin.org/post"},
        "params": {
            "message": "Test Message",
            "message_file": "testing/message.txt",
            "post_url": True,
        },
    }


@pytest.fixture
def blank_output():
    return {
        "version": {},
        "metadata": [
            {"name": "status", "value": "Posted"},
            {"name": "sender_name", "value": None},
            {"name": "sender_display_name", "value": None},
            {"name": "space_name", "value": None},
            {"name": "space_type", "value": None},
            {"name": "space_display_name", "value": None},
            {"name": "thread_name", "value": None},
            {"name": "create_time", "value": None},
        ],
    }
