"""FrankEnergie API implementation."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

from aiohttp.client import ClientError, ClientSession

from .exceptions import AuthException, AuthRequiredException
from .models import (
    Authentication,
    Invoices,
    MarketPrices,
    Me,
    MonthSummary,
    SmartBatteries,
    SmartBatterySessions,
)


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
                headers=(
                    {"Authorization": f"Bearer {self._auth.authToken}"}
                    if self._auth is not None
                    else None
                ),
            )

            response = await resp.json()

        except (asyncio.TimeoutError, ClientError, KeyError) as error:
            raise ValueError(f"Request failed: {error}") from error

        # Catch common error messages and raise a more specific exception
        if errors := response.get("errors"):
            for error in errors:
                if error["message"] == "user-error:auth-not-authorised":
                    raise AuthException

        return response

    async def login(self, username: str, password: str) -> Authentication:
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

    async def renew_token(self) -> Authentication:
        """Renew the authentication token."""
        if self._auth is None:
            raise AuthRequiredException

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

    async def month_summary(self, site_reference: str) -> MonthSummary:
        """Get month summary data.

        Returns a MonthSummary object, containing the actual and expected costs until the last meter reading date.

        Full query:
        query MonthSummary($siteReference: String!) {
            monthSummary(siteReference: $siteReference) {
                _id
                lastMeterReadingDate
                expectedCostsUntilLastMeterReadingDate
                actualCostsUntilLastMeterReadingDate
                meterReadingDayCompleteness
                gasExcluded
            }
        }
        """
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
                query MonthSummary($siteReference: String!) {
                    monthSummary(siteReference: $siteReference) {
                        actualCostsUntilLastMeterReadingDate
                        expectedCostsUntilLastMeterReadingDate
                        expectedCosts
                        lastMeterReadingDate
                    }
                }
            """,
            "operationName": "MonthSummary",
            "variables": {"siteReference": site_reference},
        }

        return MonthSummary.from_dict(await self._query(query))

    async def invoices(self, site_reference: str) -> Invoices:
        """Get invoices data.

        Returns a Invoices object, containing the previous, current and upcoming invoice.

        Full query:
        query Invoices($siteReference: String!) {
            invoices(siteReference: $siteReference) {
                _id
                previousPeriodInvoice {
                id
                StartDate
                PeriodDescription
                TotalAmount
                __typename
                }
                currentPeriodInvoice {
                id
                StartDate
                PeriodDescription
                TotalAmount
                __typename
                }
                upcomingPeriodInvoice {
                id
                StartDate
                PeriodDescription
                TotalAmount
                __typename
                }
                allInvoices {
                id
                StartDate
                PeriodDescription
                TotalAmount
                __typename
                }
                __typename
            }
        }

        """
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
                query Invoices($siteReference: String!) {
                    invoices(siteReference: $siteReference) {
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
            "variables": {"siteReference": site_reference},
        }

        return Invoices.from_dict(await self._query(query))

    async def me(self, site_reference: str | None = None) -> Me:
        """Get 'Me' data.

        Full query:
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
            notification
            createdAt
            InviteLinkUser {
                id
                fromName
                slug
                treesAmountPerConnection
                discountPerConnection
            }
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
            PushNotificationPriceAlerts {
                id
                isEnabled
                type
                weekdays
            }
            UserSettings {
                id
                disabledHapticFeedback
                jedlixUserId
                jedlixPushNotifications
                smartPushNotifications
            }
            activePaymentAuthorization {
                id
                mandateId
                signedAt
                bankAccountNumber
            }
            meterReadingExportPeriods(siteReference: $siteReference) {
                EAN
                cluster
                segment
                from
                till
                period
                type
            }
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
            }

        """
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
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
                        status
                    }
                }
            """,
            "operationName": "Me",
            "variables": {"siteReference": site_reference},
        }

        return Me.from_dict(await self._query(query))

    async def prices(
        self, start_date: date, end_date: date | None = None
    ) -> MarketPrices:
        """Get market prices."""
        query_data = {
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

        return MarketPrices.from_dict(await self._query(query_data))

    async def user_prices(self, start_date: date, site_reference: str) -> MarketPrices:
        """Get customer market prices.

        Full query:
        query MarketPrices($date: String!, $siteReference: String!) {
            customerMarketPrices(date: $date, siteReference: $siteReference) {
                id
                electricityPrices {
                    id
                    from
                    till
                    date
                    marketPrice
                    marketPriceTax
                    consumptionSourcingMarkupPrice
                    energyTax
                    perUnit
                }
                gasPrices {
                    id
                    from
                    till
                    date
                    marketPrice
                    marketPriceTax
                    consumptionSourcingMarkupPrice
                    energyTax
                    perUnit
                }
            }
        }
        """
        if self._auth is None:
            raise AuthRequiredException

        query_data = {
            "query": """
                query MarketPrices($date: String!, $siteReference: String!) {
                    customerMarketPrices(date: $date, siteReference: $siteReference) {
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
            "variables": {"date": str(start_date), "siteReference": site_reference},
            "operationName": "MarketPrices",
        }

        return MarketPrices.from_userprices_dict(await self._query(query_data))

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
            }
        }
        """
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
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
                   }
              }
            """,
            "operationName": "SmartBatteries",
        }

        return SmartBatteries.from_dict(await self._query(query))

    async def smart_battery_sessions(
        self, device_id: str, start_date: date, end_date: date
    ) -> SmartBatterySessions:
        """List smart battery sessions for a device.

        Returns a list of all smart battery sessions for a device.

        Full query:
        query SmartBatterySessions($startDate: String!, $endDate: String!, $deviceId: String!) {
            smartBatterySessions(
                startDate: $startDate
                endDate: $endDate
                deviceId: $deviceId
          ) {
            deviceId
            periodEndDate
            periodStartDate
            periodTradingResult
            sessions {
              cumulativeTradingResult
              date
              tradingResult
            }
            totalTradingResult
          }
        }
        """
        if self._auth is None:
            raise AuthRequiredException

        query = {
            "query": """
                query SmartBatterySessions($startDate: String!, $endDate: String!, $deviceId: String!) {
                      smartBatterySessions(
                        startDate: $startDate
                        endDate: $endDate
                        deviceId: $deviceId
                      ) {
                        deviceId
                        periodEndDate
                        periodStartDate
                        periodTradingResult
                        sessions {
                          cumulativeTradingResult
                          date
                          tradingResult
                        }
                        totalTradingResult
                      }
                    }
                """,
            "operationName": "SmartBatterySessions",
            "variables": {
                "deviceId": device_id,
                "startDate": str(start_date),
                "endDate": str(end_date),
            },
        }

        return SmartBatterySessions.from_dict(await self._query(query))

    @property
    def is_authenticated(self) -> bool:
        """Return if client is authenticated.

        Does not actually check if the token is valid.
        """
        return self._auth is not None

    def authentication_valid(self) -> bool:
        """Return if client is authenticated.

        Does not actually check if the token is valid.
        """
        if self._auth is None:
            return False
        return self._auth.authTokenValid()

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
