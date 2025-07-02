#!/usr/bin/env python3
"""Example demonstrating retry functionality in claif_cod."""

import asyncio

from claif.common import ClaifOptions

from claif_cod import query


async def main():
    """Run example queries with retry configuration."""

    # Example 1: Query with default retry settings

    async for _message in query("What is the capital of France?"):
        pass


    # Example 2: Query with custom retry settings

    options = ClaifOptions(
        retry_count=5,  # Try up to 5 times
        retry_delay=2.0,  # Start with 2 second delay
        verbose=True,  # Enable verbose logging
    )

    async for _message in query("Explain Python decorators", options):
        pass


    # Example 3: Query with retry disabled

    options = ClaifOptions(
        retry_count=0,  # Disable retry
        verbose=True,
    )

    async for _message in query("What is machine learning?", options):
        pass


if __name__ == "__main__":
    asyncio.run(main())
