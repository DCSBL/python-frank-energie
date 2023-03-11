from __future__ import annotations
import asyncio
import logging
import string
from http import HTTPStatus
from typing import Any, cast
from datetime import datetime, timedelta

import async_timeout
from aiohttp.client import ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_DELETE, METH_GET, METH_PUT


class FrankEnergie:
    
    DATA_URL = "https://frank-graphql-prod.graphcdn.app/"
     
    def __init__(self, clientsession: ClientSession = None):
        self._session = clientsession
    
    async def prices(self, start_date : datetime, end_date : datetime | None = None) -> dict:
        """Request to API"""
        if self._session is None:
            self._session = ClientSession()
            self._close_session = True
        
        query_data = {
            "query": """
                query MarketPrices($startDate: Date!, $endDate: Date!) {
                     marketPricesElectricity(startDate: $startDate, endDate: $endDate) {
                        from till marketPrice marketPriceTax sourcingMarkupPrice energyTaxPrice
                     }
                     marketPricesGas(startDate: $startDate, endDate: $endDate) {
                        from till marketPrice marketPriceTax sourcingMarkupPrice energyTaxPrice
                     }
                }
            """,
            "variables": {"startDate": str(start_date), "endDate": str(end_date)},
            "operationName": "MarketPrices"
        }
        
        try:
            resp = await self._session.post(self.DATA_URL, json=query_data)

            data = await resp.json()
            return data['data'] if data['data'] else {}

        except (asyncio.TimeoutError, ClientError, KeyError) as error:
            raise ValueError(f"Fetching energy data for period {start_date} - {end_date} failed: {error}") from error
    
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

async def main():
    
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    async with FrankEnergie() as fe:
        prices = await fe.prices(today, tomorrow)
    
    print(prices)
    
asyncio.run(main())
