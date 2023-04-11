"""Tests for Frank Energie Models."""

import json

import pytest

from python_frank_energie.exceptions import AuthException
from python_frank_energie.models import Authentication, MonthSummary, User

from . import load_fixtures

#
# Tests for Authentication Model.
#


def test_authentication_with_expected_parameters():
    """Test Authentication.from_dict with expected parameters."""
    auth = Authentication.from_dict(json.loads(load_fixtures("authentication.json")))
    assert auth
    assert auth.authToken == "hello"
    assert auth.refreshToken == "world"


def test_authentication_with_missing_parameters():
    """Test Authentication.from_dict with missing parameters."""
    with pytest.raises(AuthException) as excinfo:
        Authentication.from_dict({})

    assert "Unexpected response" in str(excinfo.value)


def test_authentication_with_unexpected_response():
    """Test Authentication.from_dict with unexpected response."""
    with pytest.raises(AuthException):
        Authentication.from_dict({"data": {"login": None}})


def test_authentication_error_message():
    """Test Authentication.from_dict with error message."""
    with pytest.raises(AuthException) as excinfo:
        Authentication.from_dict({"errors": [{"message": "help me"}]})

    assert "help me" in str(excinfo.value)


#
# Tests for User Model.
#


def test_user_with_expected_parameters():
    """Test User.from_dict with expected parameters."""
    user = User.from_dict(json.loads(load_fixtures("user.json")))
    assert user
    assert user.connectionsStatus == "READY"
    assert user.firstMeterReadingDate == "2022-11-20"
    assert user.lastMeterReadingDate == "2022-12-05"
    assert user.advancedPaymentAmount == 99.0
    assert user.hasCO2Compensation is False


def test_user_with_missing_parameters():
    """Test User.from_dict with missing parameters."""
    with pytest.raises(AuthException) as excinfo:
        User.from_dict({})

    assert "Unexpected response" in str(excinfo.value)


def test_user_with_unexpected_response():
    """Test User.from_dict with unexpected response."""
    with pytest.raises(AuthException):
        User.from_dict({"data": {"me": None}})


def test_user_error_message():
    """Test User.from_dict with error message."""
    with pytest.raises(AuthException) as excinfo:
        User.from_dict({"errors": [{"message": "help me"}]})

    assert "help me" in str(excinfo.value)


#
# Tests for MonthSummary Model.
#


def test_month_summary_with_expected_parameters():
    """Test MonthSummary.from_dict with expected parameters."""
    month_summary = MonthSummary.from_dict(
        json.loads(load_fixtures("month_summary.json"))
    )
    assert month_summary
    assert month_summary.actualCostsUntilLastMeterReadingDate == 12.34
    assert month_summary.expectedCostsUntilLastMeterReadingDate == 20.0
    assert month_summary.lastMeterReadingDate == "2023-01-01"


def test_month_summary_with_missing_parameters():
    """Test MonthSummary.from_dict with missing parameters."""
    with pytest.raises(AuthException) as excinfo:
        MonthSummary.from_dict({})

    assert "Unexpected response" in str(excinfo.value)


def test_month_summary_with_unexpected_response():
    """Test MonthSummary.from_dict with unexpected response."""
    with pytest.raises(AuthException):
        MonthSummary.from_dict({"data": {"monthSummary": None}})


def test_month_summary_error_message():
    """Test MonthSummary.from_dict with error message."""
    with pytest.raises(AuthException) as excinfo:
        MonthSummary.from_dict({"errors": [{"message": "help me"}]})

    assert "help me" in str(excinfo.value)
