import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ── Issue #5: no bare except ─────────────────────────────────────────

def test_no_bare_except_in_utils():
    """utils.py must not contain any bare except: clauses."""
    import ast
    with open('loadlamb/chalicelib/utils.py') as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            pytest.fail(
                f'Bare except: found at line {node.lineno} in utils.py — '
                'use "except Exception:" at minimum')


def test_dynamodb_failure_is_logged_not_silenced(capsys):
    """DynamoDB global table failure must be printed, not silently swallowed."""
    from loadlamb.chalicelib.utils import Deploy

    with patch.object(Deploy, 'build_clients_resources'):
        deploy = Deploy({'regions': ['us-east-1']})

    deploy.r = MagicMock()
    deploy.s = MagicMock()
    deploy.s3t = MagicMock()
    deploy.s3 = MagicMock()

    with patch.object(deploy, 'create_package_name'), \
         patch.object(deploy, 'create_package'), \
         patch.object(deploy, 'remove_zip_venv'), \
         patch.object(deploy, 'upload_zip', return_value=('bucket', 'key')), \
         patch.object(deploy, 'build_clients_resources'), \
         patch('loadlamb.chalicelib.utils.docb_handler') as mock_docb:

        mock_stack = MagicMock()
        mock_stack.outputs = [{'OutputKey': 'bucket', 'OutputValue': 'test-bucket'}]
        deploy.s.cf_resource.Stack.return_value = mock_stack

        mock_docb.publish_global.side_effect = Exception('DynamoDB error')

        deploy.project_config = {'regions': ['us-east-1']}
        deploy.publish()

    captured = capsys.readouterr()
    assert any(word in captured.out for word in ('DynamoDB', 'Warning', 'failed')), (
        'DynamoDB failure was silently swallowed — must print a warning')


# ── Issue #9: no private _base module reference ──────────────────────

def test_no_private_futures_base_in_load():
    """load.py must not reference concurrent.futures._base."""
    with open('loadlamb/chalicelib/load.py') as f:
        source = f.read()
    assert 'concurrent.futures._base' not in source, (
        'load.py references private concurrent.futures._base — '
        'use asyncio.TimeoutError or concurrent.futures.TimeoutError instead')


def test_load_catches_public_timeout_error():
    """LoadLamb.run() must catch a public TimeoutError variant."""
    import ast
    with open('loadlamb/chalicelib/load.py') as f:
        source = f.read()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            type_str = ast.dump(node.type)
            if 'TimeoutError' in type_str and '_base' not in type_str:
                return  # found a public TimeoutError handler

    pytest.fail(
        'load.py does not catch a public TimeoutError — '
        'add asyncio.TimeoutError or concurrent.futures.TimeoutError')
