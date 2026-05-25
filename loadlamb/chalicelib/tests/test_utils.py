import os
import shutil
import sys
import tempfile
from unittest.mock import patch, MagicMock

from loadlamb.chalicelib.utils import grouper, import_util, save_sam_template, read_config_file, create_config_file, \
    create_extension_template

from docb import Document

TEST_CONFIG = {
        'name': 'flask',
        'url': 'http://flask:5000',
        'repo': 'loadlamb',
        'user_num': 10,
        'user_batch_size': 10,
        'user_batch_sleep': 2,
        'tasks': [
            {'path': '/get', 'method_type': 'GET'},
            {'path': '/post', 'method_type': 'POST'},
            {'path': '/bad-get', 'method_type': 'GET'},
        ]
    }


def test_grouper():
    g = grouper(5, 38)
    assert g == [5, 5, 5, 5, 5, 5, 5, 3]


def test_import_util():
    u = import_util('loadlamb.chalicelib.contrib.db.models.Run')
    assert issubclass(u, Document)


def test_save_sam_template():
    save_sam_template()
    assert os.path.isfile('sam.yml')
    os.remove('sam.yml')


def test_create_read_config():
    create_config_file(config=TEST_CONFIG)
    assert os.path.isfile('loadlamb.yaml')
    assert read_config_file('loadlamb.yaml') == TEST_CONFIG
    os.remove('loadlamb.yaml')


def test_create_extension_template():
    create_config_file(config=TEST_CONFIG)
    create_extension_template('jelly', 'Test extension')
    assert read_config_file('loadlamb.yaml') == {'name': 'flask',
                                                 'repo': 'loadlamb',
                                                 'tasks': [{'method_type': 'GET', 'path': '/get'},
                                                           {'method_type': 'POST', 'path': '/post'},
                                                           {'method_type': 'GET', 'path': '/bad-get'}],
                                                 'url': 'http://flask:5000', 'user_batch_size': 10,
                                                 'user_batch_sleep': 2, 'user_num': 10, 'extensions': ['jelly']}
    shutil.rmtree('jelly')
    os.remove('loadlamb.yaml')


# Issue #1 — yaml.safe_load must be used in read_config_file
def test_read_config_file_uses_safe_load():
    """read_config_file() must delegate to yaml.safe_load, not call yaml.load directly."""
    import loadlamb.chalicelib.utils as utils_module

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write('key: value\n')
        tmp_path = f.name

    try:
        with patch.object(utils_module.yaml, 'safe_load', wraps=utils_module.yaml.safe_load) as mock_safe_load:
            result = read_config_file(tmp_path)
            assert mock_safe_load.called, 'read_config_file() must call yaml.safe_load()'
            assert result == {'key': 'value'}, 'read_config_file() must return parsed YAML content'
    finally:
        os.remove(tmp_path)


def test_read_config_file_unsafe_yaml_does_not_execute():
    """Unsafe YAML tags must not result in code execution."""
    import loadlamb.chalicelib.utils as utils_module

    # This YAML payload would execute os.system('echo pwned') with yaml.load()
    unsafe_yaml = "exploit: !!python/object/apply:os.system ['echo pwned']\n"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(unsafe_yaml)
        tmp_path = f.name

    try:
        # yaml.safe_load raises yaml.constructor.ConstructorError on unsafe tags
        import yaml
        try:
            result = read_config_file(tmp_path)
            # If it returns without raising, the value must NOT be an integer (os.system return value)
            assert not isinstance(result.get('exploit'), int), \
                'Unsafe YAML tag was executed — read_config_file() must use yaml.safe_load()'
        except yaml.YAMLError:
            pass  # Raising is the expected safe behaviour
    finally:
        os.remove(tmp_path)


# Issue #3 — install_packages() must use subprocess.run, not pip._internal
def test_install_packages_uses_subprocess_not_pip_internal():
    """Deploy.install_packages() must call subprocess.run with the pip module
    instead of importing from pip._internal."""
    from loadlamb.chalicelib.utils import Deploy

    # Patch build_clients_resources so no real AWS/boto3 calls are made during __init__
    with patch.object(Deploy, 'build_clients_resources'):
        deploy = Deploy({'regions': ['us-east-1']})

    with patch('loadlamb.chalicelib.utils.subprocess.run') as mock_run, \
         patch.object(deploy, 'get_loadlamb_path', return_value='/fake/path'):
        deploy.install_packages()
        assert mock_run.called, 'install_packages() must call subprocess.run'
        call_args = mock_run.call_args[0][0]  # First positional arg (the command list)
        assert call_args[0] == sys.executable, \
            'First argument must be sys.executable'
        assert call_args[1:3] == ['-m', 'pip'], \
            'Command must invoke pip via -m pip'


def test_install_packages_no_pip_internal_import():
    """pip._internal must not be importable from utils."""
    import loadlamb.chalicelib.utils as utils_module
    assert not hasattr(utils_module, '_main'), \
        'utils.py must not expose _main from pip._internal'

