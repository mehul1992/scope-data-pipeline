from __future__ import annotations

from typing import Any

from app.etl.transformers.dimension_transformer import DimensionTransformer
from app.etl.transformers.company_transformer import CompanyTransformer




class TransformOperator:

    def __init__(self, validated_payload: dict[str, Any], upload_id: str) -> None:
        self.validated_payload = validated_payload
        self.upload_id = upload_id

    def execute(self) -> dict[str, Any]:
        
        dimension_transformer = DimensionTransformer()
        country  = dimension_transformer.transform_country(self.validated_payload.get("parsed_payload").get("country"))
        currency = dimension_transformer.transform_currency(self.validated_payload.get("parsed_payload").get("currency"))
        dates    = dimension_transformer.transform_date_dimension(
            self.validated_payload.get("parsed_payload").get("credit_metrics", {}).get("years", [])
        )
        company_transformer = CompanyTransformer()
        company = company_transformer.transform(self.validated_payload.get("parsed_payload").get("rated_entity"), self.upload_id)
        return {
            "upload_id": self.upload_id,
            "validated_payload": self.validated_payload.get("parsed_payload"),
            "country_transformed": country,
            "currency_transformed": currency,
            "dates_transformed": dates,
            "company_transformed": company,
        }
