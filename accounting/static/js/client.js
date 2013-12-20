'use strict';

angular.module('accountingClient', ['ngRoute', 'accountingApi'])
.config(function($routeProvider) {
    $routeProvider
        .when('/', {
            controller: 'ListTransactionsCtrl',
            templateUrl: '/static/templates/list-transactions.html'
        })
        .when('/show/:transactionId', {
            controller: 'TransactionDetailCtrl',
            templateUrl: '/static/templates/detail.html'
        })
        .when('/edit/:transactionId', {
            controller: 'EditTransactionCtrl',
            templateUrl: '/static/templates/edit.html'
        })
        .when('/new', {
            controller: 'CreateTransactionCtrl',
            templateUrl: '/static/templates/edit.html'
        })
        .otherwise({
            redirectTo: '/'
        })
})
.controller('ListTransactionsCtrl', function ($scope, AccountingApi) {
    var request = AccountingApi.get();
    console.log('request: ', request)
    $scope.request = request
    console.log('$scope.request', $scope.request)
})
.controller('TransactionDetailCtrl', function ($scope, $routeParams,
                                              AccountingApi) {
    $scope.transaction = AccountingApi.get({
        id: $routeParams.transactionId
    });
})
.controller('CreateTransactionCtrl', function ($scope, $location, $timeout,
                                               AccountingApi, Transaction,
                                               Posting, Amount) {
    $scope.transaction = new Transaction({
        postings: [
            new Posting({
                amount: new Amount({symbol: 'USD'})
            }),
            new Posting({
                amount: new Amount({symbol: 'USD'})
            })
        ]
    });

    $scope.addPosting = function(e) {
        $scope.transaction.postings.push(
            new Posting({
                amount: new Amount({symbol: 'USD'})
            })
        );
        e.stopPropagation();
        return false;
    };
    $scope.save = function () {
        console.log($scope.transaction);
        AccountingApi.save($scope.transaction, function () {
            $timeout(function () { $location.path('/'); });
        });
    };
})
