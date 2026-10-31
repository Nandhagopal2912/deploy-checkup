import httpx
from deploy_checkup.models import Finding, Level


CHECK = "headers"
SIX_MONTHS= 15_552_000 #seconds

def check_headers(client: httpx.Client , url:str)->list[Finding]:
    """Check the security of the headers a browser uses to protect visitors."""
    try:
        response = client.get(url, follow_redirects=True)
        
    except httpx.RequestError:
        return []
    
    headers = response.headers
    return [
        _check_hsts(headers),
        _check_content_type_options(headers),
    ]


def _check_hsts(headers: httpx.Headers)->Finding:
    value = headers.get("strict-transport-security")
    if value is None:
        return Finding(
                check=CHECK,
                level=Level.WARNING,
                title="Strict-Transport-Security is missing",
                why=(
                "Without it, a visitor's browser may still try plain HTTP first, "
                "which someone on the same Wi-Fi can intercept."
                    ),
                fix="Send the header Strict-Transport-Security: max-age=31536000 from your app.",        
            )
    
    max_age = _parse_max_age(value)
    if max_age is None or max_age < SIX_MONTHS:
                return Finding(
            check=CHECK,
            level=Level.WARNING,
            title=f"Strict-Transport-Security is too short ({value})",
            why="Browsers forget the HTTPS-only rule quickly, so the protection keeps lapsing.",
            fix="Set max-age to at least 15552000 (6 months); 31536000 (1 year) is common.",
        )
    return Finding(
        check=CHECK,
        level=Level.PASS,
        title=f"Strict-Transport-Security is set (max-age={max_age})",
    )          
    
    
def _parse_max_age(value:str)->int|None:
    """Return the max-age number from the HSTS value, or None if it's missing or invalid"""
    for part in value.split(";"):
        name,_,number = part.strip().partition("=")
        if name.lower() == "max-age":
            try:
                return int(number.strip('"'))
            except ValueError:
                return None
    return None


def _check_content_type_options(headers: httpx.Headers)->Finding:
    value = headers.get("x-content-type-options")
    if value is None or value.strip().lower()!="nosniff":
        return Finding(
            check=CHECK,
            level=Level.WARNING,
            title="X-Content-Type-Options is not nosniff",
            why=(
                "The browser may guess a file's type, so an uploaded file "
                "could be run as a script."
            ),
            fix="Send the header X-Content-Type-Options: nosniff from your app.",
        )
        
    return Finding(check=CHECK, level=Level.PASS, title="X-Content-Type-Options is nosniff")