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
        _check_csp(headers),
        _check_frame_options(headers),
        _check_referrer_policy(headers),
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

def _check_csp(headers: httpx.Headers)-> Finding:
    if headers.get("content-security-policy") is None:
        return Finding(
            check=CHECK,
            level=Level.WARNING,
            title="Content-Security-Policy is missing",
            why=(
                "If an attacker manages to inject a script into your page, the browser "
                "will run it. A policy tells the browser which scripts are allowed."
            ),
            fix=(
                "Start with Content-Security-Policy: default-src 'self' and loosen it "
                "only for the outside sources your frontend really uses."
            ),            
        )
    return Finding(check=CHECK , level=Level.PASS,title="Content-Security-Policy is set")

def _check_frame_options(headers: httpx.Headers) -> Finding:
    value = headers.get("x-frame-options", "").strip().upper()
    csp = headers.get("content-security-policy","").strip().lower()
    
    if value in ("DENY","SAMEORIGIN"):
        return Finding(check=CHECK , level=Level.PASS , title=f"X-Frame-Options is {value}")
    
    if "frame-ancestors" in csp:
        return Finding(
            check=CHECK,
            level=Level.PASS,
            title="X-Frame-Options isn't needed (CSP sets frame-ancestors)",
        )
    
    return Finding(
        check=CHECK,
        level=Level.WARNING,
        title="X-Frame-Options is missing",
        why=(
            "Another site can load yours inside an invisible frame and trick "
            "visitors into clicking buttons they can't see."
        ),
        fix="Send X-Frame-Options: DENY, or add frame-ancestors 'none' to your CSP.",
    )
    

def _check_referrer_policy(headers: httpx.Headers)->Finding:
    value = headers.get("referrer-policy")
    if value is None:
        return Finding(
            check=CHECK,
            level=Level.INFO,
            title="Referrer-Policy is not set",
            why=(
                "Modern browsers already default to a safe policy, but setting it "
                "makes the behaviour the same in every browser."
            ),
            fix="Send Referrer-Policy: strict-origin-when-cross-origin.",
        )
    return Finding(check=CHECK, level=Level.PASS, title=f"Referrer-Policy is {value}")