(function (angular) {
    "use strict";
    angular.module("CalendarFinder", [
        "ngResource",
        "ngRoute"
    ]);
})(angular);

(function (angular) {
    "use strict";
    angular.module("CalendarFinder").config(["$routeProvider", "$resourceProvider",
        function ($routeProvider, $resourceProvider) {

            $resourceProvider.defaults.stripTrailingSlashes = false;

            $routeProvider.when("/", {
                name: "Landing",
                controller: "AppLandingController",
                controllerAs: 'vm',
                templateUrl: "/static/calendar/app_landing.html"
            }).otherwise({
                redirectTo: '/'
            });
        }
    ]);
})(angular);
