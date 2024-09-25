"""FrankEnergie API implementation."""
# python_frank_energie/frank_energie.py

import asyncio
from datetime import date, timedelta
from http import HTTPStatus
from typing import Any, Optional

import aiohttp
import requests
from aiohttp.client import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientError

from .exceptions import (AuthException, AuthRequiredException, ConnectionException, FrankEnergieError,
                         FrankEnergieException, LoginError, NetworkError, RequestException, SmartTradingNotEnabledException)
from .models import (Authentication, EnergyConsumption, Invoice, Invoices,
                     MarketPrices, Me, MonthInsights, MonthSummary, SmartBatteries, SmartBatterySessions, User)
from .authentication import Authentication

VERSION = "2024.9.25"

class FrankEnergieQuery:
    def __init__(self, query: str, operation_name: str, variables: Optional[dict[str, Any]] = None):
        self.query = query
        self.operation_name = operation_name
        self.variables = variables if variables is not None else {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "operationName": self.operation_name,
            "variables": self.variables,
        }

def sanitize_query(query: FrankEnergieQuery) -> dict[str, Any]:
    sanitized_query = query.to_dict()
    if "password" in sanitized_query["variables"]:
        sanitized_query["variables"]["password"] = "****"
    return sanitized_query

class FrankEnergie:
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

    async def _query(self, query: FrankEnergieQuery) -> dict[str, Any]:
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
            # print(f"Request: POST {self.DATA_URL}")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._auth.authToken}"
            } if self._auth is not None else None
            print(f"Request headers: {headers}")
            sanitized_query = sanitize_query(query)
            print(f"Request payload: {sanitized_query}")

            async with self._session.post(
                self.DATA_URL,
                json=query.to_dict(),
                headers=headers
            ) as resp:
                resp.raise_for_status()
                response = await resp.json()

            #self._process_diagnostic_data(response)
            self._handle_errors(response)

            # print(f"Response status code: {resp.status}")
            # print(f"Response headers: {resp.headers}")
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
            self._frank_energie_diagnostic_sensor.update_diagnostic_data(
                diagnostic_data)

    def _handle_errors(self, response: dict[str, Any]) -> None:
        """Catch common error messages and raise a more specific exception.

        Args:
            response: The API response as a dictionary.
        """

        errors = response.get("errors")
        if errors:
            for error in errors:
                message = error["message"]
                if message == "user-error:password-invalid":
                    raise AuthException("Invalid password")
                elif message == "user-error:auth-not-authorised":
                    raise AuthException("Not authorized")
                elif message == "user-error:auth-required":
                    raise AuthRequiredException("Authentication required")
                elif message == "Graphql validation error":
                    raise FrankEnergieException(
                        "Request failed: Graphql validation error")
                elif message.startswith("No marketprices found for segment"):
                    # raise FrankEnergieException("Request failed: %s", error["message"])
                    return
                elif message.startswith("No connections found for user"):
                    raise FrankEnergieException(
                        "Request failed: %s", message)
                elif message == "user-error:smart-trading-not-enabled":
                    raise SmartTradingNotEnabledException("Smart trading is not enabled for this user.")
                else:
                    print(message)
                    raise AuthException("Authorization error")

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

            # return User(user_data)
            return self._auth

        except Exception as error:
            import traceback
            traceback.print_exc()
            raise error

    LOGIN_QUERY = """
        mutation Login($email: String!, $password: String!) {
            login(email: $email, password: $password) {
                authToken
                refreshToken
            }
            version
            __typename
        }
    """

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
        if not username or not password:
            raise ValueError("Username and password must be provided.")

        query = FrankEnergieQuery(
            self.LOGIN_QUERY,
            "Login",
            {"email": username, "password": password}
        )

        try:
            response = await self._query(query)
            auth_data = None
            if not response is None:
                data = response["data"]
                if not data is None:
                    auth_data = data["login"]
                    self._auth = Authentication.from_dict(response)

            self._handle_errors(response)

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
        if self._auth is None or not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = FrankEnergieQuery(
            """
            mutation RenewToken($authToken: String!, $refreshToken: String!) {
                renewToken(authToken: $authToken, refreshToken: $refreshToken) {
                    authToken
                    refreshToken
                }
            }
            """,
            "RenewToken",
            {
                "authToken": self._auth.authToken,
                "refreshToken": self._auth.refreshToken,
            },
        )

        self._auth = Authentication.from_dict(await self._query(query))
        return self._auth

    async def meter_readings(self) -> EnergyConsumption:
        """Retrieve the meter_readings.

        Args:
            month: The month for which to retrieve the summary. Defaults to the current month.

        Returns:
            The Meter Readings.

        Raises:
            AuthRequiredException: If the client is not authenticated.
            FrankEnergieException: If the request fails.
        """
        if self._auth is None or not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = FrankEnergieQuery(
            """
            query ActualAndExpectedMeterReadings {
            completenessPercentage
            actualMeterReadings {
                date
                consumptionKwh
            }
            expectedMeterReadings {
                date
                consumptionKwh
            }
            }
            """,
            "ActualAndExpectedMeterReadings",
            {},
        )

        return EnergyConsumption.from_dict(await self._query(query))

    async def month_summary(self, site_reference: str) -> MonthSummary:
        """Retrieve the month summary for the specified month.

        Args:
            month: The month for which to retrieve the summary. Defaults to the current month.

        Returns:
            The month summary information.

        Raises:
            AuthRequiredException: If the client is not authenticated.
            FrankEnergieException: If the request fails.
        """
        if self._auth is None or not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = FrankEnergieQuery(
            """
            query MonthSummary($siteReference: String!) {
                monthSummary(siteReference: $siteReference) {
                    _id
                    actualCostsUntilLastMeterReadingDate
                    expectedCostsUntilLastMeterReadingDate
                    expectedCosts
                    lastMeterReadingDate
                    meterReadingDayCompleteness
                    gasExcluded
                    __typename
                }
                version
                __typename
            }
            """,
            "MonthSummary",
            {"siteReference": site_reference},
        )

        try:
            response = await self._query(query)
            return MonthSummary.from_dict(response)
        except Exception as e:
            raise FrankEnergieException(f"Failed to fetch month summary: {str(e)}")

    async def UserEnergyConsumption(self) -> EnergyConsumption:
        if self._auth is None:
            raise AuthRequiredException
        if not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = FrankEnergieQuery(
            """
            query GetUserEnergyConsumption {
            user {
                id
                energyConsumption {
                daily {
                    date
                    consumptionKwh
                }
                }
            }
            }
            """,
            "GetUserEnergyConsumption",
            {},
        )

        return EnergyConsumption.from_dict(await self._query(query))

    async def invoices(self, site_reference: str) -> Invoices:
        """Retrieve the invoices data.

        Returns a Invoices object, containing the previous, current and upcoming invoice.
        """
        if self._auth is None or not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = FrankEnergieQuery(
            """
            query Invoices($siteReference: String!) {
                invoices(siteReference: $siteReference) {
                    allInvoices {
                        StartDate
                        PeriodDescription
                        TotalAmount
                        __typename
                    }
                    previousPeriodInvoice {
                        StartDate
                        PeriodDescription
                        TotalAmount
                        __typename
                    }
                    currentPeriodInvoice {
                        StartDate
                        PeriodDescription
                        TotalAmount
                        __typename
                    }
                    upcomingPeriodInvoice {
                        StartDate
                        PeriodDescription
                        TotalAmount
                        __typename
                    }
                __typename
                }
            __typename
            }
            """,
            "Invoices",
            {"siteReference": site_reference},
        )

        return Invoices.from_dict(await self._query(query))

    async def fail_user(self) -> User:
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

        query = FrankEnergieQuery(
            """
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
                hasCO2Compensation
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
                status
                treesCount
                updatedAt
            }
            """,
            "Me",
            {},
        )

        return User.from_dict(await self._query(query))

    async def user(self, site_reference: str | None = None) -> User:
        """Retrieve the user information.

        Returns:
            The user information.

        Raises:
            AuthRequiredException: If the client is not authenticated.
            FrankEnergieException: If the request fails.
        """
        if self._auth is None or not self.is_authenticated:
            raise AuthRequiredException("Authentication is required.")

        query = FrankEnergieQuery(
            """
            query Me($siteReference: String) {
                me {
                    ...UserFields
                }
            }
            fragment UserFields on User {
                InviteLinkUser{
                    awardRewardType
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
                    id
                    isEnabled
                    type
                    weekdays
                }
                Signup{
                    id
                    User{
                        id
                        email
                    }
                }
                UserSettings{
                    id
                    disabledHapticFeedback
                    jedlixUserId
                    jedlixPushNotifications
                    smartPushNotifications
                    rewardPayoutPreference
                }
                PaymentAuthorizations{
                    status
                }
                activePaymentAuthorization{
                    id
                    mandateId
                    signedAt
                    bankAccountNumber
                    status
                }
                adminRights
                createdAt
                deliverySites{
                    reference
                    segments
                    address{
                        street
                        houseNumber
                        houseNumberAddition
                        zipCode
                        city
                    }
                    addressHasMultipleSites
                    status
                    propositionType
                    deliveryStartDate
                    deliveryEndDate
                    firstMeterReadingDate
                    lastMeterReadingDate
                }
                smartCharging {
                    isActivated
                    provider
                    userCreatedAt
                    userId
                    isAvailableInCountry
                    needsSubscription
                    subscription {
                        startDate
                        endDate
                        id
                        proposition {
                            product
                            countryCode
                        }
                    }
                }
                websiteUrl
                customerSupportEmail
                email
                connections(siteReference: $siteReference) {
                    id
                    connectionId
                    EAN
                    segment
                    status
                    contractStatus
                    estimatedFeedIn
                    firstMeterReadingDate
                    lastMeterReadingDate
                    meterType
                    externalDetails {
                        gridOperator
                        address {
                            street
                            houseNumber
                            houseNumberAddition
                            zipCode
                            city
                        }
                    }
                }
                externalDetails {
                    reference
                    person {
                        firstName
                        lastName
                    }
                    contact {
                        emailAddress
                        phoneNumber
                        mobileNumber
                    }
                    address {
                        street
                        houseNumber
                        houseNumberAddition
                        zipCode
                        city
                    }
                    debtor {
                        bankAccountNumber
                        preferredAutomaticCollectionDay
                    }
                }
                firstName
                hasInviteLink
                id
                email
                countryCode
                lastLogin
                advancedPaymentAmount(siteReference: $siteReference)
                hasCO2Compensation
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
                notification
                reference
                role
                status
                treesCount
                updatedAt
                __typename
            }
            """,
            "Me",
            {"siteReference": site_reference},
        )

        return User.from_dict(await self._query(query))

    async def me(self, site_reference: str | None = None) -> Me:
        if self._auth is None:
            raise AuthRequiredException

        query = FrankEnergieQuery(
            """
            query Me($siteReference: String) {
                me {
                    ...UserFields
                }
            }
            fragment UserFields on User {
                id
                email
                countryCode
                advancedPaymentAmount(siteReference: $siteReference)
                treesCount
                hasInviteLink
                hasCO2Compensation
                deliverySites {
                    reference
                    segments
                    address {
                        street
                        houseNumber
                        houseNumberAddition
                        zipCode
                        city
                    }
                    addressHasMultipleSites
                    status
                    propositionType
                    deliveryStartDate
                    deliveryEndDate
                    firstMeterReadingDate
                    lastMeterReadingDate
                    __typename
                }
                __typename
            }
            """,
            "Me",
            {"siteReference": site_reference},
        )

        return Me.from_dict(await self._query(query))

    async def prices(
        self, start_date: Optional[date] | None = None, end_date: Optional[date] | None = None
    ) -> MarketPrices:
        """Get market prices."""
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today() + timedelta(days=1)

        query = FrankEnergieQuery(
            """
            query MarketPrices($startDate: Date!, $endDate: Date!) {
                marketPricesElectricity(startDate: $startDate, endDate: $endDate) {
                    from
                    till
                    marketPrice
                    marketPriceTax
                    sourcingMarkupPrice
                    energyTaxPrice
                    perUnit
                    __typename
                }
                marketPricesGas(startDate: $startDate, endDate: $endDate) {
                    from
                    till
                    marketPrice
                    marketPriceTax
                    sourcingMarkupPrice
                    energyTaxPrice
                    perUnit
                    __typename
                }
                version
                __typename
            }
            """,
            "MarketPrices",
            {"startDate": str(start_date), "endDate": str(end_date)},
        )
        response = await self._query(query)
        return MarketPrices.from_dict(response)

    async def user_prices(
        self,
        start_date: date,
        site_reference: str,
        end_date: Optional[date] | None = None
    ) -> MarketPrices:
        """Get customer market prices."""
        if self._auth is None:
            raise AuthRequiredException

        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today() + timedelta(days=1)

        query = FrankEnergieQuery(
            """
            query MarketPrices($date: String!, $siteReference: String!) {
                customerMarketPrices(date: $date, siteReference: $siteReference) {
                    id
                    electricityPrices {
                        id
                        date
                        from
                        till
                        marketPrice
                        marketPriceTax
                        sourcingMarkupPrice: consumptionSourcingMarkupPrice
                        energyTaxPrice: energyTax
                        perUnit
                        __typename
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
                        perUnit
                        __typename
                    }
                __typename
                }
            }
            """,
            "MarketPrices",
            {"date": str(start_date), "siteReference": site_reference},
        )

        return MarketPrices.from_userprices_dict(await self._query(query))

    async def smart_batteries(self) -> SmartBatteries:
        """Get the users smart batteries.

        Returns a list of all smart batteries.

        Full query:
        query SmartBatteries {
            smartBatteries {
                brand
                capacity
                createdAt
                externalReference
                id
                maxChargePower
                maxDischargePower
                provider
                updatedAt
                __typename
            }
        }
        """
        if self._auth is None:
            raise AuthRequiredException

        query = FrankEnergieQuery(
            """
            query SmartBatteries{
                smartBatteries{
                    brand
                    capacity
                    createdAt
                    externalReference
                    id
                    maxChargePower
                    maxDischargePower
                    provider
                    updatedAt
                    __typename
                }
            }
            """,
            "SmartBatteries",
        )

        response = await self._query(query)

        self._handle_errors(response)

        return SmartBatteries.from_dict(response["data"])

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if the client is authenticated, False otherwise.

        Does not actually check if the token is valid.
        """
        return self._auth is not None and self._auth.authToken is not None

    def authentication_valid(self) -> bool:
        """Return if client is authenticated.
        Does not actually check if the token is valid.
        """
        if self._auth is None:
            return False
        return self._auth.authTokenValid()

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

        response = requests.post(self.DATA_URL, json={
                                 'query': query}, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result

    def get_diagnostic_data(self):
        # Implement the logic to fetch diagnostic data from the FrankEnergie API
        # and return the data as needed for the diagnostic sensor
        return "Diagnostic data"


# frank_energie_instance = FrankEnergie()

# Call the introspect_schema method on the instance
# introspection_result = frank_energie_instance.introspect_schema()

# Print the result
# print("Introspection Result:", introspection_result)
