import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Issue #7: body caching ──────────────────────────────────────────

def test_response_body_read_once():
    """response.text() must be called exactly once even when assert_contains
    and get_ltr are both called."""
    from loadlamb.chalicelib.response import Response

    mock_resp = MagicMock()
    mock_resp.text = AsyncMock(return_value='hello world')
    mock_resp.status = 200

    req_config = {'path': '/test', 'method_type': 'GET', 'contains': 'hello'}
    r = Response(mock_resp, req_config, 'proj', 'run', 0.1, 0, 0)

    async def run():
        await r.assert_contains()
        ltr = await r.get_ltr()
        return ltr

    ltr = asyncio.get_event_loop().run_until_complete(run())
    assert mock_resp.text.call_count == 1, (
        f'response.text() was called {mock_resp.text.call_count} times — must be called exactly once')


def test_response_body_stored_correctly():
    """LoadTestResponse.body must contain the actual response body."""
    from loadlamb.chalicelib.response import Response

    mock_resp = MagicMock()
    mock_resp.text = AsyncMock(return_value='actual body content')
    mock_resp.status = 200

    req_config = {'path': '/test', 'method_type': 'GET', 'contains': 'actual'}
    r = Response(mock_resp, req_config, 'proj', 'run', 0.1, 0, 0)

    async def run():
        await r.assert_contains()
        return await r.get_ltr()

    ltr = asyncio.get_event_loop().run_until_complete(run())
    assert ltr.body == 'actual body content', (
        f'Expected "actual body content" but got "{ltr.body}" — body was likely empty due to double read')


# ── Issue #4: missing await on assert_contains in DjangoPost ────────

def test_django_post_assert_contains_is_awaited():
    """DjangoPost.run() must await assert_contains(), not just call it."""
    import inspect
    import ast
    import textwrap

    source_file = 'loadlamb/chalicelib/contrib/requests/django.py'
    with open(source_file) as f:
        source = f.read()

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == 'run':
            for stmt in ast.walk(node):
                # Look for Await nodes wrapping a call to assert_contains
                if isinstance(stmt, ast.Await):
                    call = stmt.value
                    if isinstance(call, ast.Call):
                        func = call.func
                        if isinstance(func, ast.Attribute) and func.attr == 'assert_contains':
                            return  # found awaited assert_contains — test passes
    pytest.fail('assert_contains() in DjangoPost.run() is not awaited — found call without await')
