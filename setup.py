from distutils.core import setup

from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()



setup(
    name='hms_spacestatus',
    version='1.1',
    packages=['hms_spacestatus'],
    scripts=['bin/hms_spacestatus_daemon'],

    url='https://github.com/haum/hms_spacestatus',
    license='MIT',

    author='Romain Porte (MicroJoe)',
    author_email='microjoe@microjoe.org',

    description='HAUM\'s status microservice',
    long_description=long_description,

    classifiers = [
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    install_requires=['pika', 'hms_base>=2.0,<3', 'irc', 'coloredlogs',
                      'watchdog', 'requests']
)
