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

    asyncio.run(run())

    _, kwargs = mock_session.request.call_args
    assert 'payload' not in kwargs, (
        "aiohttp was called with 'payload=' — must use 'params=' instead")
    assert 'params' in kwargs, (
        "aiohttp was not called with 'params=' for query parameters")


# ── Issue #8: class name typo ────────────────────────────────────────

def test_cognito_request_class_has_correct_name():
    """The Cognito request class must be defined as CognitoRequest (via AST)."""
    import ast
    with open('loadlamb/chalicelib/contrib/requests/cognito.py') as f:
        source = f.read()
    tree = ast.parse(source)
    class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    assert 'CognitoRequest' in class_names, (
        f'CognitoRequest not found in cognito.py — classes defined: {class_names}')


def test_cognito_request_old_name_gone():
    """The misspelled CogntioRequest must no longer be defined (via AST)."""
    import ast
    with open('loadlamb/chalicelib/contrib/requests/cognito.py') as f:
        source = f.read()
    tree = ast.parse(source)
    class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    assert 'CogntioRequest' not in class_names, (
        'CogntioRequest (misspelled) still defined in cognito.py — rename to CognitoRequest')


def test_cognito_request_is_request_subclass():
    """CognitoRequest must subclass Request (via AST)."""
    import ast
    with open('loadlamb/chalicelib/contrib/requests/cognito.py') as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'CognitoRequest':
            base_names = [
                b.id if isinstance(b, ast.Name) else
                b.attr if isinstance(b, ast.Attribute) else ''
                for b in node.bases
            ]
            assert 'Request' in base_names, (
                f'CognitoRequest does not subclass Request — bases: {base_names}')
            return
    pytest.fail('CognitoRequest class not found in cognito.py')


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
