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
var __setFunctionName = (this && this.__setFunctionName) || function (f, name, prefix) {
    if (typeof name === "symbol") name = name.description ? "[".concat(name.description, "]") : "";
    return Object.defineProperty(f, "name", { configurable: true, value: prefix ? "".concat(prefix, " ", name) : name });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LanguageModal = void 0;
const lit_1 = require("lit");
const decorators_js_1 = require("lit/decorators.js");
const Utils_1 = require("../client/Utils");
let LanguageModal = (() => {
    let _classDecorators = [(0, decorators_js_1.customElement)("language-modal")];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _classSuper = lit_1.LitElement;
    let _visible_decorators;
    let _visible_initializers = [];
    let _visible_extraInitializers = [];
    let _languageList_decorators;
    let _languageList_initializers = [];
    let _languageList_extraInitializers = [];
    let _currentLang_decorators;
    let _currentLang_initializers = [];
    let _currentLang_extraInitializers = [];
    var LanguageModal = _classThis = class extends _classSuper {
        constructor() {
            super(...arguments);
            this.visible = __runInitializers(this, _visible_initializers, false);
            this.languageList = (__runInitializers(this, _visible_extraInitializers), __runInitializers(this, _languageList_initializers, []));
            this.currentLang = (__runInitializers(this, _languageList_extraInitializers), __runInitializers(this, _currentLang_initializers, "en"));
            this.close = (__runInitializers(this, _currentLang_extraInitializers), () => {
                this.dispatchEvent(new CustomEvent("close-modal", {
                    bubbles: true,
                    composed: true,
                }));
            });
            this.handleKeyDown = (e) => {
                if (e.code === "Escape") {
                    e.preventDefault();
                    this.close();
                }
            };
            this.selectLanguage = (lang) => {
                this.dispatchEvent(new CustomEvent("language-selected", {
                    detail: { lang },
                    bubbles: true,
                    composed: true,
                }));
            };
        }
        createRenderRoot() {
            return this; // Use Light DOM for TailwindCSS classes
        }
        updated(changedProps) {
            if (changedProps.has("visible")) {
                if (this.visible) {
                    document.body.style.overflow = "hidden";
                }
                else {
                    document.body.style.overflow = "auto";
                }
            }
        }
        connectedCallback() {
            super.connectedCallback();
            window.addEventListener("keydown", this.handleKeyDown);
        }
        disconnectedCallback() {
            super.disconnectedCallback();
            window.removeEventListener("keydown", this.handleKeyDown);
            document.body.style.overflow = "auto";
        }
        render() {
            if (!this.visible)
                return null;
            return (0, lit_1.html) `
      <aside
        class="fixed p-4 z-[1000] inset-0 bg-black/50 overflow-y-auto flex items-center justify-center"
      >
        <div
          class="bg-gray-800/80 dark:bg-gray-900/90 backdrop-blur-md rounded-lg min-w-[340px] max-w-[480px] w-full"
        >
          <header
            class="relative rounded-t-md text-lg bg-black/60 dark:bg-black/80 text-center text-white px-6 py-4 pr-10"
          >
            ${(0, Utils_1.translateText)("select_lang.title")}
            <div
              class="cursor-pointer absolute right-4 top-4 font-bold hover:text-gray-300"
              @click=${this.close}
            >
              ✕
            </div>
          </header>

          <section
            class="relative text-white dark:text-gray-100 p-6 max-h-[60dvh] overflow-y-auto"
          >
            ${this.languageList.map((lang) => {
                const isActive = this.currentLang === lang.code;
                const isDebug = lang.code === "debug";
                let buttonClasses = "w-full flex items-center gap-2 p-2 mb-2 rounded-md transition-colors duration-300 border";
                if (isDebug) {
                    buttonClasses +=
                        " animate-pulse font-bold text-white border-2 border-dashed border-cyan-400 shadow-lg shadow-cyan-400/25 bg-gradient-to-r from-red-600 via-yellow-600 via-green-600 via-blue-600 to-purple-600";
                }
                else if (isActive) {
                    buttonClasses +=
                        " bg-gray-400 dark:bg-gray-500 border-gray-300 dark:border-gray-400 text-black dark:text-white";
                }
                else {
                    buttonClasses +=
                        " bg-gray-600 dark:bg-gray-700 border-gray-500 dark:border-gray-600 text-white dark:text-gray-100 hover:bg-gray-500 dark:hover:bg-gray-600";
                }
                return (0, lit_1.html) `
                <button
                  class="${buttonClasses}"
                  @click=${() => this.selectLanguage(lang.code)}
                >
                  <img
                    src="/flags/${lang.svg}.svg"
                    class="w-6 h-4 object-contain"
                    alt="${lang.code}"
                  />
                  <span>${lang.native} (${lang.en})</span>
                </button>
              `;
            })}
          </section>
        </div>
      </aside>
    `;
        }
    };
    __setFunctionName(_classThis, "LanguageModal");
    (() => {
        var _a;
        const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create((_a = _classSuper[Symbol.metadata]) !== null && _a !== void 0 ? _a : null) : void 0;
        _visible_decorators = [(0, decorators_js_1.property)({ type: Boolean })];
        _languageList_decorators = [(0, decorators_js_1.property)({ type: Array })];
        _currentLang_decorators = [(0, decorators_js_1.property)({ type: String })];
        __esDecorate(null, null, _visible_decorators, { kind: "field", name: "visible", static: false, private: false, access: { has: obj => "visible" in obj, get: obj => obj.visible, set: (obj, value) => { obj.visible = value; } }, metadata: _metadata }, _visible_initializers, _visible_extraInitializers);
        __esDecorate(null, null, _languageList_decorators, { kind: "field", name: "languageList", static: false, private: false, access: { has: obj => "languageList" in obj, get: obj => obj.languageList, set: (obj, value) => { obj.languageList = value; } }, metadata: _metadata }, _languageList_initializers, _languageList_extraInitializers);
        __esDecorate(null, null, _currentLang_decorators, { kind: "field", name: "currentLang", static: false, private: false, access: { has: obj => "currentLang" in obj, get: obj => obj.currentLang, set: (obj, value) => { obj.currentLang = value; } }, metadata: _metadata }, _currentLang_initializers, _currentLang_extraInitializers);
        __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
        LanguageModal = _classThis = _classDescriptor.value;
        if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
        __runInitializers(_classThis, _classExtraInitializers);
    })();
    return LanguageModal = _classThis;
})();
exports.LanguageModal = LanguageModal;
