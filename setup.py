from setuptools import setup

setup(
    name="Tarot",
    version="1.0",
    description="Tarot game",
    author="Julien LIVET",
    author_email="julien.livet@free.fr",
    packages=["TarotAndroid"],
    include_package_data=True
    package_data={
        "Tarot": ["images/*.png",
                  "locales/**/*.mo"],
    },
    zip_safe=False,
    install_requires=[
        "distribute",
        "kivy",
        "pillow",
    ],
    entry_points={
        "console_scripts": [
            "tarot = TarotAndroid.main:main",
        ]
    },
)
