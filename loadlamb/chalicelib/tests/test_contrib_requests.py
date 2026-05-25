def test_remote_login_importable():
    """RemoteLogin must import without errors."""
    from loadlamb.chalicelib.contrib.requests.login import RemoteLogin
    assert RemoteLogin is not None


def test_remote_login_is_request_subclass():
    """RemoteLogin must be a subclass of Request."""
    from loadlamb.chalicelib.contrib.requests.login import RemoteLogin
    from loadlamb.chalicelib.request import Request
    assert issubclass(RemoteLogin, Request)
