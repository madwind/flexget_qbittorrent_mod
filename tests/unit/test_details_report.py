import pytest

from ptsites.utils.details_report import DetailsReport, math_suffix, suffix


@pytest.mark.parametrize('value', [0, 42, 12.5])
def test_transfer_data_accepts_numeric_points(value) -> None:
    assert DetailsReport().transfer_data('points', value) == float(value)


@pytest.mark.parametrize('key', ['uploaded', 'downloaded', 'share_ratio', 'seeding', 'leeching', 'hr'])
def test_transfer_data_accepts_numeric_values_for_all_report_fields(key: str) -> None:
    assert DetailsReport().transfer_data(key, 0) == 0.0


def test_transfer_data_still_converts_point_suffixes() -> None:
    assert DetailsReport().transfer_data('points', '1.5 K') == 1500.0


def test_transfer_data_still_converts_byte_suffixes() -> None:
    assert DetailsReport().transfer_data('uploaded', '1.5 GiB') == 1.5 * 1024 ** 3


def test_convert_suffix_accepts_numbers_directly() -> None:
    report = DetailsReport()

    assert report.convert_suffix(0, math_suffix) == 0.0
    assert report.convert_suffix(1024, suffix) == 1024.0
