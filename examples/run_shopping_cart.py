"""Example: run the AI delivery pipeline for a ShoppingCart class."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv

load_dotenv()

from ai_delivery.pipeline.run import RunPipeline

user_message = (
    "I need a small shopping cart class for a checkout demo. "
    "It should let me add products, remove them, see the subtotal, apply a simple discount code, "
    "and get the final total. "
    "For now the only discount code we support is DISCOUNT10, which takes 10 percent off. "
    "If I add the same product twice, just increase the quantity. "
    "If I remove something that is not there, don't crash. "
    "Bad data should not be accepted: negative prices or negative quantities should raise an error. "
    "Quantity zero should just do nothing. "
    "Money values should come back as floats rounded to 2 decimals. "
    "Keep it simple and put everything in a ShoppingCart class."
)

artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts/runs")
pipeline = RunPipeline(artifacts_dir=artifacts_dir)
pipeline.run(user_message)
