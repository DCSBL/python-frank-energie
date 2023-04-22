"""FrankEnergie API implementation."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from aiohttp.client import ClientError, ClientSession

from .exceptions import AuthRequiredException
from .models import Authentication, Invoices, MarketPrices, MonthSummary, User


class FrankEnergie:
    """FrankEnergie API."""

    DATA_URL = "https://frank-graphql-prod.graphcdn.app/"

    def __init__(
        self,
        clientsession: ClientSession = None,
        auth_token: str | None = None,
        refresh_token: str | None = None,
    ):
        """Initialize the FrankEnergie client."""
        self._close_session: bool = False
        self._auth: Authentication | None = None
        self._session = clientsession

        if auth_token is not None or refresh_token is not None:
            self._auth = Authentication(auth_token, refresh_token)

    async def _query(self, query):
        if self._session is None:
            self._session = ClientSession()
            self._close_session = True

        try:
            resp = await self._session.post(
                self.DATA_URL,
                json=query,
                headers={"Authorization": f"Bearer {self._auth.authToken}"}
                if self._auth is not None
                else None,
            )

            return await resp.json()

        except (asyncio.TimeoutError, ClientError, KeyError) as error:
            raise ValueError(f"Request failed: {error}") from error

    async def login(self, username: str, password: str) -> str:
        """Login and get the authentication token."""
        query = {
            "query": """
                mutation Login($email: String!, $password: String!) {
                    login(email: $email, password: $password) {
                        authToken
                        refreshToken
                    }
                }
            """,
            "operationName": "Login",
            "variables": {"email": username, "password": password},
        }

        self._auth = Authentication.from_dict(await self._query(query))
        return self._auth

    async def renewToken(self, authToken: str, refreshToken: str) -> str:
        """Renew the authentication token."""
        query = {
            "query": """
                mutation RenewToken($authToken: String!, $refreshToken: String!) {
                    renewToken(authToken: $authToken, refreshToken: $refreshToken) {
                        authToken
                        refreshToken
                    }
                }
            """,
            "operationName": "RenewToken",
            "variables": {"authToken": authToken, "refreshToken": refreshToken},
        }

        json = await self._query(query)
        print(json)

        self._auth = Authentication.from_dict(json)
        return self._auth

    async def monthSummary(self) -> MonthSummary:
        """Get month summary data."""
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
                query MonthSummary {
                    monthSummary {
                        actualCostsUntilLastMeterReadingDate
                        expectedCostsUntilLastMeterReadingDate
                        expectedCosts
                        lastMeterReadingDate
                    }
                }
            """,
            "operationName": "MonthSummary",
            "variables": {},
        }

        return MonthSummary.from_dict(await self._query(query))

    async def invoices(self) -> Invoices:
        """Get invoices data.

        Returns a Invoices object, containing the previous, current and upcoming invoice.
        """
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
                query Invoices {
                    invoices {
                        previousPeriodInvoice {
                            StartDate
                            PeriodDescription
                            TotalAmount
                        }
                        currentPeriodInvoice {
                            StartDate
                            PeriodDescription
                            TotalAmount
                        }
                        upcomingPeriodInvoice {
                            StartDate
                            PeriodDescription
                            TotalAmount
                        }
                    }
                }
            """,
            "operationName": "Invoices",
            "variables": {},
        }

        data = await self._query(query)
        print(data)
        return Invoices.from_dict(data)

        # return Invoices.from_dict(await self._query(query))

    async def user(self) -> User:
        """Get user data."""
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
                query Me {
                    me {
                        ...UserFields
                    }
                }
                fragment UserFields on User {
                    connectionsStatus
                    firstMeterReadingDate
                    lastMeterReadingDate
                    advancedPaymentAmount
                    treesCount
                    hasCO2Compensation
                }
            """,
            "operationName": "Me",
            "variables": {},
        }

        return User.from_dict(await self._query(query))

    async def prices(
        self, start_date: datetime, end_date: datetime | None = None
    ) -> MarketPrices:
        """Get market prices."""
        query_data = {
            "query": """
                query MarketPrices($startDate: Date!, $endDate: Date!) {
                    marketPricesElectricity(startDate: $startDate, endDate: $endDate) {
                       from till marketPrice marketPriceTax sourcingMarkupPrice energyTaxPrice
                    }
                    marketPricesGas(startDate: $startDate, endDate: $endDate) {
                       from till marketPrice marketPriceTax sourcingMarkupPrice energyTaxPrice
                    }
                }
            """,
            "variables": {"startDate": str(start_date), "endDate": str(end_date)},
            "operationName": "MarketPrices",
        }

        return MarketPrices.from_dict(await self._query(query_data))

    @property
    def is_authenticated(self) -> bool:
        """Return if client is authenticated.

        Does not actually check if the token is valid.
        """
        return self._auth is not None

    async def close(self) -> None:
        """Close client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> FrankEnergie:
        """Async enter.

        Returns:
            The FrankEnergie object.
        """
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.
        """
        await self.close()
