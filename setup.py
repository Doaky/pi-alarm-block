from setuptools import setup, find_packages

setup(
    name="alarm-block",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "apscheduler>=3.10.0",
        "pygame>=2.5.0",
        "python-multipart",  # For form data
        "python-jose[cryptography]",  # For future JWT support if needed
        "RPi.GPIO; platform_system == 'Linux'",  # Only on Linux systems
    ],
    python_requires=">=3.8",
    author="doaky",
    description="A Raspberry Pi alarm clock system",
    keywords="raspberry-pi, alarm-clock, fastapi",
    project_urls={
        "Source": "https://github.com/doaky/alarm-block",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: POSIX :: Linux",
        "Topic :: Home Automation",
    ],
)
