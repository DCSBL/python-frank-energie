from frank_energie import FrankEnergie, PriceData
from datetime import datetime, timedelta

import asyncio

async def main():
    
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    print(today)
    print(tomorrow)
    
    async with FrankEnergie() as fe:
        (electra_prices, gas_prices) = await fe.prices(today, tomorrow)
        
        for price in electra_prices.all:
            print(f"{price.date_from} -> {price.date_till}: {price.total}")
            
        for price in gas_prices.all:
            print(f"{price.date_from} -> {price.date_till}: {price.total}")
    
asyncio.run(main())
