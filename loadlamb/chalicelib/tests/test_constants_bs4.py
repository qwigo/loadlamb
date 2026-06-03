import ast
import warnings
import pytest


# ── Issue #17: BeautifulSoup parser ─────────────────────────────────

def test_beautifulsoup_calls_have_parser():
    """All BeautifulSoup() calls in utils.py must include an explicit parser."""
    with open('loadlamb/chalicelib/utils.py') as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = (func.id if isinstance(func, ast.Name) else
                    func.attr if isinstance(func, ast.Attribute) else None)
            if name == 'BeautifulSoup':
                assert len(node.args) >= 2 or any(k.arg == 'features' for k in node.keywords), (
                    f'BeautifulSoup() at line {node.lineno} in utils.py '
                    f'is missing the parser argument — use BeautifulSoup(..., "html.parser")')


def test_beautifulsoup_no_user_warning(tmp_path):
    """Constructing BeautifulSoup with html.parser must emit no UserWarning."""
    from bs4 import BeautifulSoup
    html = '<form><input type="hidden" name="csrf" value="abc"/></form>'
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        BeautifulSoup(html, 'html.parser')
    user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
    assert not user_warnings, f'Unexpected UserWarnings: {user_warnings}'


# ── Issue #18: constants module ──────────────────────────────────────

def test_constants_module_exists():
    """loadlamb.chalicelib.constants must be importable."""
    from loadlamb.chalicelib import constants
    assert constants is not None


def test_constants_has_required_names():
    """constants.py must define all five resource name constants."""
    from loadlamb.chalicelib import constants
    required = [
        'LAMBDA_FUNCTION_NAME',
        'IAM_ROLE_NAME',
        'S3_STACK_NAME',
        'DYNAMODB_TABLE_NAME',
        'CF_STACK_NAME',
    ]
    for name in required:
        assert hasattr(constants, name), f'constants.py is missing {name}'


def test_constants_correct_values():
    """Constants must have the correct string values."""
    from loadlamb.chalicelib import constants
    assert constants.LAMBDA_FUNCTION_NAME == 'loadlamb-run'
    assert constants.IAM_ROLE_NAME == 'loadlamb-role'
    assert constants.S3_STACK_NAME == 'loadlamb-bucket'
    assert constants.DYNAMODB_TABLE_NAME == 'loadlambddb'
    assert constants.CF_STACK_NAME == 'loadlamb'


def test_utils_uses_constants_not_literals():
    """utils.py must not contain the raw resource name string literals."""
    with open('loadlamb/chalicelib/utils.py') as f:
        source = f.read()
    # These literals should no longer appear as standalone strings in utils.py
    forbidden = ["'loadlamb-run'", "'loadlamb-role'", "'loadlamb-bucket'",
                 "'loadlambddb'", '"loadlamb-run"', '"loadlamb-role"',
                 '"loadlamb-bucket"', '"loadlambddb"']
    for lit in forbidden:
        assert lit not in source, (
            f'Raw string literal {lit} still present in utils.py — use constant from constants.py')
