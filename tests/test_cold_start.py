from deploy_checkup.checks.cold_start import check_cold_start
from deploy_checkup.models import Level


def test_slow_first_request_is_a_hint():
    finding = check_cold_start([48000.0, 120.0, 110.0])

    assert finding.level == Level.INFO
    assert "48.0 s" in finding.title
    assert "115 ms" in finding.title


def test_even_times_mean_no_cold_start():
    finding = check_cold_start([130.0, 120.0, 110.0])

    assert finding.level == Level.PASS


def test_slightly_slow_first_request_is_not_a_cold_start():
    finding = check_cold_start([900.0, 120.0, 110.0])

    assert finding.level == Level.PASS


def test_slow_api_overall_is_not_a_cold_start():
    finding = check_cold_start([6000.0, 5500.0, 5800.0])

    assert finding.level == Level.PASS