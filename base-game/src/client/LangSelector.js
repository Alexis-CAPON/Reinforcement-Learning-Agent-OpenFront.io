"use strict";
var __esDecorate = (this && this.__esDecorate) || function (ctor, descriptorIn, decorators, contextIn, initializers, extraInitializers) {
    function accept(f) { if (f !== void 0 && typeof f !== "function") throw new TypeError("Function expected"); return f; }
    var kind = contextIn.kind, key = kind === "getter" ? "get" : kind === "setter" ? "set" : "value";
    var target = !descriptorIn && ctor ? contextIn["static"] ? ctor : ctor.prototype : null;
    var descriptor = descriptorIn || (target ? Object.getOwnPropertyDescriptor(target, contextIn.name) : {});
    var _, done = false;
    for (var i = decorators.length - 1; i >= 0; i--) {
        var context = {};
        for (var p in contextIn) context[p] = p === "access" ? {} : contextIn[p];
        for (var p in contextIn.access) context.access[p] = contextIn.access[p];
        context.addInitializer = function (f) { if (done) throw new TypeError("Cannot add initializers after decoration has completed"); extraInitializers.push(accept(f || null)); };
        var result = (0, decorators[i])(kind === "accessor" ? { get: descriptor.get, set: descriptor.set } : descriptor[key], context);
        if (kind === "accessor") {
            if (result === void 0) continue;
            if (result === null || typeof result !== "object") throw new TypeError("Object expected");
            if (_ = accept(result.get)) descriptor.get = _;
            if (_ = accept(result.set)) descriptor.set = _;
            if (_ = accept(result.init)) initializers.unshift(_);
        }
        else if (_ = accept(result)) {
            if (kind === "field") initializers.unshift(_);
            else descriptor[key] = _;
        }
    }
    if (target) Object.defineProperty(target, contextIn.name, descriptor);
    done = true;
};
var __runInitializers = (this && this.__runInitializers) || function (thisArg, initializers, value) {
    var useValue = arguments.length > 2;
    for (var i = 0; i < initializers.length; i++) {
        value = useValue ? initializers[i].call(thisArg, value) : initializers[i].call(thisArg);
    }
    return useValue ? value : void 0;
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __setFunctionName = (this && this.__setFunctionName) || function (f, name, prefix) {
    if (typeof name === "symbol") name = name.description ? "[".concat(name.description, "]") : "";
    return Object.defineProperty(f, "name", { configurable: true, value: prefix ? "".concat(prefix, " ", name) : name });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LangSelector = void 0;
const lit_1 = require("lit");
const decorators_js_1 = require("lit/decorators.js");
require("./LanguageModal");
const ar_json_1 = require("../../resources/lang/ar.json");
const bg_json_1 = require("../../resources/lang/bg.json");
const bn_json_1 = require("../../resources/lang/bn.json");
const cs_json_1 = require("../../resources/lang/cs.json");
const da_json_1 = require("../../resources/lang/da.json");
const de_json_1 = require("../../resources/lang/de.json");
const en_json_1 = require("../../resources/lang/en.json");
const eo_json_1 = require("../../resources/lang/eo.json");
const es_json_1 = require("../../resources/lang/es.json");
const fi_json_1 = require("../../resources/lang/fi.json");
const fr_json_1 = require("../../resources/lang/fr.json");
const gl_json_1 = require("../../resources/lang/gl.json");
const he_json_1 = require("../../resources/lang/he.json");
const hi_json_1 = require("../../resources/lang/hi.json");
const hu_json_1 = require("../../resources/lang/hu.json");
const it_json_1 = require("../../resources/lang/it.json");
const ja_json_1 = require("../../resources/lang/ja.json");
const ko_json_1 = require("../../resources/lang/ko.json");
const nl_json_1 = require("../../resources/lang/nl.json");
const pl_json_1 = require("../../resources/lang/pl.json");
const pt_BR_json_1 = require("../../resources/lang/pt-BR.json");
const pt_PT_json_1 = require("../../resources/lang/pt-PT.json");
const ru_json_1 = require("../../resources/lang/ru.json");
const sh_json_1 = require("../../resources/lang/sh.json");
const sk_json_1 = require("../../resources/lang/sk.json");
const sl_json_1 = require("../../resources/lang/sl.json");
const sv_SE_json_1 = require("../../resources/lang/sv-SE.json");
const tp_json_1 = require("../../resources/lang/tp.json");
const tr_json_1 = require("../../resources/lang/tr.json");
const uk_json_1 = require("../../resources/lang/uk.json");
const zh_CN_json_1 = require("../../resources/lang/zh-CN.json");
let LangSelector = (() => {
    let _classDecorators = [(0, decorators_js_1.customElement)("lang-selector")];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _classSuper = lit_1.LitElement;
    let _translations_decorators;
    let _translations_initializers = [];
    let _translations_extraInitializers = [];
    let _defaultTranslations_decorators;
    let _defaultTranslations_initializers = [];
    let _defaultTranslations_extraInitializers = [];
    let _currentLang_decorators;
    let _currentLang_initializers = [];
    let _currentLang_extraInitializers = [];
    let _languageList_decorators;
    let _languageList_initializers = [];
    let _languageList_extraInitializers = [];
    let _showModal_decorators;
    let _showModal_initializers = [];
    let _showModal_extraInitializers = [];
    let _debugMode_decorators;
    let _debugMode_initializers = [];
    let _debugMode_extraInitializers = [];
    var LangSelector = _classThis = class extends _classSuper {
        constructor() {
            super(...arguments);
            this.translations = __runInitializers(this, _translations_initializers, void 0);
            this.defaultTranslations = (__runInitializers(this, _translations_extraInitializers), __runInitializers(this, _defaultTranslations_initializers, void 0));
            this.currentLang = (__runInitializers(this, _defaultTranslations_extraInitializers), __runInitializers(this, _currentLang_initializers, "en"));
            this.languageList = (__runInitializers(this, _currentLang_extraInitializers), __runInitializers(this, _languageList_initializers, []));
            this.showModal = (__runInitializers(this, _languageList_extraInitializers), __runInitializers(this, _showModal_initializers, false));
            this.debugMode = (__runInitializers(this, _showModal_extraInitializers), __runInitializers(this, _debugMode_initializers, false));
            this.debugKeyPressed = (__runInitializers(this, _debugMode_extraInitializers), false);
            this.languageMap = {
                ar: ar_json_1.default,
                bg: bg_json_1.default,
                bn: bn_json_1.default,
                de: de_json_1.default,
                en: en_json_1.default,
                es: es_json_1.default,
                eo: eo_json_1.default,
                fr: fr_json_1.default,
                it: it_json_1.default,
                hi: hi_json_1.default,
                hu: hu_json_1.default,
                ja: ja_json_1.default,
                nl: nl_json_1.default,
                pl: pl_json_1.default,
                "pt-PT": pt_PT_json_1.default,
                "pt-BR": pt_BR_json_1.default,
                ru: ru_json_1.default,
                sh: sh_json_1.default,
                tr: tr_json_1.default,
                tp: tp_json_1.default,
                uk: uk_json_1.default,
                cs: cs_json_1.default,
                he: he_json_1.default,
                da: da_json_1.default,
                fi: fi_json_1.default,
                "sv-SE": sv_SE_json_1.default,
                "zh-CN": zh_CN_json_1.default,
                ko: ko_json_1.default,
                gl: gl_json_1.default,
                sl: sl_json_1.default,
                sk: sk_json_1.default,
            };
        }
        createRenderRoot() {
            return this;
        }
        connectedCallback() {
            super.connectedCallback();
            this.setupDebugKey();
            this.initializeLanguage();
        }
        setupDebugKey() {
            window.addEventListener("keydown", (e) => {
                var _a;
                if (((_a = e.key) === null || _a === void 0 ? void 0 : _a.toLowerCase()) === "t")
                    this.debugKeyPressed = true;
            });
            window.addEventListener("keyup", (e) => {
                var _a;
                if (((_a = e.key) === null || _a === void 0 ? void 0 : _a.toLowerCase()) === "t")
                    this.debugKeyPressed = false;
            });
        }
        getClosestSupportedLang(lang) {
            if (!lang)
                return "en";
            if (lang in this.languageMap)
                return lang;
            const base = lang.slice(0, 2);
            const candidates = Object.keys(this.languageMap).filter((key) => key.startsWith(base));
            if (candidates.length > 0) {
                candidates.sort((a, b) => b.length - a.length); // More specific first
                return candidates[0];
            }
            return "en";
        }
        initializeLanguage() {
            return __awaiter(this, void 0, void 0, function* () {
                const browserLocale = navigator.language;
                const savedLang = localStorage.getItem("lang");
                const userLang = this.getClosestSupportedLang(savedLang !== null && savedLang !== void 0 ? savedLang : browserLocale);
                this.defaultTranslations = this.loadLanguage("en");
                this.translations = this.loadLanguage(userLang);
                this.currentLang = userLang;
                yield this.loadLanguageList();
                this.applyTranslation();
            });
        }
        loadLanguage(lang) {
            var _a;
            const language = (_a = this.languageMap[lang]) !== null && _a !== void 0 ? _a : {};
            const flat = flattenTranslations(language);
            return flat;
        }
        loadLanguageList() {
            return __awaiter(this, void 0, void 0, function* () {
                var _a, _b, _c, _d;
                try {
                    const data = this.languageMap;
                    let list = [];
                    const browserLang = new Intl.Locale(navigator.language).language;
                    for (const langCode of Object.keys(data)) {
                        const langData = data[langCode].lang;
                        if (!langData)
                            continue;
                        list.push({
                            code: (_a = langData.lang_code) !== null && _a !== void 0 ? _a : langCode,
                            native: (_b = langData.native) !== null && _b !== void 0 ? _b : langCode,
                            en: (_c = langData.en) !== null && _c !== void 0 ? _c : langCode,
                            svg: (_d = langData.svg) !== null && _d !== void 0 ? _d : langCode,
                        });
                    }
                    let debugLang = null;
                    if (this.debugKeyPressed) {
                        debugLang = {
                            code: "debug",
                            native: "Debug",
                            en: "Debug",
                            svg: "xx",
                        };
                        this.debugMode = true;
                    }
                    const currentLangEntry = list.find((l) => l.code === this.currentLang);
                    const browserLangEntry = browserLang !== this.currentLang && browserLang !== "en"
                        ? list.find((l) => l.code === browserLang)
                        : undefined;
                    const englishEntry = this.currentLang !== "en"
                        ? list.find((l) => l.code === "en")
                        : undefined;
                    list = list.filter((l) => l.code !== this.currentLang &&
                        l.code !== browserLang &&
                        l.code !== "en" &&
                        l.code !== "debug");
                    list.sort((a, b) => a.en.localeCompare(b.en));
                    const finalList = [];
                    if (currentLangEntry)
                        finalList.push(currentLangEntry);
                    if (englishEntry)
                        finalList.push(englishEntry);
                    if (browserLangEntry)
                        finalList.push(browserLangEntry);
                    finalList.push(...list);
                    if (debugLang)
                        finalList.push(debugLang);
                    this.languageList = finalList;
                }
                catch (err) {
                    console.error("Failed to load language list:", err);
                }
            });
        }
        changeLanguage(lang) {
            localStorage.setItem("lang", lang);
            this.translations = this.loadLanguage(lang);
            this.currentLang = lang;
            this.applyTranslation();
            this.showModal = false;
        }
        applyTranslation() {
            var _a;
            const components = [
                "single-player-modal",
                "host-lobby-modal",
                "join-private-lobby-modal",
                "emoji-table",
                "leader-board",
                "build-menu",
                "win-modal",
                "game-starting-modal",
                "top-bar",
                "player-panel",
                "replay-panel",
                "help-modal",
                "settings-modal",
                "username-input",
                "public-lobby",
                "user-setting",
                "o-modal",
                "o-button",
                "territory-patterns-modal",
            ];
            document.title = (_a = this.translateText("main.title")) !== null && _a !== void 0 ? _a : document.title;
            document.querySelectorAll("[data-i18n]").forEach((element) => {
                const key = element.getAttribute("data-i18n");
                if (key === null)
                    return;
                const text = this.translateText(key);
                if (text === null) {
                    console.warn(`Translation key not found: ${key}`);
                    return;
                }
                element.textContent = text;
            });
            components.forEach((tag) => {
                document.querySelectorAll(tag).forEach((el) => {
                    if (typeof el.requestUpdate === "function") {
                        el.requestUpdate();
                    }
                });
            });
        }
        translateText(key, params = {}) {
            let text;
            if (this.translations && key in this.translations) {
                text = this.translations[key];
            }
            else if (this.defaultTranslations && key in this.defaultTranslations) {
                text = this.defaultTranslations[key];
            }
            else {
                console.warn(`Translation key not found: ${key}`);
                return key;
            }
            for (const param in params) {
                const value = params[param];
                text = text.replace(`{${param}}`, String(value));
            }
            return text;
        }
        openModal() {
            this.debugMode = this.debugKeyPressed;
            this.showModal = true;
            this.loadLanguageList();
        }
        render() {
            var _a;
            const currentLang = (_a = this.languageList.find((l) => l.code === this.currentLang)) !== null && _a !== void 0 ? _a : (this.currentLang === "debug"
                ? {
                    code: "debug",
                    native: "Debug",
                    en: "Debug",
                    svg: "xx",
                }
                : {
                    native: "English",
                    en: "English",
                    svg: "uk_us_flag",
                });
            return (0, lit_1.html) `
      <div class="container__row">
        <button
          id="lang-selector"
          @click=${this.openModal}
          class="text-center appearance-none w-full bg-blue-100 dark:bg-gray-700 hover:bg-blue-200 dark:hover:bg-gray-600 text-blue-900 dark:text-gray-100 p-3 sm:p-4 lg:p-5 font-medium text-sm sm:text-base lg:text-lg rounded-md border-none cursor-pointer transition-colors duration-300 flex items-center gap-2 justify-center"
        >
          <img
            id="lang-flag"
            class="w-6 h-4"
            src="/flags/${currentLang.svg}.svg"
            alt="flag"
          />
          <span id="lang-name">${currentLang.native} (${currentLang.en})</span>
        </button>
      </div>

      <language-modal
        .visible=${this.showModal}
        .languageList=${this.languageList}
        .currentLang=${this.currentLang}
        @language-selected=${(e) => this.changeLanguage(e.detail.lang)}
        @close-modal=${() => (this.showModal = false)}
      ></language-modal>
    `;
        }
    };
    __setFunctionName(_classThis, "LangSelector");
    (() => {
        var _a;
        const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create((_a = _classSuper[Symbol.metadata]) !== null && _a !== void 0 ? _a : null) : void 0;
        _translations_decorators = [(0, decorators_js_1.state)()];
        _defaultTranslations_decorators = [(0, decorators_js_1.state)()];
        _currentLang_decorators = [(0, decorators_js_1.state)()];
        _languageList_decorators = [(0, decorators_js_1.state)()];
        _showModal_decorators = [(0, decorators_js_1.state)()];
        _debugMode_decorators = [(0, decorators_js_1.state)()];
        __esDecorate(null, null, _translations_decorators, { kind: "field", name: "translations", static: false, private: false, access: { has: obj => "translations" in obj, get: obj => obj.translations, set: (obj, value) => { obj.translations = value; } }, metadata: _metadata }, _translations_initializers, _translations_extraInitializers);
        __esDecorate(null, null, _defaultTranslations_decorators, { kind: "field", name: "defaultTranslations", static: false, private: false, access: { has: obj => "defaultTranslations" in obj, get: obj => obj.defaultTranslations, set: (obj, value) => { obj.defaultTranslations = value; } }, metadata: _metadata }, _defaultTranslations_initializers, _defaultTranslations_extraInitializers);
        __esDecorate(null, null, _currentLang_decorators, { kind: "field", name: "currentLang", static: false, private: false, access: { has: obj => "currentLang" in obj, get: obj => obj.currentLang, set: (obj, value) => { obj.currentLang = value; } }, metadata: _metadata }, _currentLang_initializers, _currentLang_extraInitializers);
        __esDecorate(null, null, _languageList_decorators, { kind: "field", name: "languageList", static: false, private: false, access: { has: obj => "languageList" in obj, get: obj => obj.languageList, set: (obj, value) => { obj.languageList = value; } }, metadata: _metadata }, _languageList_initializers, _languageList_extraInitializers);
        __esDecorate(null, null, _showModal_decorators, { kind: "field", name: "showModal", static: false, private: false, access: { has: obj => "showModal" in obj, get: obj => obj.showModal, set: (obj, value) => { obj.showModal = value; } }, metadata: _metadata }, _showModal_initializers, _showModal_extraInitializers);
        __esDecorate(null, null, _debugMode_decorators, { kind: "field", name: "debugMode", static: false, private: false, access: { has: obj => "debugMode" in obj, get: obj => obj.debugMode, set: (obj, value) => { obj.debugMode = value; } }, metadata: _metadata }, _debugMode_initializers, _debugMode_extraInitializers);
        __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
        LangSelector = _classThis = _classDescriptor.value;
        if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
        __runInitializers(_classThis, _classExtraInitializers);
    })();
    return LangSelector = _classThis;
})();
exports.LangSelector = LangSelector;
function flattenTranslations(obj, parentKey = "", result = {}) {
    for (const key in obj) {
        const value = obj[key];
        const fullKey = parentKey ? `${parentKey}.${key}` : key;
        if (typeof value === "string") {
            result[fullKey] = value;
        }
        else if (value && typeof value === "object" && !Array.isArray(value)) {
            flattenTranslations(value, fullKey, result);
        }
        else {
            console.warn("Unknown type", typeof value, value);
        }
    }
    return result;
}
