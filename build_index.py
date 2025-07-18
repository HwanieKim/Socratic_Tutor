#!/usr/bin/env python3
"""
Build script to create index during Railway deployment
"""
import os
import sys
import asyncio

# Add src to path
sys.path.append('src')

async def build_index():
    """Build index during deployment"""
    try:
        from core.persistence import create_index
        print("Creating index during build...")
        await create_index()
        print("Index created successfully!")
    except Exception as e:
        print(f"Failed to create index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(build_index())

