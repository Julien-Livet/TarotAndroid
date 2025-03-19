from setuptools import setup

setup(
    name="Tarot",
    version="1.0",
    description="Tarot game",
    author="Julien LIVET",
    author_email="julien.livet@free.fr",
    packages=["TarotAndroid"],
    install_requires=[
        "kivy",
        "pillow",
    ],
    entry_points={
        "console_scripts": [
            "tarot = TarotAndroid.main:main",
        ]
    },
)
