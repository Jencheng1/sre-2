from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="sre-copilot",
    version="0.1.0",
    author="SRE Copilot Team",
    author_email="your.email@example.com",
    description="A multi-agent system built on AWS Bedrock for root cause analysis of incidents in AWS environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sre-copilot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "sre-configure=src.core.configure_agents:main",
            "sre-test=src.core.test_functionality:main",
            "sre-kb=src.core.knowledge_base_manager:main",
            "sre-analyze=src.core.incident_analyzer:main",
        ],
    },
)
