====================
 The Accounting API
====================

--------------
 Dependencies
--------------

-   ledger-cli version 3 (I have not tried with version 2.x)
-   Flask (install by running ``pip install -r requirements.txt``).


-------
 Usage
-------

.. code-block:: bash

    # Run the web service
    LEDGER_FILE=../path/to/your.ledger ./bin/serve

    # Run a simple example
    python3 accounting/__init__.py
