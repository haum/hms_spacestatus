HAUM's SpaceStatus microservice
===============================

.. image:: https://travis-ci.org/haum/hms_spacestatus.svg?branch=master
    :target: https://travis-ci.org/haum/hms_spacestatus

.. image:: https://coveralls.io/repos/github/haum/hms_spacestatus/badge.svg?branch=master
    :target: https://coveralls.io/github/haum/hms_spacestatus?branch=master

A microservice that handles the hackerspace's status.

Using
-----

Create a Python 3 virtualenv and install software::

    $ virtualenv -ppython3 venv
    $ source venv/bin/activate
    (venv) $ pip install .

Then start the daemon inside the virtual env::

    $ hms_spacestatus_daemon

License
-------

This project is brought to you under MIT license. For further information,
please read the provided ``LICENSE`` file.
