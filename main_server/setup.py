from setuptools import setup

setup(
    name='sumica',
    packages=['sumica'],
    include_package_data=True,
    install_requires=[
        'flask',
        'Flask-PyMongo'
    ],
)
