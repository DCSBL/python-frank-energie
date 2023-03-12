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


asyncio.run(main())
