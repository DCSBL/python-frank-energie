"""Test for Frank Energie."""

from datetime import datetime

import aiohttp
import pytest

from python_frank_energie import FrankEnergie
from python_frank_energie.exceptions import AuthException, AuthRequiredException

from . import load_fixtures

SIMPLE_DATA_URL = "frank-graphql-prod.graphcdn.app"


@pytest.mark.asyncio
async def test_init_without_authentication():
    """Test init without authentication."""
    api = FrankEnergie()
    assert api.is_authenticated is False


@pytest.mark.asyncio
async def test_init_with_authentication():
    """Test init with authentication."""
    api = FrankEnergie(auth_token="a", refresh_token="b")  # noqa: S106
    assert api.is_authenticated is True


#
# Login tests
#


@pytest.mark.asyncio
async def test_login(aresponses):
    """Test login."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("authentication.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        auth = await api.login("a", "b")  # noqa: S106
        await api.close()

    assert api.is_authenticated is True
    assert auth.authToken == "hello"
    assert auth.refreshToken == "world"


@pytest.mark.asyncio
async def test_login_invalid_credentials(aresponses):
    """Test login with invalid credentials."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("response_with_error.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthException):
            await api.login("a", "b")  # noqa: S106
        await api.close()


@pytest.mark.asyncio
async def test_login_invalid_response(aresponses):
    """Test login with invalid response."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text="{}",
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthException):
            await api.login("a", "b")  # noqa: S106
        await api.close()


#
# RenewToken tests


@pytest.mark.asyncio
async def test_renew_token(aresponses):
    """Test login."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("authentication.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        auth = await api.renewToken("a", "b")  # noqa: S106
        await api.close()

    assert api.is_authenticated is True
    assert auth.authToken == "hello"
    assert auth.refreshToken == "world"


@pytest.mark.asyncio
async def test_renew_token_invalid_credentials(aresponses):
    """Test login with invalid credentials."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("response_with_error.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthException):
            await api.renewToken("a", "b")  # noqa: S106
        await api.close()


@pytest.mark.asyncio
async def test_renew_token_invalid_response(aresponses):
    """Test login with invalid response."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text="{}",
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthException):
            await api.renewToken("a", "b")  # noqa: S106
        await api.close()


#
# Month Summary
#


@pytest.mark.asyncio
async def test_month_summary(aresponses):
    """Test request with authentication."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("month_summary.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session, auth_token="a", refresh_token="b")  # noqa: S106
        summary = await api.monthSummary()
        await api.close()

    assert summary is not None
    assert summary.actualCostsUntilLastMeterReadingDate == 12.34
    assert summary.expectedCostsUntilLastMeterReadingDate == 20.00
    assert summary.expectedCosts == 50.00
    assert summary.lastMeterReadingDate == "2023-01-01"


@pytest.mark.asyncio
async def test_month_summary_without_authentication(aresponses):
    """Test request without authentication.

    'month_summary' request requires authentication.
    """
    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthRequiredException):
            await api.monthSummary()
        await api.close()


#
# Invoices
#


@pytest.mark.asyncio
async def test_invoices(aresponses):
    """Test request with authentication."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("invoices.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session, auth_token="a", refresh_token="b")  # noqa: S106
        invoices = await api.invoices()
        await api.close()

    assert invoices is not None
    assert invoices.previousPeriodInvoice.StartDate == datetime(2023, 3, 1)
    assert invoices.previousPeriodInvoice.PeriodDescription == "Maart 2023"
    assert invoices.previousPeriodInvoice.TotalAmount == 140.12

    assert invoices.currentPeriodInvoice.StartDate == datetime(2023, 4, 1)
    assert invoices.currentPeriodInvoice.PeriodDescription == "April 2023"
    assert invoices.currentPeriodInvoice.TotalAmount == 80.34

    assert invoices.upcomingPeriodInvoice.StartDate == datetime(2023, 5, 1)
    assert invoices.upcomingPeriodInvoice.PeriodDescription == "Mei 2023"
    assert invoices.upcomingPeriodInvoice.TotalAmount == 80.34


@pytest.mark.asyncio
async def test_invoices_without_authentication(aresponses):
    """Test request without authentication.

    'invoices' request requires authentication.
    """
    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthRequiredException):
            await api.invoices()
        await api.close()


#
# User
#


@pytest.mark.asyncio
async def test_user(aresponses):
    """Test request with authentication."""
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("user.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session, auth_token="a", refresh_token="b")  # noqa: S106
        user = await api.user()
        await api.close()

    assert user is not None
    assert user.connectionsStatus == "READY"
    assert user.firstMeterReadingDate == "2022-11-20"
    assert user.lastMeterReadingDate == "2022-12-05"
    assert user.advancedPaymentAmount == 99.00
    assert user.hasCO2Compensation is False


@pytest.mark.asyncio
async def test_user_without_authentication(aresponses):
    """Test request without authentication.

    'user' request requires authentication.
    """
    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthRequiredException):
            await api.user()
        await api.close()


#
# Prices
#


@pytest.mark.asyncio
async def test_prices(aresponses):
    """Test request without authentication.

    'prices' request does not require authentication.
    """
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("market_prices.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        prices = await api.prices(datetime.utcnow().date(), datetime.utcnow().date())
        await api.close()

    assert prices.electricity is not None
    assert len(prices.electricity.price_data) == 24

    assert prices.gas is not None
    assert len(prices.gas.price_data) == 24
