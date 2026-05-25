import asyncio
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ── Issue #6: params= not payload= ──────────────────────────────────

def test_request_uses_params_kwarg_not_payload():
    """Request.run() must pass params= to aiohttp, not payload=."""
    from loadlamb.chalicelib.request import Request

    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.text = AsyncMock(return_value='ok')
    mock_session.request = AsyncMock(return_value=mock_resp)

    proj_config = {
        'project_slug': 'test',
        'run_slug': 'run-1',
        'active_stage': 'dev',
        'stages': [{'name': 'dev', 'url': 'http://localhost'}],
        'timeout': 30,
    }
    req_config = {
        'path': '/search',
        'method_type': 'GET',
        'params': [{'q': 'hello'}],
    }

    req = Request(mock_session, req_config, proj_config, 0, 0)

    async def run():
        with patch('loadlamb.chalicelib.request.Response') as MockResponse:
            mock_ltr = MagicMock()
            MockResponse.return_value.get_ltr = AsyncMock(return_value=mock_ltr)
            MockResponse.return_value.assert_contains = AsyncMock()
            return await req.run()

    asyncio.get_event_loop().run_until_complete(run())

    _, kwargs = mock_session.request.call_args
    assert 'payload' not in kwargs, (
        "aiohttp was called with 'payload=' — must use 'params=' instead")
    assert 'params' in kwargs, (
        "aiohttp was not called with 'params=' for query parameters")


# ── Issue #8: class name typo ────────────────────────────────────────

def test_cognito_request_class_has_correct_name():
    """The Cognito request class must be importable as CognitoRequest."""
    from loadlamb.chalicelib.contrib.requests.cognito import CognitoRequest
    assert CognitoRequest is not None


def test_cognito_request_old_name_gone():
    """The misspelled CogntioRequest name must no longer exist."""
    import loadlamb.chalicelib.contrib.requests.cognito as mod
    assert not hasattr(mod, 'CogntioRequest'), (
        'CogntioRequest (misspelled) still exists — rename to CognitoRequest')


def test_cognito_request_is_request_subclass():
    """CognitoRequest must still be a subclass of Request."""
    from loadlamb.chalicelib.contrib.requests.cognito import CognitoRequest
    from loadlamb.chalicelib.request import Request
    assert issubclass(CognitoRequest, Request)


def test_cognito_uses_params_kwarg_not_payload():
    """CognitoRequest.run() must pass params= to aiohttp, not payload=."""
    import ast
    with open('loadlamb/chalicelib/contrib/requests/cognito.py') as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == 'payload':
            pytest.fail(
                "cognito.py still uses 'payload=' keyword argument — must be 'params='")
