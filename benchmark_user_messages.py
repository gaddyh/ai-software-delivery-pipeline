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

# Suggested MVP 1 Benchmark Set (first 5 + 2 regressions)
mvp1_benchmark_set = [
    benchmark_user_messages[0],  # apply_discount
    benchmark_user_messages[1],  # calculate_ticket_price
    benchmark_user_messages[2],  # BankAccount
    benchmark_user_messages[3],  # Inventory
    benchmark_user_messages[5],  # GradeBook
]
