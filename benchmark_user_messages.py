# MVP 1 Benchmark User Messages
# A progressive list of user messages for testing the AI Software Delivery Pipeline.

benchmark_user_messages = [
    # Level 1 — Simple function, clear rules
    (
        "I need a small Python function called apply_discount. "
        "It should take price: float and discount_percent: float and return the discounted price as a float. "
        "If price is negative, raise ValueError. "
        "If discount_percent is negative or greater than 100, raise ValueError. "
        "A discount of 0 should return the original price. "
        "A discount of 100 should return 0.0. "
        "Round the result to 2 decimal places."
    ),
    
    # Level 2 — Function with precedence rules
    (
        "Build a Python function called calculate_ticket_price for an event checkout. "
        "It should take base_price: float, age: int, is_student: bool, and is_vip: bool. "
        "Start with the base price. Children under 12 get 50 percent off. "
        "Students get 20 percent off. VIP tickets add a fixed 30 dollar fee after discounts. "
        "If someone is both a child and a student, apply only the child discount, not both. "
        "If base_price is negative or age is negative, raise ValueError. "
        "Return the final price as a float rounded to 2 decimal places."
    ),
    
    # Level 3 — Class with simple state
    (
        "I need a BankAccount class for a tiny banking demo. "
        "It should let me deposit money, withdraw money, and check the current balance. "
        "Use these public methods: deposit(amount: float) -> None, withdraw(amount: float) -> None, "
        "and get_balance() -> float. "
        "The account starts with balance 0.0. "
        "Depositing a positive amount increases the balance. "
        "Withdrawing a positive amount decreases the balance. "
        "If the withdrawal amount is greater than the current balance, raise ValueError. "
        "If deposit or withdraw gets a negative amount or zero, raise ValueError. "
        "Returned balances should be floats rounded to 2 decimal places."
    ),
    
    # Level 4 — Class with item state and partial operations
    (
        "Create an Inventory class for a small store. "
        "It should support add_stock(product_name: str, quantity: int) -> None, "
        "remove_stock(product_name: str, quantity: int) -> None, "
        "get_quantity(product_name: str) -> int, and is_in_stock(product_name: str) -> bool. "
        "Adding stock should increase the quantity for that product. "
        "Removing stock should decrease the quantity. "
        "If remove_stock asks to remove more than available, raise ValueError. "
        "If the product does not exist, get_quantity should return 0 and is_in_stock should return False. "
        "If quantity is negative or zero for add_stock or remove_stock, raise ValueError. "
        "When quantity reaches 0, the product should be considered out of stock."
    ),
    
    # Level 5 — Function with overlapping rules and caps
    (
        "I need a Python function called calculate_refund. "
        "It should take order_total: float, days_since_purchase: int, is_member: bool, and item_condition: str. "
        "Valid item_condition values are 'new', 'used', and 'damaged'. "
        "If days_since_purchase is more than 30, return 0.0. "
        "If item_condition is 'damaged', return 0.0. "
        "For 'new' items, refund 100 percent of order_total. "
        "For 'used' items, refund 50 percent of order_total. "
        "Members get an extra 10 percent refund bonus, but the final refund can never exceed the original order_total. "
        "If order_total is negative or days_since_purchase is negative, raise ValueError. "
        "If item_condition is invalid, raise ValueError. "
        "Return the refund as a float rounded to 2 decimal places."
    ),
    
    # Level 6 — Class with multiple operations and derived totals
    (
        "Build a GradeBook class for a teacher demo. "
        "It should support add_student(name: str) -> None, add_grade(name: str, grade: float) -> None, "
        "get_average(name: str) -> float, get_class_average() -> float, and has_student(name: str) -> bool. "
        "Adding a student creates the student with no grades. "
        "Adding the same student twice should do nothing and not raise an error. "
        "Grades must be between 0 and 100 inclusive, otherwise raise ValueError. "
        "Adding a grade for a student that does not exist should raise ValueError. "
        "get_average for a student with no grades should return 0.0. "
        "get_average for a missing student should raise ValueError. "
        "get_class_average should average all grades across all students. "
        "If there are no grades in the class, get_class_average should return 0.0. "
        "Return averages rounded to 2 decimal places."
    ),
    
    # Level 7 — Harder class: lifecycle/status logic
    (
        "Create a TaskTracker class for a small productivity app. "
        "It should support add_task(title: str, priority: int = 3) -> None, "
        "complete_task(title: str) -> None, reopen_task(title: str) -> None, "
        "get_status(title: str) -> str, get_open_tasks() -> list[str], and get_completed_tasks() -> list[str]. "
        "New tasks start with status 'open'. "
        "Priority must be between 1 and 5 inclusive, otherwise raise ValueError. "
        "Adding a task with an existing title should raise ValueError. "
        "Completing an open task changes status to 'completed'. "
        "Completing an already completed task should do nothing. "
        "Reopening a completed task changes status back to 'open'. "
        "Reopening an already open task should do nothing. "
        "Any operation on a missing task should raise ValueError, except get_open_tasks and get_completed_tasks. "
        "get_open_tasks should return open task titles sorted by priority ascending, then title alphabetically. "
        "get_completed_tasks should return completed task titles alphabetically."
    ),
    
    # Level 8 — Very hard for MVP 1: date-like rule without real dates
    (
        "I need a Subscription class for a SaaS billing demo. "
        "Use integer days instead of real dates. "
        "It should support start(plan: str, start_day: int) -> None, cancel(cancel_day: int) -> None, "
        "is_active(day: int) -> bool, get_plan() -> str, and get_bill_amount(day: int) -> float. "
        "Valid plans are 'basic' and 'pro'. Basic costs 10.0 per 30-day period. Pro costs 25.0 per 30-day period. "
        "A subscription is active from start_day until canceled. "
        "Canceling before start_day should raise ValueError. "
        "Calling cancel before start should raise ValueError. "
        "Calling start twice should raise ValueError. "
        "Invalid plan should raise ValueError. "
        "Negative days should raise ValueError. "
        "get_bill_amount(day) should return 0.0 if the subscription is not active on that day. "
        "If active, it should return the plan price. "
        "Return bill amounts rounded to 2 decimal places."
    ),
]

# Harder MVP 1 Benchmark User Messages
# These are still one-artifact tasks: one function or one class in solution.py.
# They are designed to stress TaskSpec quality, tester grounding, refinement, and critic behavior.

harder_benchmark_user_messages = [
    # Level 1 — Function with rule ordering, caps, and invalid states
    (
        "I need a function called calculate_coupon_discount for checkout. "
        "It takes cart_total: float, coupon_code: str, is_first_order: bool, and item_count: int. "
        "Valid coupon codes are 'SAVE10', 'SAVE20', and 'NONE'. "
        "'SAVE10' gives 10 percent off. 'SAVE20' gives 20 percent off, but only if cart_total is at least 100. "
        "'NONE' gives no discount. First-time orders get an extra 5 percent off, but total discount can never exceed 25 percent. "
        "If item_count is 0, return 0.0 no matter what coupon is used. "
        "If cart_total is negative or item_count is negative, raise ValueError. "
        "If coupon_code is invalid, raise ValueError. "
        "Return the discount amount, not the final price, rounded to 2 decimals."
    ),

    # Level 2 — Function with mutually exclusive precedence rules
    (
        "Build a function called calculate_late_fee. "
        "It takes amount_due: float, days_late: int, customer_tier: str, and had_prior_warning: bool. "
        "Valid customer tiers are 'standard', 'premium', and 'vip'. "
        "If days_late is 0, return 0.0. "
        "For standard customers, fee is 5 percent of amount_due. "
        "For premium customers, fee is 2 percent of amount_due. "
        "VIP customers never pay late fees. "
        "If had_prior_warning is True, add a fixed 10.0 penalty, but not for VIP customers. "
        "The total fee can never exceed 50.0. "
        "If amount_due is negative or days_late is negative, raise ValueError. "
        "If customer_tier is invalid, raise ValueError. "
        "Return the fee rounded to 2 decimals."
    ),

    # Level 3 — Class with replace-vs-merge state behavior
    (
        "Create a Playlist class for a music app demo. "
        "It should support add_song(title: str, duration_seconds: int) -> None, "
        "remove_song(title: str) -> None, get_total_duration() -> int, "
        "has_song(title: str) -> bool, and get_song_count() -> int. "
        "Adding a song with a new title adds it to the playlist. "
        "Adding a song with a title that already exists should replace its duration, not create a duplicate. "
        "Removing a missing song should do nothing. "
        "duration_seconds must be greater than 0, otherwise raise ValueError. "
        "Song titles must not be empty strings, otherwise raise ValueError. "
        "get_total_duration should return the sum of all current song durations. "
        "An empty playlist has duration 0 and song count 0."
    ),

    # Level 4 — Class with account locking and operation ordering
    (
        "I need a LoginAttemptTracker class. "
        "It should support record_failure(username: str) -> None, record_success(username: str) -> None, "
        "is_locked(username: str) -> bool, get_failure_count(username: str) -> int, and reset(username: str) -> None. "
        "A user starts with 0 failures and is not locked. "
        "Each failure increases the failure count by 1. "
        "After 3 failures, the user is locked. "
        "A successful login resets the failure count to 0, but only if the user is not locked. "
        "If the user is locked, record_success should not unlock the user. "
        "reset should clear the failure count and unlock the user. "
        "An empty username should raise ValueError for all methods that take username. "
        "Unknown users should behave like users with 0 failures and not locked."
    ),

    # Level 5 — Class with cart-style state but stricter replacement/cap rules
    (
        "Build a LoyaltyWallet class for a store. "
        "It should support earn_points(order_total: float) -> None, redeem_points(points: int) -> float, "
        "get_balance() -> int, and get_total_redeemed_value() -> float. "
        "For every full 10.0 dollars spent, earn 1 point. Partial dollars do not count. "
        "redeem_points removes points from the balance and returns their dollar value. "
        "Each point is worth 0.5 dollars. "
        "A customer cannot redeem more points than they have; if they try, raise ValueError. "
        "order_total must be non-negative, otherwise raise ValueError. "
        "redeem_points must receive a positive integer, otherwise raise ValueError. "
        "The total redeemed value should accumulate over time and be rounded to 2 decimals."
    ),

    # Level 6 — Function with tiered calculation plus override rules
    (
        "I need a function called calculate_paycheck. "
        "It takes hourly_rate: float, hours_worked: float, is_holiday: bool, and tax_rate: float. "
        "Regular pay applies up to 40 hours. "
        "Hours above 40 are paid at 1.5 times the hourly rate. "
        "If is_holiday is True, all hours are paid at 2 times the hourly rate and overtime does not apply separately. "
        "After gross pay is calculated, subtract tax_rate percent. "
        "tax_rate must be between 0 and 100 inclusive. "
        "hourly_rate and hours_worked must be non-negative. "
        "Return net pay rounded to 2 decimals."
    ),

    # Level 7 — Class with status transitions and allowed/forbidden transitions
    (
        "Create an OrderStateMachine class for an ecommerce demo. "
        "It should support create_order(order_id: str) -> None, pay(order_id: str) -> None, "
        "ship(order_id: str) -> None, cancel(order_id: str) -> None, get_status(order_id: str) -> str, "
        "and list_orders_by_status(status: str) -> list[str]. "
        "New orders start as 'created'. "
        "pay moves an order from 'created' to 'paid'. "
        "ship moves an order from 'paid' to 'shipped'. "
        "cancel is allowed only from 'created' or 'paid', and moves the order to 'cancelled'. "
        "A shipped order cannot be cancelled. "
        "Calling pay on anything other than 'created' should raise ValueError. "
        "Calling ship on anything other than 'paid' should raise ValueError. "
        "Creating the same order_id twice should raise ValueError. "
        "Missing order_id should raise ValueError for pay, ship, cancel, and get_status. "
        "list_orders_by_status should return matching order IDs sorted alphabetically. "
        "Valid statuses are 'created', 'paid', 'shipped', and 'cancelled'. Invalid status should raise ValueError."
    ),

    # Level 8 — Class with reservation windows using integer times
    (
        "I need a RoomBooking class for a meeting-room demo. "
        "Use integer hours instead of real dates. "
        "It should support book(room: str, start_hour: int, end_hour: int) -> None, "
        "cancel(room: str, start_hour: int, end_hour: int) -> None, "
        "is_available(room: str, start_hour: int, end_hour: int) -> bool, "
        "and get_bookings(room: str) -> list[tuple[int, int]]. "
        "A booking is valid only if start_hour is less than end_hour. "
        "Hours must be between 0 and 24 inclusive. "
        "Bookings overlap if their time ranges intersect. "
        "A room cannot have overlapping bookings. If book overlaps an existing booking, raise ValueError. "
        "Back-to-back bookings are allowed, for example 9-10 and 10-11 do not overlap. "
        "cancel should remove the exact matching booking. If no exact booking exists, raise ValueError. "
        "get_bookings should return bookings for the room sorted by start_hour."
    ),

    # Level 9 — Function with normalization and parsing rules
    (
        "Build a function called normalize_phone_number. "
        "It takes phone: str and default_country: str and returns a normalized phone number string. "
        "Valid default_country values are 'US' and 'IL'. "
        "Remove spaces, dashes, and parentheses from the phone input. "
        "If the cleaned phone starts with '+', keep the plus and digits only. "
        "For default_country 'US', if the cleaned phone has exactly 10 digits, return '+1' followed by the digits. "
        "For default_country 'IL', if the cleaned phone starts with '0', remove the leading 0 and return '+972' followed by the rest. "
        "If the cleaned phone is already international, return it unchanged after cleanup. "
        "If phone is empty after cleanup, raise ValueError. "
        "If default_country is invalid, raise ValueError. "
        "If the phone cannot be normalized by these rules, raise ValueError."
    ),

    # Level 10 — Hard class with allocation/cap rules
    (
        "Create a BudgetAllocator class. "
        "It should support set_budget(total_budget: float) -> None, allocate(category: str, amount: float) -> None, "
        "get_allocation(category: str) -> float, get_remaining_budget() -> float, and reset_category(category: str) -> None. "
        "The initial total budget is 0.0 until set_budget is called. "
        "set_budget replaces the total budget, but existing allocations remain. "
        "If existing allocations exceed the new budget, set_budget should raise ValueError and leave the old budget unchanged. "
        "allocate adds to the category allocation. "
        "Allocations across all categories cannot exceed the total budget. "
        "If an allocation would exceed the total budget, raise ValueError and do not change state. "
        "Negative budgets or negative allocation amounts should raise ValueError. "
        "Unknown categories should return allocation 0.0. "
        "reset_category removes that category allocation. "
        "Returned money values should be rounded to 2 decimals."
    ),
]


# Suite A — MVP smoke benchmark
# Purpose:
#   Prove the full pipeline works end-to-end on simple but representative tasks:
#   validation, rounding, precedence rules, simple state, keyed state, and lifecycle behavior.
#
# Expected use:
#   This suite should usually pass. It is not meant to be adversarial.
mvp1_benchmark_set = [
    benchmark_user_messages[0],  # apply_discount — validation + rounding
    benchmark_user_messages[1],  # calculate_ticket_price — precedence rules
    benchmark_user_messages[2],  # BankAccount — simple mutable state
    benchmark_user_messages[3],  # Inventory — keyed mutable state
    benchmark_user_messages[6],  # TaskTracker — lifecycle + sorted views
]


# Suite B — Hard business-logic benchmark
# Purpose:
#   Test whether the pipeline can handle harder one-artifact business logic:
#   caps, rule ordering, lock behavior, forbidden transitions, interval overlap,
#   and rollback/state consistency.
#
# Expected use:
#   This is the main showcase benchmark.
harder_mvp1_benchmark_set = [
    harder_benchmark_user_messages[0],  # calculate_coupon_discount — caps + rule ordering
    harder_benchmark_user_messages[3],  # LoginAttemptTracker — lock behavior + reset
    harder_benchmark_user_messages[6],  # OrderStateMachine — forbidden transitions
    harder_benchmark_user_messages[7],  # RoomBooking — interval overlap logic
    harder_benchmark_user_messages[9],  # BudgetAllocator — rollback + state consistency
]


adversarial_benchmark_set_original = [
    harder_benchmark_user_messages[2],  # Playlist — replace vs duplicate
    harder_benchmark_user_messages[4],  # LoyaltyWallet — accumulated redemption
    harder_benchmark_user_messages[5],  # calculate_paycheck — holiday override vs overtime
    harder_benchmark_user_messages[8],  # normalize_phone_number — parsing/normalization
    harder_benchmark_user_messages[9],  # BudgetAllocator — rollback/state consistency
]