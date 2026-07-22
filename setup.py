from setuptools import setup, find_packages

setup(
    name="marketshift",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "fastapi",
        "uvicorn",
        "streamlit",
        "xgboost",
        "python-dotenv",
        "ta",
        "scikit-learn",
        "joblib",
    ],
)
