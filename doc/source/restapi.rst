========================
 REST API Documentation
========================

The accounting-api projects main application provides a REST API for accounting
data. This is the documentation for the various REST endpoints that the
accounting-api application provides.

Get all transactions
----------------

.. http:get:: /transaction

    **Example request**

    .. code-block:: http

        GET /transaction HTTP/1.1
        Host: accounting.example
        Accept: application/json


    **Example response**

    .. code-block:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "transactions": [
            {
              "__type__": "Transaction",
              "date": "2010-01-01",
              "id": "Ids can be anything",
              "metadata": {},
              "payee": "Kindly T. Donor",
              "postings": [
                {
                  "__type__": "Posting",
                  "account": "Income:Foo:Donation",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "-100",
                    "symbol": "$"
                  },
                  "metadata": {
                    "Invoice": "Projects/Foo/Invoices/Invoice20100101.pdf"
                  }
                },
                {
                  "__type__": "Posting",
                  "account": "Assets:Checking",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "100",
                    "symbol": "$"
                  },
                  "metadata": {}
                }
              ]
            },
            {
              "__type__": "Transaction",
              "date": "2011-03-15",
              "id": "but mind you if they collide.",
              "metadata": {},
              "payee": "Another J. Donor",
              "postings": [
                {
                  "__type__": "Posting",
                  "account": "Income:Foo:Donation",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "-400",
                    "symbol": "$"
                  },
                  "metadata": {
                    "Approval": "Projects/Foo/earmark-record.txt"
                  }
                },
                {
                  "__type__": "Posting",
                  "account": "Assets:Checking",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "400",
                    "symbol": "$"
                  },
                  "metadata": {}
                }
              ]
            },
          ]
        }


Get a single transaction
------------------------

.. http:get:: /transaction/<string:transaction_id>

    **Example request**

    .. code-block:: http

        GET /transaction/2aeea63b-0996-4ead-bc4c-e15505dff226 HTTP/1.1
        Host: accounting.example
        Accept: application/json

    **Example response**

    .. code-block:: http

        HTTP/1.0 200 OK
        Content-Type: application/json

        {
          "transaction": {
            "__type__": "Transaction", 
            "date": "2013-12-26", 
            "id": "2aeea63b-0996-4ead-bc4c-e15505dff226", 
            "metadata": {}, 
            "payee": "January Rent", 
            "postings": [
              {
                "__type__": "Posting", 
                "account": "Assets:Checking", 
                "amount": {
                  "__type__": "Amount", 
                  "amount": "-424.24", 
                  "symbol": "USD"
                }, 
                "metadata": {}
              }, 
              {
                "__type__": "Posting", 
                "account": "Expenses:Rent", 
                "amount": {
                  "__type__": "Amount", 
                  "amount": "424.24", 
                  "symbol": "USD"
                }, 
                "metadata": {}
              }
            ]
          }
        }

Add transactions
----------------

.. http:post:: /transaction

    :jsonparam array transactions: A list of Transaction objects to add.

    **Example request**

    .. code-block:: http

        POST /transaction HTTP/1.1
        Host: accounting.example
        Content-Type: application/json
        Accept: application/json

        {
          "transactions": [
            {
              "__type__": "Transaction",
              "date": "2010-01-01",
              "id": "Ids can be anything",
              "metadata": {},
              "payee": "Kindly T. Donor",
              "postings": [
                {
                  "__type__": "Posting",
                  "account": "Income:Foo:Donation",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "-100",
                    "symbol": "$"
                  },
                  "metadata": {
                    "Invoice": "Projects/Foo/Invoices/Invoice20100101.pdf"
                  }
                },
                {
                  "__type__": "Posting",
                  "account": "Assets:Checking",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "100",
                    "symbol": "$"
                  },
                  "metadata": {}
                }
              ]
            },
          ]
        }

    **Example response**

    .. code-block:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "status": "OK",
          "transaction_ids": [
            "Ids can be anything"
          ]
        }


Delete a transaction
--------------------

.. http:delete:: /transaction/<string:transaction_id>

    Delete the transaction with ID :data:`transaction_id`.

    **Example request**

    .. code-block:: http

        DELETE /transaction/123456 HTTP/1.1
        Host: accounting.example
        Accept: application/json

    **Example response**

    .. code-block:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "status": "OK"
        }


Update a transaction
--------------------

.. http:post:: /transaction/<string:transaction_id>

    **Example request**

    .. code-block:: http

        POST /transaction/2aeea63b-0996-4ead-bc4c-e15505dff226 HTTP/1.1
        Host: accounting.example
        Content-Type: application/json
        Accept: application/json

        {
          "transaction": {
            "__type__": "Transaction", 
            "date": "2013-12-26", 
            "id": "2aeea63b-0996-4ead-bc4c-e15505dff226", 
            "metadata": {}, 
            "payee": "February Rent", 
            "postings": [
              {
                "__type__": "Posting", 
                "account": "Assets:Checking", 
                "amount": {
                  "__type__": "Amount", 
                  "amount": "-424.24", 
                  "symbol": "USD"
                }, 
                "metadata": {}
              }, 
              {
                "__type__": "Posting", 
                "account": "Expenses:Rent", 
                "amount": {
                  "__type__": "Amount", 
                  "amount": "424.24", 
                  "symbol": "USD"
                }, 
                "metadata": {}
              }
            ]
          }
        }

    **Example response**

    .. code-block:: http

        HTTP/1.0 200 OK
        Content-Type: application/json

        {
          "status": "OK"
        }
