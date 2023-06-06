"""FrankEnergie API implementation."""

from __future__ import annotations

import logging

import aiohttp

from datetime import date
from typing import Any, Optional

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from aiohttp.client_exceptions import ClientError

from .exceptions import AuthRequiredException
from .models import Authentication, Invoices, MarketPrices, MonthSummary, User

class RequestFailedException(Exception):
    """Exception raised when a request fails."""

    def __init__(self, message="Request failed."):
        super().__init__(message)

class FrankEnergie:
    """FrankEnergie API."""

    DATA_URL = "https://frank-graphql-prod.graphcdn.app/"

    def __init__(
        self,
        clientsession: ClientSession = None,
        auth_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        """Initialize the FrankEnergie client."""
        self._session = clientsession or ClientSession()
        self._auth = Authentication(auth_token, refresh_token)

    async def _query(self, query):
        try:
            headers = (
                {"Authorization": f"Bearer {self._auth.authToken}"}
                if self.is_authenticated
                else {}
            )

            async with self._session.post(
                self.DATA_URL, json=query, headers=headers
            ) as resp:
                response_json = await resp.json()
                return response_json

        except (TimeoutError, ClientError, KeyError) as error:
            raise ValueError(f"Request failed: {error}") from error

    async def login(self, username: str, password: str) -> Authentication:
        """Login and get the authentication token."""
        if not username:
            raise ValueError("Username is required.")
        if not password:
            raise ValueError("Password is required.")

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

        try:
            self._auth = Authentication.from_dict(await self._query(query))
            return self._auth
        except (TimeoutError, ClientError, KeyError) as error:
            raise RequestFailedException(f"Login failed: {error}") from error

    async def renewToken(self, auth_token: str, refresh_token: str) -> Authentication:
        """Renew the authentication token."""
        if not auth_token:
            raise ValueError("Authentication token is required.")
        if not refresh_token:
            raise ValueError("Refresh token is required.")

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
            "variables": {"authToken": auth_token, "refreshToken": refresh_token},
        }

        try:
            json = await self._query(query)
            new_auth = Authentication.from_dict(json)

            self._auth = new_auth  # Update the _auth attribute
            return self._auth
        except (TimeoutError, ClientError, KeyError) as error:
            raise RequestFailedException(f"Token renewal failed: {error}") from error

    async def check_token_validity(self) -> bool:
        """Check if the authentication token is still valid."""
        if not self._auth or not getattr(self._auth, 'authToken', None):
            return False

        headers = {
            "Authorization": f"Bearer {self._auth.authToken}"
        }

        query = """
            query CheckTokenValidity {
                checkTokenValidity {
                    isValid
                }
            }
        """

        async with self._session.post(
            self.DATA_URL, json={'query': query}, headers=headers
        ) as response:
            # Check the response status and content
            if response.status == 200:
                data = await response.json()
                if 'data' in data and 'checkTokenValidity' in data['data']:
                    return data['data']['checkTokenValidity'].get('isValid', False)
                else:
                    return False
            else:
                return False

    async def ensure_authenticated(self) -> bool:
        """Ensure that the client is authenticated and the token is valid.
        
        If the token has expired, attempt to renew it using the refresh token.
        Returns True if the client is authenticated, False otherwise.
        """
        if self.is_authenticated and await self.check_token_validity():
            return True

        if not self._auth or not self._auth.refreshToken:
            return False

        try:
            renewed_auth = await self.renewToken(
                self._auth.authToken, self._auth.refreshToken
            )
            self._auth = renewed_auth
            return True
        except RequestFailedException:
            raise AuthRequiredException("Failed to renew authentication token.")

    async def monthSummary(self) -> MonthSummary:
        """Get month summary data."""

        self._check_auth_required()
        await self.ensure_authenticated()

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
        self._check_auth_required()
        await self.ensure_authenticated()

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

        return Invoices.from_dict(await self._query(query))

    async def user(self) -> User:
        """Get user data."""
        self._check_auth_required()
        await self.ensure_authenticated()

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
        self, start_date: date, end_date: Optional[date] = None
    ) -> MarketPrices:
        """Get market prices."""
        query = {
            "query": """
                query MarketPrices($startDate: Date!, $endDate: Date!) {
                    marketPricesElectricity(startDate: $startDate, endDate: $endDate) {
                        from
                        till
                        marketPrice
                        marketPriceTax
                        sourcingMarkupPrice
                        energyTaxPrice
                    }
                    marketPricesGas(startDate: $startDate, endDate: $endDate) {
                        from
                        till
                        marketPrice
                        marketPriceTax
                        sourcingMarkupPrice
                        energyTaxPrice
                    }
                }
            """,
            "operationName": "MarketPrices",
            "variables": {
                "startDate": str(start_date),
                 "endDate": end_date.isoformat() if end_date else None,
            },
        }

        return MarketPrices.from_dict(await self._query(query))

    async def userPrices(self, start_date: date) -> MarketPrices:
        """Get customer market prices."""

        self._check_auth_required()
        await self.ensure_authenticated()

        query = {
            "query": """
                query CustomerMarketPrices($date: String!) {
                    customerMarketPrices(date: $date) {
                        electricityPrices {
                            from
                            till
                            marketPrice
                            marketPriceTax
                            sourcingMarkupPrice: consumptionSourcingMarkupPrice
                            energyTaxPrice: energyTax
                        }
                        gasPrices {
                            from
                            till
                            marketPrice
                            marketPriceTax
                            sourcingMarkupPrice: consumptionSourcingMarkupPrice
                            energyTaxPrice: energyTax
                        }
                    }
                }
            """,
            "variables": {"date": str(start_date)},
            "operationName": "CustomerMarketPrices",
        }

        return MarketPrices.from_dict(await self._query(query))

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self._auth is not None and self._auth.authToken is not None

    def _check_auth_required(self):
        """Check if authentication is required for the API endpoint."""
        if not self.is_authenticated:
            raise AuthRequiredException("Authentication token is missing.")

    def _raise_auth_required(self):
        """Raise an exception indicating authentication is required."""
        raise AuthRequiredException("Authentication is required to access this resource.")

    async def close(self) -> None:
        """Close client session."""
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
