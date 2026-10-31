from dataclasses import FrozenInstanceError
import pytest
from deploy_checkup.models import Finding, Level


def make_finding():
    return Finding(
        check="https",
        level=Level.FAIL,
        title="Plain HTTP doesn't redirect to HTTPS",
        why="Visitors who type http:// send everything unencrypted.",
        fix="Render redirects automatically; check you're not using a custom domain without TLS.",
)


def test_fields_read_back():
    finding=make_finding()
    
    assert finding.level == Level.FAIL
    assert finding.check == "https"
    assert finding.title == "Plain HTTP doesn't redirect to HTTPS"

def test_why_and_fix_default_to_empty():
    finding = Finding(check="https",level=Level.PASS , title="HTTPS works")
    
    assert finding.why==""
    assert finding.fix==""
    
def test_finding_cannot_be_changed():
    finding = make_finding()
    
    with pytest.raises(FrozenInstanceError):
        finding.title = "WARN"
        
def test_level_from_string():
    assert Level("warning") is Level.WARNING
    
    with pytest.raises(ValueError):
        Level("warn")
def test_could_not_finish_names_the_check_and_error():
    from deploy_checkup.models import could_not_finish

    finding = could_not_finish("cors", TimeoutError("slow"))

    assert finding.level == Level.INFO
    assert finding.title == "Couldn't finish the cors check (TimeoutError)"