"""Test for Frank Energie."""

from datetime import datetime

import aiohttp
import pytest
from syrupy.assertion import SnapshotAssertion

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
async def test_login(aresponses, snapshot: SnapshotAssertion):
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
    assert auth == snapshot


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
async def test_renew_token(aresponses, snapshot: SnapshotAssertion):
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
        api = FrankEnergie(session, "a", "b")  # noqa: S106
        auth = await api.renew_token()
        await api.close()

    assert api.is_authenticated is True
    assert auth == snapshot


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
        api = FrankEnergie(session, "a", "b")  # noqa: S106
        with pytest.raises(AuthException):
            await api.renew_token()
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
        api = FrankEnergie(session, "a", "b")  # noqa: S106
        with pytest.raises(AuthException):
            await api.renew_token()
        await api.close()


#
# Month Summary
#


@pytest.mark.asyncio
async def test_month_summary(aresponses, snapshot: SnapshotAssertion):
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
        summary = await api.month_summary()
        await api.close()

    assert summary is not None
    assert summary == snapshot


@pytest.mark.asyncio
async def test_month_summary_without_authentication(aresponses):
    """Test request without authentication.

    'month_summary' request requires authentication.
    """
    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session)
        with pytest.raises(AuthRequiredException):
            await api.month_summary()
        await api.close()


#
# Invoices
#


@pytest.mark.asyncio
async def test_invoices(aresponses, snapshot: SnapshotAssertion):
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
    assert invoices == snapshot


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
async def test_user(aresponses, snapshot: SnapshotAssertion):
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
    assert user == snapshot


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
async def test_prices(aresponses, snapshot: SnapshotAssertion):
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

    assert [prices.electricity.all, prices.gas.all] == snapshot


@pytest.mark.asyncio
async def test_user_prices(aresponses, snapshot: SnapshotAssertion):
    """Test request with authentication.

    'prices' request does not require authentication.
    """
    aresponses.add(
        SIMPLE_DATA_URL,
        "/",
        "POST",
        aresponses.Response(
            text=load_fixtures("customer_market_prices.json"),
            status=200,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = FrankEnergie(session, auth_token="a", refresh_token="b")  # noqa: S106
        prices = await api.user_prices(datetime.utcnow().date())
        await api.close()

    assert prices.electricity is not None
    assert len(prices.electricity.price_data) == 24

    assert prices.gas is not None
    assert len(prices.gas.price_data) == 24

    assert [prices.electricity.all, prices.gas.all] == snapshot
