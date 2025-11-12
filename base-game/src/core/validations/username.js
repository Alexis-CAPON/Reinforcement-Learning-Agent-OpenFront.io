"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MAX_USERNAME_LENGTH = exports.MIN_USERNAME_LENGTH = void 0;
exports.fixProfaneUsername = fixProfaneUsername;
exports.isProfaneUsername = isProfaneUsername;
exports.validateUsername = validateUsername;
exports.sanitizeUsername = sanitizeUsername;
const obscenity_1 = require("obscenity");
const Utils_1 = require("../../client/Utils");
const Util_1 = require("../Util");
const matcher = new obscenity_1.RegExpMatcher(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign({}, obscenity_1.englishDataset.build()), obscenity_1.englishRecommendedTransformers), (0, obscenity_1.resolveConfusablesTransformer)()), (0, obscenity_1.skipNonAlphabeticTransformer)()), (0, obscenity_1.collapseDuplicatesTransformer)()), (0, obscenity_1.resolveLeetSpeakTransformer)()));
exports.MIN_USERNAME_LENGTH = 3;
exports.MAX_USERNAME_LENGTH = 27;
const validPattern = /^[a-zA-Z0-9_[\] 🐈🍀üÜ]+$/u;
const shadowNames = [
    "NicePeopleOnly",
    "BeKindPlz",
    "LearningManners",
    "StayClassy",
    "BeNicer",
    "NeedHugs",
    "MakeFriends",
];
function fixProfaneUsername(username) {
    if (isProfaneUsername(username)) {
        return shadowNames[(0, Util_1.simpleHash)(username) % shadowNames.length];
    }
    return username;
}
function isProfaneUsername(username) {
    return matcher.hasMatch(username);
}
function validateUsername(username) {
    if (typeof username !== "string") {
        return { isValid: false, error: (0, Utils_1.translateText)("username.not_string") };
    }
    if (username.length < exports.MIN_USERNAME_LENGTH) {
        return {
            isValid: false,
            error: (0, Utils_1.translateText)("username.too_short", {
                min: exports.MIN_USERNAME_LENGTH,
            }),
        };
    }
    if (username.length > exports.MAX_USERNAME_LENGTH) {
        return {
            isValid: false,
            error: (0, Utils_1.translateText)("username.too_long", {
                max: exports.MAX_USERNAME_LENGTH,
            }),
        };
    }
    if (!validPattern.test(username)) {
        return {
            isValid: false,
            error: (0, Utils_1.translateText)("username.invalid_chars", {
                max: exports.MAX_USERNAME_LENGTH,
            }),
        };
    }
    // All checks passed
    return { isValid: true };
}
function sanitizeUsername(str) {
    const sanitized = Array.from(str)
        .filter((ch) => validPattern.test(ch))
        .join("")
        .slice(0, exports.MAX_USERNAME_LENGTH);
    return sanitized.padEnd(exports.MIN_USERNAME_LENGTH, "x");
}
