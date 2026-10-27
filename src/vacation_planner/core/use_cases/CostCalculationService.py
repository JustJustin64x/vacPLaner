from src.vacation_planner.core.domain.models.AccommodationOption import AccommodationOption
from src.vacation_planner.core.domain.models.TransportOption import TransportOption
from src.vacation_planner.core.domain.value_objects.MonetaryAmount import MonetaryAmount


class CostCalculationService:
    """
    Domain service responsible for calculating the aggregate financial cost of a vacation package
    and verifying whether the aggregated total adheres to the user's budget constraints.
    """

    def calculate_total_package_cost(
        self,
        outbound_transport: TransportOption,
        return_transport: TransportOption,
        accommodation: AccommodationOption,
    ) -> MonetaryAmount:
        """
        Sums up the outbound transport, return transport, and accommodation total costs.
        Ensures all components are denominated in identical currencies.
        """
        total = outbound_transport.total_price
        total = total.add(return_transport.total_price)
        total = total.add(accommodation.total_price)
        return total

    def evaluate_budget_compliance(
        self, total_cost: MonetaryAmount, maximum_budget: MonetaryAmount
    ) -> tuple[bool, str]:
        """
        Compares total cost against the maximum allowed budget.
        Returns a tuple of (is_compliant, explanation_message).
        """
        if total_cost.is_less_than_or_equal_to(maximum_budget):
            remaining_budget = maximum_budget.subtract(total_cost)
            return (
                True,
                f"Package is within budget. Remaining balance: {remaining_budget}.",
            )
        else:
            budget_overrun = total_cost.subtract(maximum_budget)
            return (
                False,
                f"Package exceeds maximum budget by {budget_overrun}.",
            )

