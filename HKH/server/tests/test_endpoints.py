from http.client import (
    BAD_REQUEST,
    CREATED,
    FORBIDDEN,
    NOT_ACCEPTABLE,
    NOT_FOUND,
    OK,
    SERVICE_UNAVAILABLE,
)

from unittest.mock import patch

import pytest

import server.endpoints as ep
import states.query as sqry

TEST_CLIENT = ep.app.test_client()
TEST_ST = sqry.TEST_STATE


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_get_states(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.STATES_EP)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.STATES_RESP in resp_json
    assert isinstance(resp_json[ep.STATES_RESP], dict)


@patch('states.query.is_db_up', return_value=False, autospec=True)
def test_get_states_db_unavailable(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.STATES_EP)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('states.query.is_db_up', return_value=False, autospec=True)
def test_create_db_down(mock_is_db_up):
    ret = sqry.create(TEST_ST['state_code'],
                      TEST_ST['population'],
                      TEST_ST['capital'],
                      TEST_ST['area_sq_miles'],
                      TEST_ST['name'])
    assert ret is None


@pytest.fixture
def temp_state():
    yield dict(sqry.TEST_STATE)
    with patch('states.query.is_db_up', return_value=True, autospec=True):
        sqry.delete(sqry.TEST_STATE['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state(mock_is_db_up, temp_state):
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state)
    assert resp.status_code == CREATED
    assert sqry.exists(temp_state['state_code'])


@patch('states.query.is_db_up', return_value=True, autospec=True)
def test_create_state_bad_data(mock_is_db_up, temp_state):
    temp_state['population'] = -1
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state)
    assert resp.status_code == BAD_REQUEST


@patch('states.query.is_db_up', return_value=False, autospec=True)
def test_create_state_db_unavailable(mock_is_db_up, temp_state):
    resp = TEST_CLIENT.post(ep.STATES_EP, json=temp_state)
    assert resp.status_code == SERVICE_UNAVAILABLE


def test_get_endpoints():
    resp = TEST_CLIENT.get(ep.ENDPOINT_EP)

    assert resp.status_code == OK

    resp_json = resp.get_json()
    assert ep.ENDPOINT_RESP in resp_json

    endpoints = resp_json[ep.ENDPOINT_RESP]
    assert isinstance(endpoints, list)

    expected_routes = {ep.HELLO_EP, ep.ENDPOINT_EP, ep.STATES_EP}
    assert expected_routes.issubset(set(endpoints))

    assert endpoints == sorted(endpoints)


@patch('server.endpoints.sqry.read', return_value={}, autospec=True)
def test_get_states_empty_result(mock_read):
    resp = TEST_CLIENT.get(ep.STATES_EP)

    assert resp.status_code == OK
    assert resp.get_json() == {ep.STATES_RESP: {}}
    mock_read.assert_called_once_with()
