==========
 REST API
==========

Get transactions
----------------

.. http:get:: /transaction

    Get all transactions

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
