from importlib.metadata import version

import pytest 
from deploy_checkup.cli import main

def test_prints_url_api(capsys):
    exit_code = main(["https://example.com","--api","https://api.example.com"])
    
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "https://example.com" in output
    assert "https://api.example.com" in output
    

def test_missing_url_exits_with_code_2():
    with pytest.raises(SystemExit) as exc:
        main([])
    
    assert exc.value.code ==2
    

def test_version_prints_installed_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    
    assert exc.value.code ==0
    assert version("deploy-checkup") in capsys.readouterr().out
    