export var GameEnv;
(function (GameEnv) {
    GameEnv[GameEnv["Dev"] = 0] = "Dev";
    GameEnv[GameEnv["Preprod"] = 1] = "Preprod";
    GameEnv[GameEnv["Prod"] = 2] = "Prod";
})(GameEnv || (GameEnv = {}));
