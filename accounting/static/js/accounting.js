'use strict';
// Part of the accounting-api project:
// https://gitorious.org/conservancy/accounting-api
// License: AGPLv3-or-later

function s4() {
  return Math.floor((1 + Math.random()) * 0x10000)
             .toString(16)
             .substring(1);
};

function guid() {
  return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
         s4() + '-' + s4() + s4() + s4();
}

function Transaction(args) {
    var self = this;
    this.__type__ = 'Transaction';
    this.id = null;
    this.payee = null;
    this.date = null;
    this.postings = null;
    this.metadata = {};

    this.generateId = function () {
        self.id = guid();
    }

    for (var i in args) {
        this[i] = args[i];
    }
}

function Posting(args) {
    this.__type__ = 'Posting';
    this.account = null;
    this.amount = null;

    for (var i in args) {
        this[i] = args[i];
    }
}

function Amount(args) {
    this.__type__ = 'Amount';
    this.symbol = null;
    this.amount = null;

    for (var i in args) {
        this[i] = args[i];
    }
}

var models = {
    'Amount': Amount,
    'Posting': Posting,
    'Transaction': Transaction
};

function accountingObjectHook(object) {
    if ('__type__' in object) {
        console.log('Found typed object: ', object.__type__, object);
        var model = new models[object.__type__];
        for (var i in object) {
            model[i] = object[i];
        }
        return model;
    }
    return object;
}

function transformResponseFactory(object_hook) {
    var self = this;
    self.object_hook = object_hook;

    function transformResponse(json, headers) {
        var transformed;
        console.log('json: ', json);
        if (typeof json == 'undefined') {
            return;
        } else if ((typeof json == 'object') &&
                   Object.prototype.toString.call(json) == '[object Object]') {
            console.log('json is Object, json: ', json);
            for (var i in json) {
                json[i] = transformResponse(json[i]);
            }
            transformed = self.object_hook(json)
        } else if ((typeof json == 'object') &&
                   Object.prototype.toString.call(json) == '[object Array]') {
            console.log('json is Array, json: ', json);
            for (var i in json) {
                json[i] = transformResponse(json[i]);
            }
            transformed = json;
        } else {
            transformed = json;
        }
        return transformed;
    };
    return transformResponse;
}

function transformRequestFactory(object_hook) {
    function transformRequest(data, headerSetter) {
        console.log('transformRequest', data, headerSetter)
        headerSetter()['Content-Type'] = 'application/json';
        return data;
    }
    return transformRequest;
}

angular.module('accountingApi', ['ngResource'])
.factory('Transaction', function () {
    return Transaction;
})
.factory('Posting', function () {
    return Posting;
})
.factory('Amount', function () {
    return Amount;
})
.factory('AccountingApi', function($resource, $http) {
    $http.defaults.useXDomain = true;
    $http.defaults.transformResponse.push(new transformResponseFactory(
        accountingObjectHook));
    var AccountingApi = $resource(
        '/transaction/:id',
        {},
        {
            get: {
                method: 'GET',
                transformResponse: Array.prototype.concat(
                    $http.defaults.transformResponse,
                    [function (data){
                        if (typeof data == 'object' &&
                            'transaction' in data) {
                            return data.transaction;
                        }
                        return data;
                    }]
                )
            },
            save: {
                method: 'POST',
                transformRequest: [new transformRequestFactory()].concat(
                    $http.defaults.transformRequest)
            }
        }
    );
    return AccountingApi;
});
