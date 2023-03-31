from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from dateutil import parser

from .exceptions import AuthException


@dataclass
class Authentication:

    authToken: str
    refreshToken: str

    @staticmethod
    def from_dict(data: dict[str, str]) -> Authentication:

        if errors := data.get("errors"):
            raise AuthException(errors[0]["message"])

        payload = data.get("data").get("login")
        if payload is None:
            raise AuthException("Unexpected response")

        return Authentication(
            authToken=payload.get("authToken"),
            refreshToken=payload.get("refreshToken"),
        )


@dataclass
class User:
    connectionsStatus: str
    firstMeterReadingDate: str
    lastMeterReadingDate: str
    advancedPaymentAmount: float
    hasCO2Compensation: bool

    @staticmethod
    def from_dict(data: dict[str, str]) -> Authentication:

        if errors := data.get("errors"):
            raise AuthException(errors[0]["message"])

        payload = data.get("data").get("me")
        if payload is None:
            raise AuthException("Unexpected response")

        return User(
            connectionsStatus=payload.get("connectionsStatus"),
            firstMeterReadingDate=payload.get("firstMeterReadingDate"),
            lastMeterReadingDate=payload.get("lastMeterReadingDate"),
            advancedPaymentAmount=payload.get("advancedPaymentAmount"),
            hasCO2Compensation=payload.get("hasCO2Compensation"),
        )


@dataclass
class MonthSummary:
    actualCostsUntilLastMeterReadingDate: float
    expectedCostsUntilLastMeterReadingDate: float
    lastMeterReadingDate: str

    @staticmethod
    def from_dict(data: dict[str, str]) -> Authentication:

        if errors := data.get("errors"):
            raise AuthException(errors[0]["message"])

        payload = data.get("data").get("monthSummary")
        if payload is None:
            raise AuthException("Unexpected response")

        return MonthSummary(
            actualCostsUntilLastMeterReadingDate=payload.get(
                "actualCostsUntilLastMeterReadingDate"
            ),
            expectedCostsUntilLastMeterReadingDate=payload.get(
                "expectedCostsUntilLastMeterReadingDate"
            ),
            lastMeterReadingDate=payload.get("lastMeterReadingDate"),
        )


class Price:
    """Price data for one hour."""

    date_from: datetime
    date_till: datetime
    market_price: float
    market_price_tax: float
    sourcing_markup_rice: float
    energy_tax_price: float

    def __init__(self, data: dict) -> None:
        self.date_from = parser.parse(data["from"])
        self.date_till = parser.parse(data["till"])

        self.market_price = data["marketPrice"]
        self.market_price_tax = data["marketPriceTax"]
        self.sourcing_markup_price = data["sourcingMarkupPrice"]
        self.energy_tax_price = data["energyTaxPrice"]

    def __str__(self) -> str:
        return f"{self.date_from} -> {self.date_till}: {self.total}"

    @property
    def for_now(self) -> bool:
        """Whether this price entry is for the current hour."""
        return self.date_from <= datetime.now(timezone.utc) < self.date_till

    @property
    def for_future(self) -> bool:
        """Whether this price entry is for and hour after the current one."""
        return self.date_from.hour > datetime.now(timezone.utc).hour

    @property
    def for_today(self) -> bool:
        """Whether this price entry is for the current day."""
        day_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)
        return self.date_from >= day_start and self.date_till <= day_end

    @property
    def market_price_with_tax(self) -> float:
        return round(self.market_price + self.market_price_tax, 4)

    @property
    def total(self) -> float:
        return round(
            self.market_price
            + self.market_price_tax
            + self.sourcing_markup_price
            + self.energy_tax_price,
            4,
        )


class PriceData:
    price_data: list[Price] = []

    def __init__(self, price_data: list[dict] | None = None) -> None:
        if price_data is not None:
            self.price_data = [Price(price) for price in price_data]

    def __add__(self, b: PriceData) -> PriceData:
        pd = PriceData()
        pd.price_data = self.price_data + b.price_data
        return pd

    @property
    def all(self) -> list[Price]:
        return self.price_data

    @property
    def today(self) -> list[Price]:
        return [hour for hour in self.price_data if hour.for_today]

    @property
    def current_hour(self) -> Price:
        """Price that's currently applicable."""
        return [hour for hour in self.price_data if hour.for_now][0]

    @property
    def today_min(self) -> Price:
        return min([hour for hour in self.today], key=lambda hour: hour.total)

    @property
    def today_max(self) -> Price:
        return max([hour for hour in self.today], key=lambda hour: hour.total)

    @property
    def today_avg(self) -> float:
        return round(sum(hour.total for hour in self.today) / len(self.today), 5)

    def get_future_prices(self) -> list[Price]:
        """Prices for hours after the current one."""
        return [hour for hour in self.price_data if hour.for_future]

    def asdict(self, attr) -> dict:
        """Return a dict that can be used as entity attribute data."""
        return [
            {"from": e.date_from, "till": e.date_till, "price": getattr(e, attr)}
            for e in self.price_data
        ]
