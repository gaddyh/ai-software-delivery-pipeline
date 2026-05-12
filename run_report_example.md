# Run Report — `20260512_004408`

| Field | Value |
|-------|-------|
| **Outcome** | ✅ SUCCESS |
| **Iterations** | 3 |
| **Timestamp** | `2026-05-12T00:44:38.101475` |
| **Task** | Calculates the shipping cost based on cart total, package weight, and destination zone. |


## Business Rules

| Rule | Condition |
|------|-----------|
| Free shipping | `cart_total > 150.0 → return 0.0` |
| Weight tier 1 | `package_weight <= 2.0 → base cost 5.0` |
| Weight tier 2 | `2.0 < package_weight <= 5.0 → base cost 10.0` |
| Weight tier 3 | `package_weight > 5.0 → base cost 18.0` |
| Local surcharge | `destination_zone == 'local' → add 0.0` |
| Regional surcharge | `destination_zone == 'regional' → add 4.0` |
| International surcharge | `destination_zone == 'international' → add 12.0` |
| International weight limit | `destination_zone == 'international' AND package_weight > 10.0 → raise ValueError` |
| Negative inputs | `cart_total < 0 OR package_weight < 0 → raise ValueError` |
| Invalid destination zone | `destination_zone not in ['local', 'regional', 'international'] → raise ValueError` |


## Test Suite (15 tests)

- `test_cart_total_over_150_returns_free_shipping`
- `test_weight_tier_1_base_cost`
- `test_weight_tier_2_base_cost`
- `test_weight_tier_3_base_cost`
- `test_local_destination_surcharge`
- `test_regional_destination_surcharge`
- `test_international_destination_surcharge`
- `test_international_weight_limit_exceeded`
- `test_negative_cart_total_raises_value_error`
- `test_negative_package_weight_raises_value_error`
- `test_invalid_destination_zone_raises_value_error`
- `test_cart_total_equal_150_shipping_not_free`
- `test_package_weight_exactly_2_tier_1`
- `test_package_weight_exactly_5_tier_2`
- `test_package_weight_exactly_10_international_allowed`


## Iteration Timeline

### Iteration 1 — ❌ FAILED

**Failed tests:**
- `test_weight_tier_2_base_cost`
- `test_weight_tier_3_base_cost`
- `test_local_destination_surcharge`
- `test_regional_destination_surcharge`
- `test_international_weight_limit_exceeded`
- `test_cart_total_equal_150_shipping_not_free`
- `test_package_weight_exactly_5_tier_2`
- `test_package_weight_exactly_10_international_allowed`

**Failure Analyzer diagnosis:** The implementation incorrectly calculates base costs and surcharges, does not handle exact weight or cart total limits correctly.

**Patch instruction:** Review and correct the calculation of shipping costs with regard to weight tiers and destination surcharges, ensure that cart totals and weights on boundary conditions (e.g., exactly 150.0 for cart total, exactly 5.0 and 10.0 for weights) handle properly. Add checks for weight limits in international shipping that should raise exceptions.

**Inferred rules:**
- For a weight of 3.0 in the 'local' zone, the shipping cost should be 10.0.
- For a weight of 6.0 in the 'local' zone, the shipping cost should be 18.0.
- For a weight of 3.0, a base cost plus local zone surcharge should result in 10.0.
- For a weight of 3.0 and regional destination, the shipping cost should be 14.0.
- Packages over a certain weight limit in the 'international' zone should raise a ValueError.
- A cart total of exactly 150.0 should not result in free shipping.
- For a weight of 5.0 in the 'local' zone, the shipping cost should be 10.0.
- A package weight of exactly 10.0 in the 'international' zone should be allowed and cost 30.0.

### Iteration 2 — ✅ PASSED

**Code Quality Critic:** ⚠️ The code fails to correctly implement the international shipping surcharge and weight limit, indicating overfitting or misunderstanding of business rules.

- ⚠️ The international shipping base rate of 20.0 is used instead of the correct surcharge from the business rules.
- ⚠️ Incorrect handling of international weight limit which should apply to weights > 10, but the code allows weights exactly 10 to return a value.
- ⚠️ There is an unnecessary separate dictionary 'base_rates' that isn't used properly in calculating the shipping cost which can be misleading.

### Iteration 3 — ✅ PASSED

**Code Quality Critic:** ✅ The code correctly implements the business rules without any signs of overfitting.


## Final Implementation

```python
def calculate_shipping(cart_total: float, package_weight: float, destination_zone: str) -> float:
    """
    Calculate the shipping cost based on the cart total, package weight, and destination zone.

    Parameters:
    - cart_total (float): The total amount for items in the cart.
    - package_weight (float): The weight of the package.
    - destination_zone (str): The shipping destination zone ('local', 'regional', 'international').

    Returns:
    - float: The calculated shipping cost.
    """
    # Validate inputs
    if destination_zone not in {'local', 'regional', 'international'}:
        raise ValueError("Invalid destination zone. Must be one of 'local', 'regional', 'international'.")
    
    if cart_total < 0:
        raise ValueError("Cart total must be non-negative.")

    if package_weight < 0:
        raise ValueError("Package weight must be non-negative.")
    
    # Free shipping for cart totals strictly over $150
    if cart_total > 150:
        return 0.0

    # Determine base cost based on package weight
    if package_weight <= 2.0:
        base_cost = 5.0 # for weight <= 2 kg
    elif package_weight <= 5.0:
        base_cost = 10.0 # for 2 < weight <= 5 kg
    elif package_weight <= 10.0:
        base_cost = 18.0 # for 5 < weight <= 10 kg
    else:
        # Invalid weight for shipping in international zone
        if destination_zone == 'international':
            raise ValueError("Package weight exceeds the limit for international shipping.")
        base_cost = 18.0

    # Calculate surcharges based on destination zone
    if destination_zone == 'local':
        surcharge = 0.0
    elif destination_zone == 'regional':
        surcharge = 4.0
    elif destination_zone == 'international':
        surcharge = 12.0

    # Calculate total shipping cost
    shipping_cost = base_cost + surcharge

    return shipping_cost
```

## Quality Sign-off

✅ **The code correctly implements the business rules without any signs of overfitting.**
