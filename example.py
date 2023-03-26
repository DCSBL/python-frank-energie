import asyncio
from datetime import datetime, timedelta

from python_frank_energie import FrankEnergie


async def main():
    """Fetch and print data from Frank energie."""
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    async with FrankEnergie() as fe:

        (prices_today_electricity, prices_today_gas) = await fe.prices(today, tomorrow)
        (prices_tomorrow_electricity, prices_tomorrow_gas) = await fe.prices(
            tomorrow, day_after_tomorrow
        )

        for price in (prices_today_electricity + prices_tomorrow_electricity).all:
            print(f"{price.date_from} -> {price.date_till}: {price.total}")

        for price in (prices_today_gas + prices_tomorrow_gas).all:
            print(f"{price.date_from} -> {price.date_till}: {price.total}")

    async with FrankEnergie() as fe:
        authToken = await fe.login("USERNAME", "PASSWORD")
        print(await fe.monthSummary())

    async with FrankEnergie(auth_token=authToken) as fe:
        print(await fe.monthSummary())
        print(await fe.user())


asyncio.run(main())
