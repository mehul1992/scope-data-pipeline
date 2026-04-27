"""
Dimension transformer.

Maps raw country and currency strings from parsed data
into DimCountry and DimCurrency lookup records.

Handles upsert logic — creates dimension record if not exists,
returns existing record if already present.
"""
from __future__ import annotations

from typing import Any

import logging

logger = logging.getLogger(__name__)

# ISO mapping for countries seen in real data
COUNTRY_ISO_MAP: dict[str, dict[str, str]] = {
    "Federal Republic of Germany": {
        "iso_alpha2": "DE",
        "iso_alpha3": "DEU",
        "region": "Western Europe",
    },
    "Switzerland": {
        "iso_alpha2": "CH",
        "iso_alpha3": "CHE",
        "region": "Western Europe",
    },
    "France": {
        "iso_alpha2": "FR",
        "iso_alpha3": "FRA",
        "region": "Western Europe",
    },
    "United Kingdom": {
        "iso_alpha2": "GB",
        "iso_alpha3": "GBR",
        "region": "Northern Europe",
    },
    "United States": {
        "iso_alpha2": "US",
        "iso_alpha3": "USA",
        "region": "North America",
    },
}

# Currency metadata for known currencies
CURRENCY_META_MAP: dict[str, dict[str, str]] = {
    "EUR": {"currency_name": "Euro", "symbol": "€"},
    "CHF": {"currency_name": "Swiss Franc", "symbol": "CHF"},
    "USD": {"currency_name": "US Dollar", "symbol": "$"},
    "GBP": {"currency_name": "British Pound", "symbol": "£"},
}


class DimensionTransformer:
    """
    Transforms raw country and currency strings into
    dimension table payloads ready for upsert.
    """

    def transform_country(
        self, country_name: str | None
    ) -> dict[str, Any] | None:
        """
        Transform a raw country string into a DimCountry payload.

        Returns None if country_name is missing.
        Enriches with ISO codes and region if known.
        Unknown countries stored with name only.
        """
        if not country_name:
            return None

        iso_data = COUNTRY_ISO_MAP.get(country_name, {})

        payload = {
            "country_name": country_name,
            "iso_alpha2": iso_data.get("iso_alpha2"),
            "iso_alpha3": iso_data.get("iso_alpha3"),
            "region": iso_data.get("region"),
        }

        logger.debug(
            "country dimension transformed country=%s iso_alpha2=%s",
            country=country_name,
            iso_alpha2=payload["iso_alpha2"],
        )

        return payload

    def transform_currency(
        self, currency_code: str | None
    ) -> dict[str, Any] | None:
        """
        Transform a raw currency code into a DimCurrency payload.

        Returns None if currency_code is missing.
        Enriches with name and symbol if known.
        """
        if not currency_code:
            return None

        meta = CURRENCY_META_MAP.get(currency_code.upper(), {})

        payload = {
            "currency_code": currency_code.upper(),
            "currency_name": meta.get("currency_name"),
            "symbol": meta.get("symbol"),
        }

        logger.debug(
            "currency dimension transformed currency_code=%s currency_name=%s symbol=%s",
            currency=currency_code,
            currency_name=payload["currency_name"],
            symbol=payload["symbol"],
            currency_code=currency_code,
        )

        return payload

    def transform_date_dimension(
        self, years: list[str]
    ) -> list[dict[str, Any]]:
        """
        Transform year headers from credit_metrics into DimDate payloads.

        Handles both actual years (2018, 2019...) and
        estimate years (2025E, 2026E, 2027E).
        """
        payloads = []
        for sort_order, year_value in enumerate(years):
            is_estimate = str(year_value).endswith("E")
            calendar_year = None

            if not is_estimate:
                try:
                    calendar_year = int(year_value)
                except (ValueError, TypeError):
                    pass

            payloads.append({
                "year_value": str(year_value),
                "calendar_year": calendar_year,
                "is_estimate": is_estimate,
                "sort_order": sort_order,
            })

        return payloads