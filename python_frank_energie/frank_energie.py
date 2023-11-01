"""FrankEnergie API implementation."""
# python_frank_energie/frank_energie.py

import asyncio
from datetime import date, timedelta
from typing import Any, Optional

import aiohttp
import requests

from aiohttp.client import ClientSession, ClientResponse
from aiohttp.client_exceptions import ClientError
from http import HTTPStatus

from .exceptions import (
    AuthException,
    AuthRequiredException,
    FrankEnergieException,
)
from .models import (
    Authentication,
    Invoices,
    Invoice,
    MarketPrices,
    MonthSummary,
    MonthInsights,
    User,
)

VERSION = "5.0.1"

class FrankEnergie(object):
    """FrankEnergie API."""

    DATA_URL = "https://frank-graphql-prod.graphcdn.app/"

    def __init__(
        self,
        clientsession: Optional[ClientSession] = None,
        auth_token: Optional[str] | None = None,
        refresh_token: Optional[str] | None = None,
    ) -> None:
        """Initialize the FrankEnergie client."""
        self._close_session: bool = False
        self._auth: Optional[Authentication] | None = None
        self._session = clientsession

        if auth_token is not None or refresh_token is not None:
            self._auth = Authentication(auth_token, refresh_token)

    async def _query(self, query: dict[str, Any]) -> dict[str, Any]:
        """Send a query to the FrankEnergie API.

        Args:
            query: The GraphQL query as a dictionary.

        Returns:
            The response from the API as a dictionary.

        Raises:
            FrankEnergieException: If the request fails.
        """
        if self._session is None:
            self._session = ClientSession()
            self._close_session = True

        try:
            #print(f"Request: POST {self.DATA_URL}")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._auth.authToken}"
            } if self._auth is not None else None
            #print(f"Request headers: {headers}")
            print(f"Request payload: {query}")

            async with self._session.post(
                self.DATA_URL, json=query, headers=headers
            ) as resp:
                resp.raise_for_status()
                response = await resp.json()

            self._process_diagnostic_data(response)
            self._handle_errors(response)

            #print(f"Response status code: {resp.status}")
            #print(f"Response headers: {resp.headers}")
            print(f"Response body: {response}")

            if resp.status == 200:
                return response

        except (asyncio.TimeoutError, ClientError, KeyError) as error:
            raise FrankEnergieException(f"Request failed: {error}") from error
        except Exception as error:
            import traceback
            traceback.print_exc()
            raise error

        
    def _process_diagnostic_data(self, response: dict[str, Any]) -> None:
        """Process the diagnostic data and update the sensor state.

        Args:
            response: The API response as a dictionary.
        """
        diagnostic_data = response.get("diagnostic_data")
        if diagnostic_data:
            self._frank_energie_diagnostic_sensor.update_diagnostic_data(diagnostic_data)

    def _handle_errors(self, response: dict[str, Any]) -> None:
        """Catch common error messages and raise a more specific exception.

        Args:
            response: The API response as a dictionary.
        """

        errors = response.get("errors")
        if errors:
            for error in errors:
                if error["message"] == "user-error:password-invalid":
                    raise AuthException("Invalid password")
                elif error["message"] == "user-error:auth-not-authorised":
                    raise AuthException("Not authorized")
                elif error["message"] == "user-error:auth-required":
                    raise AuthRequiredException("Authentication required")
                elif error["message"] == "Graphql validation error":
                    raise FrankEnergieException("Request failed: Graphql validation error")
                else:
                    print(error["message"])
                    raise AuthException("Authorization error")
        return

    async def old_login(self, username: str, password: str) -> Authentication:
        """Login and retrieve the authentication token.

        Args:
            username: The user's email.
            password: The user's password.

        Returns:
            The authentication information.

        Raises:
            AuthException: If the login fails.
        """
        try:
            query = {
                "query": """
                    mutation Login($email: String!, $password: String!) {
                        login(email: $email, password: $password) {
                            authToken
                            refreshToken
                            user {
                                email
                                status
                                role
                                updatedAt
                                InviteLinkUser{
                                    User{
                                        email
                                    }
                                }
                                Organization{
                                    Email
                                }
                                OrganizationId
                                PaymentAuthorizations{
                                    status
                                }
                                PushNotificationPriceAlerts{
                                    isEnabled
                                }
                                Signup{
                                    User{
                                        email
                                    }
                                }
                                UserSettings{
                                    rewardPayoutPreference
                                }
                                activePaymentAuthorization{
                                    status
                                }
                                adminRights
                                advancedPaymentAmount
                                connections{
                                    status
                                }
                                connectionsStatus
                                deliverySites{
                                    address{
                                        street
                                        houseNumber
                                        zipCode
                                        city
                                    }
                                }
                                firstMeterReadingDate
                                firstName
                                friendsCount
                                hasCO2Compensation
                                hasInviteLink
                                id
                                lastLogin
                                lastMeterReadingDate
                                lastName
                                meterReadingExportPeriods{
                                    EAN
                                    User{
                                        email
                                    }
                                    cluster
                                    createdAt
                                    from
                                    till
                                    period
                                    segment
                                    type
                                    updatedAt
                                }
                                updatedAt
                                reference
                                __typename
                            }
                            __typename
                        }
                        version
                        __typename
                    }
                """,
                "operationName": "Login",
                "variables": {"email": username, "password": password},
            }

            response = await self._query(query)
            auth_data = None
            if not response is None:
                data = response["data"]
                if not data is None:
                    auth_data = data["login"]
                    user_data = auth_data["user"]
                    self._auth = Authentication.from_dict(response)

            self._handle_errors(response)

            #return User(user_data)
            return self._auth

        except Exception as error:
            import traceback
            traceback.print_exc()
            raise error

    async def login(self, username: str, password: str) -> Authentication:
        """Login and retrieve the authentication token.

        Args:
            username: The user's email.
            password: The user's password.

        Returns:
            The authentication information.

        Raises:
            AuthException: If the login fails.
        """
        try:
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

            response = await self._query(query)
            auth_data = None
            if not response is None:
                data = response["data"]
                if not data is None:
                    auth_data = data["login"]
                    self._auth = Authentication.from_dict(response)

            self._handle_errors(response)

            #return User(user_data)
            return self._auth

        except Exception as error:
            import traceback
            traceback.print_exc()
            raise error

    async def renew_token(self) -> Authentication:
        """Renew the authentication token.

        Returns:
            The renewed authentication information.

        Raises:
            AuthRequiredException: If the client is not authenticated.
            AuthException: If the token renewal fails.
        """
        if self._auth is None:
            raise AuthRequiredException
        if not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

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
            "variables": {
                "authToken": self._auth.authToken,
                "refreshToken": self._auth.refreshToken,
            },
        }

        self._auth = Authentication.from_dict(await self._query(query))
        return self._auth

    async def month_insights(self) -> MonthInsights:
        """Retrieve the month summary for the specified month.

        Args:
            month: The month for which to retrieve the summary. Defaults to the current month.

        Returns:
            The month summary information.

        Raises:
            AuthRequiredException: If the client is not authenticated.
            FrankEnergieException: If the request fails.
        """
        if self._auth is None:
            raise AuthRequiredException
        if not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = {
            "query": """
                query ActualAndExpectedMeterReadings {
                    completenessPercentage
                }
            """,
            "operationName": "ActualAndExpectedMeterReadings",
            "variables": {},
        }

        return MonthInsights.from_dict(await self._query(query))

    async def month_summary(self) -> MonthSummary:
        """Retrieve the month summary for the specified month.

        Args:
            month: The month for which to retrieve the summary. Defaults to the current month.

        Returns:
            The month summary information.

        Raises:
            AuthRequiredException: If the client is not authenticated.
            FrankEnergieException: If the request fails.
        """
        if self._auth is None:
            raise AuthRequiredException
        if not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = {
            "query": """
                query MonthSummary {
                    monthSummary {
                        _id
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
        """Retrieve the invoices data.

        Returns a Invoices object, containing the previous, current and upcoming invoice.
        """
        if self._auth is None:
            raise AuthRequiredException
        if not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = {
            "query": """
                query Invoices {
                    invoices {
                        allInvoices {
                            StartDate
                            PeriodDescription
                            TotalAmount
                        }
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
        """Retrieve the user information.

        Returns:
            The user information.

        Raises:
            AuthRequiredException: If the client is not authenticated.
            FrankEnergieException: If the request fails.
        """
        if self._auth is None:
            raise AuthRequiredException
        if not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = {
            "query": """
                query Me {
                    me {
                        ...UserFields
                    }
                }
                fragment UserFields on User {
                    InviteLinkUser{
                        awardRewardType
                        backendOnly
                        createdAt
                        description
                        discountPerConnection
                        fromName
                        id
                        imageUrl
                        slug
                        status
                        tintColor
                        treesAmountPerConnection
                        type
                        updatedAt
                        usedCount
                    }
                    Organization{
                        Email
                    }
                    OrganizationId
                    PushNotificationPriceAlerts{
                        isEnabled
                    }
                    Signup{
                        User{
                            email
                        }
                    }
                    UserSettings{
                        rewardPayoutPreference
                    }
                    PaymentAuthorizations{
                        status
                    }
                    activePaymentAuthorization{
                        status
                    }
                    adminRights
                    updatedAt
                    createdAt
                    deliverySites{
                        address{
                            street
                            houseNumber
                            zipCode
                            city
                        }
                    }
                    email
                    connectionsStatus
                    connections{
                        status
                    }
                    firstMeterReadingDate
                    firstName
                    friendsCount
                    hasInviteLink
                    id
                    lastLogin
                    lastMeterReadingDate
                    advancedPaymentAmount
                    treesCount
                    hasCO2Compensation
                    status
                    meterReadingExportPeriods{
                        EAN
                        User{
                            email
                            firstName
                            lastName
                        }
                        cluster
                        createdAt
                        from
                        till
                        period
                        segment
                        type
                        updatedAt
                    }
                    notification
                    reference
                    role
                }
            """,
            "operationName": "Me",
            "variables": {},
        }

        return User.from_dict(await self._query(query))


    async def prices(
        self, start_date: Optional[date] | None = None, end_date: Optional[date] | None = None
    ) -> MarketPrices:
        """Get market prices."""
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today() + timedelta(days=1)
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
            "variables": {"startDate": str(start_date), "endDate": str(end_date)},
            "operationName": "MarketPrices",
        }

        return MarketPrices.from_dict(await self._query(query))

    async def user_prices(
            self, start_date: Optional[date] | None = None, end_date: Optional[date] | None = None
    ) -> MarketPrices:
        """Get customer market prices."""
        if self._auth is None:
            raise AuthRequiredException

        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today() + timedelta(days=1)

        query = {
            "query": """
                query CustomerMarketPrices($date: String!) {
                    customerMarketPrices(date: $date) {
                        electricityPrices {
                            id
                            date
                            from
                            till
                            marketPrice
                            marketPriceTax
                            sourcingMarkupPrice: consumptionSourcingMarkupPrice
                            energyTaxPrice: energyTax
                        }
                        gasPrices {
                            id
                            date
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

        return MarketPrices.from_userprices_dict(await self._query(query))

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if the client is authenticated, False otherwise.

        Does not actually check if the token is valid.
        """
        return self._auth is not None and self._auth.authToken is not None

    async def close(self) -> None:
        """Close client session."""
        if self._close_session and self._session is not None:
            await self._session.close()
            self._session = None
            self._close_session = False

    async def __aenter__(self):
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

    def introspect_schema(self):
        query = """
            query IntrospectionQuery {
                __schema {
                    types {
                        name
                        fields {
                            name
                        }
                    }
                }
            }
        """

        response = requests.post(self.DATA_URL, json={'query': query})
        response.raise_for_status()
        result = response.json()
        return result

    def get_diagnostic_data(self):
        # Implement the logic to fetch diagnostic data from the FrankEnergie API
        # and return the data as needed for the diagnostic sensor
        return "Diagnostic data"

    
    #introspection_result = introspect_schema(DATA_URL)
    #print(introspection_result)
