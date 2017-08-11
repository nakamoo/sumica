from setuptools import setup

setup(
    name='hai',
    packages=['hai'],
    include_package_data=True,
    install_requires=[
        'flask',
        'Flask-PyMongo'
    ],
)
