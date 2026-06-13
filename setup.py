from setuptools import setup

setup(
    name="tellm",
    version="4.0.3",
    packages=["tellm"],
    package_dir={"tellm": "."},
    install_requires=[
        "litellm>=1.0.0",
        "websockets>=12.0",
        "pyttsx3>=2.90",
        "python-dotenv>=1.0.0",
        "faster-whisper>=0.11.0",
    ],
    entry_points={"console_scripts": ["tellm-bot=tellm.main:main"]},
    python_requires=">=3.8",
)
