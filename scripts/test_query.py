from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timedelta

from python_frank_energie import FrankEnergie

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Filename: test_query.py


_LOGGER = logging.getLogger(__name__)


async def execute_query():
    """
    Executes a market prices query for electricity and gas.
    
    Calculates the current date and the following day to define a one-day query window, then uses a FrankEnergie client to asynchronously fetch market prices. The function prints electricity and gas price details if available. It returns 0 on success, 1 when no market prices or both price lists are missing, and 2 if an exception occurs. In all cases, it ensures the client session is closed.
    """
    current_date = datetime.now().date()
    tomorrow = current_date + timedelta(days=1)
    start_date = current_date
    end_date = tomorrow

    try:
        frank_energie = FrankEnergie()
        print("Testing public prices query")
        market_prices = await frank_energie.prices(start_date, end_date)

        if not market_prices:
            print("No market prices available.", file=sys.stderr)
            return 1  # Exit code 1 indicates failure

        # Access electricity and gas prices
        electricity_prices = market_prices.electricity
        gas_prices = market_prices.gas

        # Handle cases where prices might be empty or missing
        if not electricity_prices and not gas_prices:
            print("No prices available", file=sys.stderr)
            return 1

        # Print electricity prices
        print("Electricity Prices:")
        for price in electricity_prices.all:
            print(f"From: {price.date_from}, Till: {price.date_till}, Market Price: {price.market_price}, Total: {price.total}")

        # Print gas prices
        print("Gas Prices:")
        for price in gas_prices.all:
            print(f"From: {price.date_from}, Till: {price.date_till}, Market Price: {price.market_price}, Total: {price.total}")

        return 0  # Exit code 0 means success

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2  # Custom error code for exceptions
    finally:
        await frank_energie.close()  # Close the client session when done


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    exit_code = loop.run_until_complete(execute_query())
    sys.exit(exit_code)
