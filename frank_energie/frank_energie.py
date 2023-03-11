from __future__ import annotations
import asyncio
from typing import Any
from datetime import datetime, timedelta

from aiohttp.client import ClientError, ClientResponseError, ClientSession

from .models import Price, PriceData

class FrankEnergie:
    
    DATA_URL = "https://frank-graphql-prod.graphcdn.app/"
     
    def __init__(self, clientsession: ClientSession = None):
        self._session = clientsession
    
    async def prices(self, start_date : datetime, end_date : datetime | None = None) -> tuple(PriceData, PriceData):
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
            return (PriceData(data['data']['marketPricesElectricity'] if data['data'] else {}), PriceData(data['data']['marketPricesGas'] if data['data'] else {}))

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
