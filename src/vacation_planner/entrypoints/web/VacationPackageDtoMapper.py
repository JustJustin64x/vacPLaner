from __future__ import annotations

from typing import Any
from src.vacation_planner.core.domain.models.VacationPackage import VacationPackage


class VacationPackageDtoMapper:
    """
    Data Transfer Object (DTO) mapper responsible for transforming Core domain VacationPackage
    entities into JSON-serializable dictionaries for REST Web API responses.
    """

    def map_vacation_package_to_dto(self, package: VacationPackage) -> dict[str, Any]:
        """
        Converts a VacationPackage domain aggregate into a clean JSON dictionary.
        """
        return {
            "package_id": package.package_id,
            "origin": {
                "id": package.origin_location.location_id,
                "name": package.origin_location.name,
                "country": package.origin_location.country_name,
                "country_code": package.origin_location.country_code,
                "coordinates": {
                    "latitude": package.origin_location.coordinates.latitude,
                    "longitude": package.origin_location.coordinates.longitude,
                },
            },
            "destination": {
                "id": package.destination_location.location_id,
                "name": package.destination_location.name,
                "country": package.destination_location.country_name,
                "country_code": package.destination_location.country_code,
                "coordinates": {
                    "latitude": package.destination_location.coordinates.latitude,
                    "longitude": package.destination_location.coordinates.longitude,
                },
            },
            "date_range": {
                "start_date": package.date_range.start_date.isoformat(),
                "end_date": package.date_range.end_date.isoformat(),
                "total_nights": package.date_range.calculate_total_nights(),
                "duration_days": package.date_range.calculate_duration_in_days(),
            },
            "outbound_transport": {
                "transport_option_id": package.outbound_transport_option.transport_option_id,
                "transport_type": package.outbound_transport_option.transport_type.value,
                "departure_time": package.outbound_transport_option.departure_time.isoformat(),
                "arrival_time": package.outbound_transport_option.arrival_time.isoformat(),
                "total_duration_minutes": package.outbound_transport_option.calculate_total_duration_in_minutes(),
                "price": {
                    "amount": package.outbound_transport_option.total_price.to_float(),
                    "currency": package.outbound_transport_option.total_price.currency,
                },
                "carbon_dioxide_emission_kg": package.outbound_transport_option.carbon_dioxide_emission_in_kilograms,
                "transfers_count": package.outbound_transport_option.count_transfers(),
                "segments": [
                    {
                        "from": seg.departure_station_or_airport,
                        "to": seg.arrival_station_or_airport,
                        "departure_time": seg.departure_time.isoformat(),
                        "arrival_time": seg.arrival_time.isoformat(),
                        "duration_minutes": seg.duration_in_minutes,
                        "carrier": seg.carrier_or_operator_name,
                        "identifier": seg.segment_identifier,
                    }
                    for seg in package.outbound_transport_option.segments
                ],
            },
            "return_transport": {
                "transport_option_id": package.return_transport_option.transport_option_id,
                "transport_type": package.return_transport_option.transport_type.value,
                "departure_time": package.return_transport_option.departure_time.isoformat(),
                "arrival_time": package.return_transport_option.arrival_time.isoformat(),
                "total_duration_minutes": package.return_transport_option.calculate_total_duration_in_minutes(),
                "price": {
                    "amount": package.return_transport_option.total_price.to_float(),
                    "currency": package.return_transport_option.total_price.currency,
                },
                "carbon_dioxide_emission_kg": package.return_transport_option.carbon_dioxide_emission_in_kilograms,
                "transfers_count": package.return_transport_option.count_transfers(),
                "segments": [
                    {
                        "from": seg.departure_station_or_airport,
                        "to": seg.arrival_station_or_airport,
                        "departure_time": seg.departure_time.isoformat(),
                        "arrival_time": seg.arrival_time.isoformat(),
                        "duration_minutes": seg.duration_in_minutes,
                        "carrier": seg.carrier_or_operator_name,
                        "identifier": seg.segment_identifier,
                    }
                    for seg in package.return_transport_option.segments
                ],
            },
            "accommodation": {
                "accommodation_id": package.accommodation_option.accommodation_id,
                "name": package.accommodation_option.name,
                "type": package.accommodation_option.accommodation_type.value,
                "star_rating": package.accommodation_option.star_rating,
                "address": package.accommodation_option.address_line,
                "total_price": {
                    "amount": package.accommodation_option.total_price.to_float(),
                    "currency": package.accommodation_option.total_price.currency,
                },
                "price_per_night": {
                    "amount": package.accommodation_option.price_per_night.to_float(),
                    "currency": package.accommodation_option.price_per_night.currency,
                },
                "amenities": list(package.accommodation_option.included_amenities),
            },
            "recommended_attractions": [
                {
                    "attraction_id": attr.attraction_id,
                    "name": attr.name,
                    "category": attr.category,
                    "admission_fee": {
                        "amount": attr.admission_fee.to_float(),
                        "currency": attr.admission_fee.currency,
                    },
                    "estimated_duration_minutes": attr.estimated_visit_duration_in_minutes,
                    "user_rating": attr.user_rating,
                    "description": attr.description,
                }
                for attr in package.recommended_attractions
            ],
            "total_package_cost": {
                "amount": package.total_package_cost.to_float(),
                "currency": package.total_package_cost.currency,
            },
            "total_carbon_dioxide_emission_kg": package.calculate_total_carbon_dioxide_emission_in_kilograms(),
            "is_within_budget": package.is_within_budget,
            "validation_notes": list(package.validation_notes),
        }

