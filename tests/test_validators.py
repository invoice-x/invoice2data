import pytest

from invoice2data.extract.validators import classify_identifier
from invoice2data.extract.validators import validate_bic
from invoice2data.extract.validators import validate_iban
from invoice2data.extract.validators import validate_vat


@pytest.mark.parametrize(
    "value",
    [
        "DE89370400440532013000",
        "NL91ABNA0417164300",
        "GB82WEST12345698765432",
        "GB82 WEST 1234 5698 7654 32",  # spaces are tolerated
        "nl91abna0417164300",  # case is tolerated
    ],
)
def test_validate_iban_accepts_valid(value: str) -> None:
    assert validate_iban(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "DE89370400440532013001",  # last digit altered -> checksum fails
        "GB00WEST12345698765432",  # bad check digits
        "NL91",  # too short
        "1234567890123456",  # no country letters
        "not an iban",
    ],
)
def test_validate_iban_rejects_invalid(value: str) -> None:
    assert validate_iban(value) is False


@pytest.mark.parametrize(
    "value",
    ["NL123456789B01", "DE123456789", "BE0123456789", "FR12345678901", "IT12345678901"],
)
def test_validate_vat_accepts_valid(value: str) -> None:
    assert validate_vat(value) is True


@pytest.mark.parametrize("value", ["XX123456789", "DE12", "12345", "NL123"])
def test_validate_vat_rejects_invalid(value: str) -> None:
    assert validate_vat(value) is False


@pytest.mark.parametrize("value", ["DEUTDEFF", "DEUTDEFF500", "NWBKGB2L"])
def test_validate_bic_accepts_valid(value: str) -> None:
    assert validate_bic(value) is True


@pytest.mark.parametrize("value", ["DEUT1EFF", "ABC", "DEUTDEFF5"])
def test_validate_bic_rejects_invalid(value: str) -> None:
    assert validate_bic(value) is False


def test_classify_identifier_disambiguates() -> None:
    # A valid IBAN is reported as iban (checksum wins over VAT-shaped patterns).
    assert classify_identifier("NL91ABNA0417164300") == "iban"
    # A VAT-shaped value that is not a valid IBAN falls through to vat.
    assert classify_identifier("NL123456789B01") == "vat"
    assert classify_identifier("DEUTDEFF500") == "bic"
    assert classify_identifier("just some text") is None
