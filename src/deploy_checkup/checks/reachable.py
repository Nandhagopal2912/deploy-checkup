import httpx

def check_reachable(client: httpx.Client , url:str)->str:
    """Return "pass" if the url answers without an error ,else fail"""
    
    try:
        response = client.get(url)
    except httpx.RequestError:
        return "fail"
    
    if response.status_code < 400:
        return "pass"
    
    return "fail"