import httpx

from deploy_checkup.checks.reachable import check_reachable

def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))

def test_ok_response_passes():
    client = make_client(lambda request: httpx.Response(200))
    
    assert check_reachable(client, "https://example.com") =="pass"
    
def test_server_error_fails():
    client = make_client(lambda request: httpx.Response(500))
    
    assert check_reachable(client,"https://example.com") =="fail"
    
def test_connection_error_fails():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)
    client = make_client(handler)
    
    assert check_reachable(client,"https://example.com") =="fail"