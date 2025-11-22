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
var __setFunctionName = (this && this.__setFunctionName) || function (f, name, prefix) {
    if (typeof name === "symbol") name = name.description ? "[".concat(name.description, "]") : "";
    return Object.defineProperty(f, "name", { configurable: true, value: prefix ? "".concat(prefix, " ", name) : name });
};
import { LitElement, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import "./LanguageModal";
import ar from "../../resources/lang/ar.json";
import bg from "../../resources/lang/bg.json";
import bn from "../../resources/lang/bn.json";
import cs from "../../resources/lang/cs.json";
import da from "../../resources/lang/da.json";
import de from "../../resources/lang/de.json";
import en from "../../resources/lang/en.json";
import eo from "../../resources/lang/eo.json";
import es from "../../resources/lang/es.json";
import fi from "../../resources/lang/fi.json";
import fr from "../../resources/lang/fr.json";
import gl from "../../resources/lang/gl.json";
import he from "../../resources/lang/he.json";
import hi from "../../resources/lang/hi.json";
import hu from "../../resources/lang/hu.json";
import it from "../../resources/lang/it.json";
import ja from "../../resources/lang/ja.json";
import ko from "../../resources/lang/ko.json";
import nl from "../../resources/lang/nl.json";
import pl from "../../resources/lang/pl.json";
import pt_BR from "../../resources/lang/pt-BR.json";
import pt_PT from "../../resources/lang/pt-PT.json";
import ru from "../../resources/lang/ru.json";
import sh from "../../resources/lang/sh.json";
import sk from "../../resources/lang/sk.json";
import sl from "../../resources/lang/sl.json";
import sv_SE from "../../resources/lang/sv-SE.json";
import tp from "../../resources/lang/tp.json";
import tr from "../../resources/lang/tr.json";
import uk from "../../resources/lang/uk.json";
import zh_CN from "../../resources/lang/zh-CN.json";
let LangSelector = (() => {
    let _classDecorators = [customElement("lang-selector")];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _classSuper = LitElement;
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
                ar,
                bg,
                bn,
                de,
                en,
                es,
                eo,
                fr,
                it,
                hi,
                hu,
                ja,
                nl,
                pl,
                "pt-PT": pt_PT,
                "pt-BR": pt_BR,
                ru,
                sh,
                tr,
                tp,
                uk,
                cs,
                he,
                da,
                fi,
                "sv-SE": sv_SE,
                "zh-CN": zh_CN,
                ko,
                gl,
                sl,
                sk,
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
                if (e.key?.toLowerCase() === "t")
                    this.debugKeyPressed = true;
            });
            window.addEventListener("keyup", (e) => {
                if (e.key?.toLowerCase() === "t")
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
        async initializeLanguage() {
            const browserLocale = navigator.language;
            const savedLang = localStorage.getItem("lang");
            const userLang = this.getClosestSupportedLang(savedLang ?? browserLocale);
            this.defaultTranslations = this.loadLanguage("en");
            this.translations = this.loadLanguage(userLang);
            this.currentLang = userLang;
            await this.loadLanguageList();
            this.applyTranslation();
        }
        loadLanguage(lang) {
            const language = this.languageMap[lang] ?? {};
            const flat = flattenTranslations(language);
            return flat;
        }
        async loadLanguageList() {
            try {
                const data = this.languageMap;
                let list = [];
                const browserLang = new Intl.Locale(navigator.language).language;
                for (const langCode of Object.keys(data)) {
                    const langData = data[langCode].lang;
                    if (!langData)
                        continue;
                    list.push({
                        code: langData.lang_code ?? langCode,
                        native: langData.native ?? langCode,
                        en: langData.en ?? langCode,
                        svg: langData.svg ?? langCode,
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
        }
        changeLanguage(lang) {
            localStorage.setItem("lang", lang);
            this.translations = this.loadLanguage(lang);
            this.currentLang = lang;
            this.applyTranslation();
            this.showModal = false;
        }
        applyTranslation() {
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
            document.title = this.translateText("main.title") ?? document.title;
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
            const currentLang = this.languageList.find((l) => l.code === this.currentLang) ??
                (this.currentLang === "debug"
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
            return html `
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
        const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(_classSuper[Symbol.metadata] ?? null) : void 0;
        _translations_decorators = [state()];
        _defaultTranslations_decorators = [state()];
        _currentLang_decorators = [state()];
        _languageList_decorators = [state()];
        _showModal_decorators = [state()];
        _debugMode_decorators = [state()];
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
export { LangSelector };
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
