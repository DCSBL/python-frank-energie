"""Tests for Frank Energie Models."""

import json

import pytest
from freezegun import freeze_time
from syrupy.assertion import SnapshotAssertion

from python_frank_energie.exceptions import AuthException, RequestException
from python_frank_energie.models import (
    Authentication,
    Invoices,
    MarketPrices,
    MonthSummary,
    User,
)

from . import load_fixtures

#
# Tests for Authentication Model.
#


def test_authentication_with_expected_parameters(snapshot: SnapshotAssertion):
    """Test Authentication.from_dict with expected parameters."""
    auth = Authentication.from_dict(json.loads(load_fixtures("authentication.json")))

    assert auth == snapshot


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


def test_user_with_expected_parameters(snapshot: SnapshotAssertion):
    """Test User.from_dict with expected parameters."""
    user = User.from_dict(json.loads(load_fixtures("user.json")))
    assert user == snapshot


def test_user_with_missing_parameters():
    """Test User.from_dict with missing parameters."""
    with pytest.raises(RequestException) as excinfo:
        User.from_dict({})

    assert "Unexpected response" in str(excinfo.value)


def test_user_with_unexpected_response():
    """Test User.from_dict with unexpected response."""
    with pytest.raises(RequestException):
        User.from_dict({"data": {"me": None}})


def test_user_error_message():
    """Test User.from_dict with error message."""
    with pytest.raises(RequestException) as excinfo:
        User.from_dict({"errors": [{"message": "help me"}]})

    assert "help me" in str(excinfo.value)


#
# Tests for MonthSummary Model.
#


def test_month_summary_with_expected_parameters(snapshot: SnapshotAssertion):
    """Test MonthSummary.from_dict with expected parameters."""
    month_summary = MonthSummary.from_dict(
        json.loads(load_fixtures("month_summary.json"))
    )
    assert month_summary == snapshot


def test_month_summary_with_missing_parameters():
    """Test MonthSummary.from_dict with missing parameters."""
    with pytest.raises(RequestException) as excinfo:
        MonthSummary.from_dict({})

    assert "Unexpected response" in str(excinfo.value)


def test_month_summary_with_unexpected_response():
    """Test MonthSummary.from_dict with unexpected response."""
    with pytest.raises(RequestException):
        MonthSummary.from_dict({"data": {"monthSummary": None}})


def test_month_summary_error_message():
    """Test MonthSummary.from_dict with error message."""
    with pytest.raises(RequestException) as excinfo:
        MonthSummary.from_dict({"errors": [{"message": "help me"}]})

    assert "help me" in str(excinfo.value)


#
# Tests for MarketPrices Model.
#


def test_market_prices_with_expected_parameters(snapshot: SnapshotAssertion):
    """Test MarketPrices.from_dict with expected parameters."""
    market_prices = MarketPrices.from_dict(
        json.loads(load_fixtures("market_prices.json"))
    )

    assert [market_prices.electricity.all, market_prices.gas.all] == snapshot


def test_market_prices_with_missing_parameters():
    """Test MarketPrices.from_dict with missing parameters."""
    with pytest.raises(RequestException) as excinfo:
        MarketPrices.from_dict({})

    assert "Unexpected response" in str(excinfo.value)


def test_market_prices_error_message():
    """Test MarketPrices.from_dict with error message."""
    with pytest.raises(RequestException) as excinfo:
        MarketPrices.from_dict({"errors": [{"message": "help me"}]})

    assert "help me" in str(excinfo.value)


@freeze_time("2022-11-21 14:15:00")
def test_market_prices_pricedata_current_hour(snapshot: SnapshotAssertion):
    """Test functionality of MarketPrices.price_data."""
    market_prices = MarketPrices.from_dict(
        json.loads(load_fixtures("market_prices.json"))
    )

    assert [market_prices.electricity.all, market_prices.gas.all] == snapshot


@freeze_time("2022-11-21 14:15:00")
def test_market_prices_pricedata_next_hour(snapshot: SnapshotAssertion):
    """Test functionality of MarketPrices.price_data."""
    market_prices = MarketPrices.from_dict(
        json.loads(load_fixtures("market_prices.json"))
    )

    future_prices = market_prices.electricity.get_future_prices()
    assert future_prices == snapshot


#
# Tests for Invoices Model.
#


def test_invoices_with_expected_parameters(snapshot: SnapshotAssertion):
    """Test Invoices.from_dict with expected parameters."""
    invoices = Invoices.from_dict(json.loads(load_fixtures("invoices.json")))

    assert invoices == snapshot


def test_invoices_with_missing_parameters():
    """Test Invoices.from_dict with missing parameters."""
    with pytest.raises(RequestException) as excinfo:
        Invoices.from_dict({})

    assert "Unexpected response" in str(excinfo.value)


def test_invoices_error_message():
    """Test Invoices.from_dict with error message."""
    with pytest.raises(RequestException) as excinfo:
        Invoices.from_dict({"errors": [{"message": "help me"}]})

    assert "help me" in str(excinfo.value)


def test_invoices_none_data():
    """Test Invoices.from_dict with None data."""
    invoices = Invoices.from_dict(
        {
            "data": {
                "invoices": {
                    "previousPeriodInvoice": None,
                    "currentPeriodInvoice": None,
                    "upcomingPeriodInvoice": None,
                }
            }
        }
    )

    assert invoices.previousPeriodInvoice is None
    assert invoices.currentPeriodInvoice is None
    assert invoices.upcomingPeriodInvoice is None
