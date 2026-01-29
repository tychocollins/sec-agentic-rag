class FinancialTools:
    def percentage_change(self, start_value: float, end_value: float) -> float:
        """
        Calculates the percentage change from start_value to end_value.
        Formula: ((end_value - start_value) / start_value) * 100
        """
        if start_value == 0:
            return 0.0
        return ((end_value - start_value) / start_value) * 100

    def margin(self, revenue: float, cost: float) -> float:
        """
        Calculates the profit margin percentage.
        Formula: ((revenue - cost) / revenue) * 100
        """
        if revenue == 0:
            return 0.0
        return ((revenue - cost) / revenue) * 100

    def ratio(self, numerator: float, denominator: float) -> float:
        """
        Calculates a simple ratio (numerator / denominator).
        """
        if denominator == 0:
            return 0.0
        return numerator / denominator
