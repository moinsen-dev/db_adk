from setuptools import setup, find_packages

setup(
    name="db_adk",
    version="0.1.0",
    description="Database-driven Agent Development Kit using Google ADK",
    author="",
    author_email="",
    packages=find_packages(),
    install_requires=[
        "google-adk>=0.2.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "click>=8.1.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "jsonschema>=4.17.0",
    ],
    entry_points={
        "console_scripts": [
            "db-adk=db_adk.api.cli:cli",
        ],
    },
    python_requires=">=3.9",
)
