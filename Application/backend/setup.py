from setuptools import find_packages, setup

setup(
    name="nba_stats",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "aiohttp",
        "pytest",
        "pytest-asyncio",
        "python-dateutil",
        "nba_api",
        "alembic",
    ],
)
