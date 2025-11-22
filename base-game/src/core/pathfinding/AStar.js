export var PathFindResultType;
(function (PathFindResultType) {
    PathFindResultType[PathFindResultType["NextTile"] = 0] = "NextTile";
    PathFindResultType[PathFindResultType["Pending"] = 1] = "Pending";
    PathFindResultType[PathFindResultType["Completed"] = 2] = "Completed";
    PathFindResultType[PathFindResultType["PathNotFound"] = 3] = "PathNotFound";
})(PathFindResultType || (PathFindResultType = {}));
