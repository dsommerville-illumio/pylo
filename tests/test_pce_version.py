import pytest

from pylo import SoftwareVersion


def test_expected_semantic_version(mock_pce):
    assert mock_pce.pce_version.semantic_version == '21.2.1-532'


def test_gt_comparison(mock_pce):
    assert mock_pce.pce_version > SoftwareVersion('21.2.0-397')


def test_ge_comparison(mock_pce):
    assert mock_pce.pce_version >= SoftwareVersion('21.2.1-532')


def test_lt_comparison(mock_pce):
    assert mock_pce.pce_version < SoftwareVersion('21.3.0')


def test_le_comparison(mock_pce):
    assert mock_pce.pce_version <= SoftwareVersion('21.2.1-532')


def test_eq_comparison(mock_pce):
    assert mock_pce.pce_version == SoftwareVersion('21.2.1-532')


def test_invalid_input(mock_pce):
    with pytest.raises(AttributeError):
        mock_pce.pce_version > 'foo'
