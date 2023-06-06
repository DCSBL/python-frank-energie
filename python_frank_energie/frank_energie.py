"""FrankEnergie API implementation."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientError

from .exceptions import AuthRequiredException
from .models import Authentication, Invoices, MarketPrices, MonthSummary, User, Consumption

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
        self._logger = logging.getLogger(__name__)

    async def _execute_query(self, query_name: str, query: dict) -> dict:
        """Execute a GraphQL query and handle errors."""
        try:
            return await self._query(query)
        except (ValueError, ClientError) as error:
            raise RequestFailedException(f"{query_name} failed: {error}") from error

    async def _query(self, query):
        """Construct and execute a GraphQL query."""
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

                # Log request and response information
                self._logger.debug("Request URL: %s", resp.url)
                self._logger.debug("Request Headers: %s", resp.request_info.headers)
                self._logger.debug("Request JSON Body: %s", query)
                self._logger.debug("Response Status: %s", resp.status)
                self._logger.debug("Response Headers: %s", resp.headers)
                self._logger.debug("Response Body: %s", response_json)

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

        response = await self._execute_query("Login", query)
        self._auth = Authentication.from_dict(response)
        return self._auth

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

        response = await self._execute_query("RenewToken", query)
        new_auth = Authentication.from_dict(response)

        self._auth = new_auth
        return self._auth

    async def check_token_validity(self) -> bool:
        """Check if the authentication token is still valid."""
        if not self.is_authenticated:
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

        try:
            async with self._session.post(
                self.DATA_URL, json={'query': query}, headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and 'checkTokenValidity' in data['data']:
                        return data['data']['checkTokenValidity'].get('isValid', False)
        except (TimeoutError, ClientError, KeyError) as error:
            self._logger.error("Token validity check failed: %s", error)

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

        response = await self._execute_query("MonthSummary", query)
        return MonthSummary.from_dict(response)

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

        response = await self._execute_query("Invoices", query)
        return Invoices.from_dict(response)

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

        response = await self._execute_query("Me", query)
        return Invoices.from_dict(response)

    async def prices(
        self, start_date: date, end_date: Optional[date] = None
    ) -> MarketPrices:
        """ Fetch market prices for electricity and gas within a specified date range """
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

        response = await self._execute_query("MarketPrices", query)
        return MarketPrices.from_dict(response)

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

        response = await self._execute_query("CustomerMarketPrices", query)
        return MarketPrices.from_dict(response)

    async def consumption(self, start_date: str, end_date: str) -> Consumption:
        """Get consumption data for a specified date range.

        Args:
            start_date (str): Start date in the format 'YYYY-MM-DD'.
            end_date (str): End date in the format 'YYYY-MM-DD'.

        Returns:
            Consumption: Consumption object containing the consumption data.
        """
        self._check_auth_required()
        await self.ensure_authenticated()

        query = {
            "query": """
                query Consumption($startDate: Date!, $endDate: Date!) {
                    consumption(startDate: $startDate, endDate: $endDate) {
                        start
                        end
                        electricity
                        gas
                    }
                }
            """,
            "operationName": "Consumption",
            "variables": {"startDate": start_date, "endDate": end_date},
        }

        response = await self._execute_query("Consumption", query)
        return Consumption.from_dict(response)

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self._auth and self._auth.authToken

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

"""
In Home Assistant, the prevailing naming convention is snake_case. Home Assistant follows the Python community's style guide, which recommends using snake_case for variable names, function names, and method names. This convention is consistent across the Home Assistant codebase, including its core components, integrations, and custom components developed by the community.
"""
