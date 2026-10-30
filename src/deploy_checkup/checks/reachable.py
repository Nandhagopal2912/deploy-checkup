import httpx

from deploy_checkup.models import Finding,Level


CHECK = "reachable"

def check_reachable(client:httpx.Client , url:str)->list[Finding]:
    """Report whether the url answers, and how"""
    
    try:
        response = client.get(url)
    except httpx.RequestError:
        return[
            Finding(
                check=CHECK,
                level=Level.FAIL,
                title="Couldn't connect to the site",
                why="Nobody can use your app if the address doesn't answer.",
                fix = (
                "Check the URL is right, then open the service in the Render dashboard and look at the Events and Logs tabs."
                ),
            )
        ]
        
    status = response.status_code
    title =  f"Site answered with status {status}"
    
    if status>=500:
        return [
            Finding(
                check=CHECK,
                level=Level.FAIL,
                title=title,
                why="Your server hit an error, so visitors see a broken page instead of your app.",
                fix=(
                    "Open the service's Logs tab on Render. A 502 or 503 usually means "
                    "the app crashed on startup or is still deploying."
                ),
            )
        ]
    
    if status>=400:
        return [
            Finding(
                check=CHECK,
                level=Level.WARNING,
                title=title,
                why="Visitors to this address get an error page instead of your app.",
                fix="Check the URL is the page you meant to test, for example your home page.",
            )
        ]
    
    return [Finding(check=CHECK,level=Level.PASS,title=title)]
              
