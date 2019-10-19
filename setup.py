from setuptools import setup

setup(
    name="img",
    version="0.1",
    py_modules=["img"],
    entry_points = {
        'console_scripts': [
            'img=img:main',
        ],
    },
    install_requires=["pillow>=6.1.0"],
)
