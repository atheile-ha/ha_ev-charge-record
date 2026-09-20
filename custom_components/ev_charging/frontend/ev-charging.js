/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ie = globalThis, be = ie.ShadowRoot && (ie.ShadyCSS === void 0 || ie.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, we = Symbol(), Ue = /* @__PURE__ */ new WeakMap();
let Ye = class {
  constructor(e, t, s) {
    if (this._$cssResult$ = !0, s !== we) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (be && e === void 0) {
      const s = t !== void 0 && t.length === 1;
      s && (e = Ue.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), s && Ue.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const ct = (r) => new Ye(typeof r == "string" ? r : r + "", void 0, we), b = (r, ...e) => {
  const t = r.length === 1 ? r[0] : e.reduce((s, i, n) => s + ((a) => {
    if (a._$cssResult$ === !0) return a.cssText;
    if (typeof a == "number") return a;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + a + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + r[n + 1], r[0]);
  return new Ye(t, r, we);
}, dt = (r, e) => {
  if (be) r.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const s = document.createElement("style"), i = ie.litNonce;
    i !== void 0 && s.setAttribute("nonce", i), s.textContent = t.cssText, r.appendChild(s);
  }
}, Oe = be ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const s of e.cssRules) t += s.cssText;
  return ct(t);
})(r) : r;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: ht, defineProperty: ut, getOwnPropertyDescriptor: pt, getOwnPropertyNames: _t, getOwnPropertySymbols: ft, getPrototypeOf: gt } = Object, he = globalThis, Re = he.trustedTypes, mt = Re ? Re.emptyScript : "", vt = he.reactiveElementPolyfillSupport, K = (r, e) => r, ae = { toAttribute(r, e) {
  switch (e) {
    case Boolean:
      r = r ? mt : null;
      break;
    case Object:
    case Array:
      r = r == null ? r : JSON.stringify(r);
  }
  return r;
}, fromAttribute(r, e) {
  let t = r;
  switch (e) {
    case Boolean:
      t = r !== null;
      break;
    case Number:
      t = r === null ? null : Number(r);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(r);
      } catch {
        t = null;
      }
  }
  return t;
} }, xe = (r, e) => !ht(r, e), Ne = { attribute: !0, type: String, converter: ae, reflect: !1, useDefault: !1, hasChanged: xe };
Symbol.metadata ??= Symbol("metadata"), he.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let I = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ??= []).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Ne) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const s = Symbol(), i = this.getPropertyDescriptor(e, s, t);
      i !== void 0 && ut(this.prototype, e, i);
    }
  }
  static getPropertyDescriptor(e, t, s) {
    const { get: i, set: n } = pt(this.prototype, e) ?? { get() {
      return this[t];
    }, set(a) {
      this[t] = a;
    } };
    return { get: i, set(a) {
      const l = i?.call(this);
      n?.call(this, a), this.requestUpdate(e, l, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Ne;
  }
  static _$Ei() {
    if (this.hasOwnProperty(K("elementProperties"))) return;
    const e = gt(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(K("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(K("properties"))) {
      const t = this.properties, s = [..._t(t), ...ft(t)];
      for (const i of s) this.createProperty(i, t[i]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [s, i] of t) this.elementProperties.set(s, i);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, s] of this.elementProperties) {
      const i = this._$Eu(t, s);
      i !== void 0 && this._$Eh.set(i, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const s = new Set(e.flat(1 / 0).reverse());
      for (const i of s) t.unshift(Oe(i));
    } else e !== void 0 && t.push(Oe(e));
    return t;
  }
  static _$Eu(e, t) {
    const s = t.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
  }
  addController(e) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
  }
  removeController(e) {
    this._$EO?.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
    for (const s of t.keys()) this.hasOwnProperty(s) && (e.set(s, this[s]), delete this[s]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return dt(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((e) => e.hostDisconnected?.());
  }
  attributeChangedCallback(e, t, s) {
    this._$AK(e, s);
  }
  _$ET(e, t) {
    const s = this.constructor.elementProperties.get(e), i = this.constructor._$Eu(e, s);
    if (i !== void 0 && s.reflect === !0) {
      const n = (s.converter?.toAttribute !== void 0 ? s.converter : ae).toAttribute(t, s.type);
      this._$Em = e, n == null ? this.removeAttribute(i) : this.setAttribute(i, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const s = this.constructor, i = s._$Eh.get(e);
    if (i !== void 0 && this._$Em !== i) {
      const n = s.getPropertyOptions(i), a = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : ae;
      this._$Em = i;
      const l = a.fromAttribute(t, n.type);
      this[i] = l ?? this._$Ej?.get(i) ?? l, this._$Em = null;
    }
  }
  requestUpdate(e, t, s, i = !1, n) {
    if (e !== void 0) {
      const a = this.constructor;
      if (i === !1 && (n = this[e]), s ??= a.getPropertyOptions(e), !((s.hasChanged ?? xe)(n, t) || s.useDefault && s.reflect && n === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, s)))) return;
      this.C(e, t, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: s, reflect: i, wrapped: n }, a) {
    s && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, a ?? t ?? this[e]), n !== !0 || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || s || (t = void 0), this._$AL.set(e, t)), i === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [i, n] of this._$Ep) this[i] = n;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [i, n] of s) {
        const { wrapped: a } = n, l = this[i];
        a !== !0 || this._$AL.has(i) || l === void 0 || this.C(i, void 0, n, l);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((s) => s.hostUpdate?.()), this.update(t)) : this._$EM();
    } catch (s) {
      throw e = !1, this._$EM(), s;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    this._$EO?.forEach((t) => t.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq &&= this._$Eq.forEach((t) => this._$ET(t, this[t])), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
I.elementStyles = [], I.shadowRootOptions = { mode: "open" }, I[K("elementProperties")] = /* @__PURE__ */ new Map(), I[K("finalized")] = /* @__PURE__ */ new Map(), vt?.({ ReactiveElement: I }), (he.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Se = globalThis, ze = (r) => r, oe = Se.trustedTypes, De = oe ? oe.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, Ze = "$lit$", C = `lit$${Math.random().toFixed(9).slice(2)}$`, Ge = "?" + C, $t = `<${Ge}>`, z = document, Y = () => z.createComment(""), Z = (r) => r === null || typeof r != "object" && typeof r != "function", Ae = Array.isArray, yt = (r) => Ae(r) || typeof r?.[Symbol.iterator] == "function", ge = `[ 	
\f\r]`, q = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, He = /-->/g, Ie = />/g, R = RegExp(`>|${ge}(?:([^\\s"'>=/]+)(${ge}*=${ge}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Le = /'/g, Fe = /"/g, Je = /^(?:script|style|textarea|title)$/i, bt = (r) => (e, ...t) => ({ _$litType$: r, strings: e, values: t }), o = bt(1), D = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), je = /* @__PURE__ */ new WeakMap(), N = z.createTreeWalker(z, 129);
function Xe(r, e) {
  if (!Ae(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return De !== void 0 ? De.createHTML(e) : e;
}
const wt = (r, e) => {
  const t = r.length - 1, s = [];
  let i, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", a = q;
  for (let l = 0; l < t; l++) {
    const c = r[l];
    let h, _, u = -1, x = 0;
    for (; x < c.length && (a.lastIndex = x, _ = a.exec(c), _ !== null); ) x = a.lastIndex, a === q ? _[1] === "!--" ? a = He : _[1] !== void 0 ? a = Ie : _[2] !== void 0 ? (Je.test(_[2]) && (i = RegExp("</" + _[2], "g")), a = R) : _[3] !== void 0 && (a = R) : a === R ? _[0] === ">" ? (a = i ?? q, u = -1) : _[1] === void 0 ? u = -2 : (u = a.lastIndex - _[2].length, h = _[1], a = _[3] === void 0 ? R : _[3] === '"' ? Fe : Le) : a === Fe || a === Le ? a = R : a === He || a === Ie ? a = q : (a = R, i = void 0);
    const E = a === R && r[l + 1].startsWith("/>") ? " " : "";
    n += a === q ? c + $t : u >= 0 ? (s.push(h), c.slice(0, u) + Ze + c.slice(u) + C + E) : c + C + (u === -2 ? l : E);
  }
  return [Xe(r, n + (r[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), s];
};
class G {
  constructor({ strings: e, _$litType$: t }, s) {
    let i;
    this.parts = [];
    let n = 0, a = 0;
    const l = e.length - 1, c = this.parts, [h, _] = wt(e, t);
    if (this.el = G.createElement(h, s), N.currentNode = this.el.content, t === 2 || t === 3) {
      const u = this.el.content.firstChild;
      u.replaceWith(...u.childNodes);
    }
    for (; (i = N.nextNode()) !== null && c.length < l; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const u of i.getAttributeNames()) if (u.endsWith(Ze)) {
          const x = _[a++], E = i.getAttribute(u).split(C), se = /([.?@])?(.*)/.exec(x);
          c.push({ type: 1, index: n, name: se[2], strings: E, ctor: se[1] === "." ? St : se[1] === "?" ? At : se[1] === "@" ? Et : ue }), i.removeAttribute(u);
        } else u.startsWith(C) && (c.push({ type: 6, index: n }), i.removeAttribute(u));
        if (Je.test(i.tagName)) {
          const u = i.textContent.split(C), x = u.length - 1;
          if (x > 0) {
            i.textContent = oe ? oe.emptyScript : "";
            for (let E = 0; E < x; E++) i.append(u[E], Y()), N.nextNode(), c.push({ type: 2, index: ++n });
            i.append(u[x], Y());
          }
        }
      } else if (i.nodeType === 8) if (i.data === Ge) c.push({ type: 2, index: n });
      else {
        let u = -1;
        for (; (u = i.data.indexOf(C, u + 1)) !== -1; ) c.push({ type: 7, index: n }), u += C.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const s = z.createElement("template");
    return s.innerHTML = e, s;
  }
}
function j(r, e, t = r, s) {
  if (e === D) return e;
  let i = s !== void 0 ? t._$Co?.[s] : t._$Cl;
  const n = Z(e) ? void 0 : e._$litDirective$;
  return i?.constructor !== n && (i?._$AO?.(!1), n === void 0 ? i = void 0 : (i = new n(r), i._$AT(r, t, s)), s !== void 0 ? (t._$Co ??= [])[s] = i : t._$Cl = i), i !== void 0 && (e = j(r, i._$AS(r, e.values), i, s)), e;
}
class xt {
  constructor(e, t) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: t }, parts: s } = this._$AD, i = (e?.creationScope ?? z).importNode(t, !0);
    N.currentNode = i;
    let n = N.nextNode(), a = 0, l = 0, c = s[0];
    for (; c !== void 0; ) {
      if (a === c.index) {
        let h;
        c.type === 2 ? h = new Q(n, n.nextSibling, this, e) : c.type === 1 ? h = new c.ctor(n, c.name, c.strings, this, e) : c.type === 6 && (h = new Ct(n, this, e)), this._$AV.push(h), c = s[++l];
      }
      a !== c?.index && (n = N.nextNode(), a++);
    }
    return N.currentNode = z, i;
  }
  p(e) {
    let t = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(e, s, t), t += s.strings.length - 2) : s._$AI(e[t])), t++;
  }
}
class Q {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, s, i) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = s, this.options = i, this._$Cv = i?.isConnected ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const t = this._$AM;
    return t !== void 0 && e?.nodeType === 11 && (e = t.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, t = this) {
    e = j(this, e, t), Z(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== D && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : yt(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && Z(this._$AH) ? this._$AA.nextSibling.data = e : this.T(z.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: s } = e, i = typeof s == "number" ? this._$AC(e) : (s.el === void 0 && (s.el = G.createElement(Xe(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === i) this._$AH.p(t);
    else {
      const n = new xt(i, this), a = n.u(this.options);
      n.p(t), this.T(a), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = je.get(e.strings);
    return t === void 0 && je.set(e.strings, t = new G(e)), t;
  }
  k(e) {
    Ae(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let s, i = 0;
    for (const n of e) i === t.length ? t.push(s = new Q(this.O(Y()), this.O(Y()), this, this.options)) : s = t[i], s._$AI(n), i++;
    i < t.length && (this._$AR(s && s._$AB.nextSibling, i), t.length = i);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const s = ze(e).nextSibling;
      ze(e).remove(), e = s;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class ue {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, s, i, n) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = e, this.name = t, this._$AM = i, this.options = n, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = d;
  }
  _$AI(e, t = this, s, i) {
    const n = this.strings;
    let a = !1;
    if (n === void 0) e = j(this, e, t, 0), a = !Z(e) || e !== this._$AH && e !== D, a && (this._$AH = e);
    else {
      const l = e;
      let c, h;
      for (e = n[0], c = 0; c < n.length - 1; c++) h = j(this, l[s + c], t, c), h === D && (h = this._$AH[c]), a ||= !Z(h) || h !== this._$AH[c], h === d ? e = d : e !== d && (e += (h ?? "") + n[c + 1]), this._$AH[c] = h;
    }
    a && !i && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class St extends ue {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class At extends ue {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class Et extends ue {
  constructor(e, t, s, i, n) {
    super(e, t, s, i, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = j(this, e, t, 0) ?? d) === D) return;
    const s = this._$AH, i = e === d && s !== d || e.capture !== s.capture || e.once !== s.once || e.passive !== s.passive, n = e !== d && (s === d || i);
    i && this.element.removeEventListener(this.name, this, s), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Ct {
  constructor(e, t, s) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    j(this, e);
  }
}
const kt = Se.litHtmlPolyfillSupport;
kt?.(G, Q), (Se.litHtmlVersions ??= []).push("3.3.3");
const Tt = (r, e, t) => {
  const s = t?.renderBefore ?? e;
  let i = s._$litPart$;
  if (i === void 0) {
    const n = t?.renderBefore ?? null;
    s._$litPart$ = i = new Q(e.insertBefore(Y(), n), n, void 0, t ?? {});
  }
  return i._$AI(r), i;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ee = globalThis;
let v = class extends I {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const e = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= e.firstChild, e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Tt(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return D;
  }
};
v._$litElement$ = !0, v.finalized = !0, Ee.litElementHydrateSupport?.({ LitElement: v });
const Pt = Ee.litElementPolyfillSupport;
Pt?.({ LitElement: v });
(Ee.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Mt = { attribute: !0, type: String, converter: ae, reflect: !1, hasChanged: xe }, Ut = (r = Mt, e, t) => {
  const { kind: s, metadata: i } = t;
  let n = globalThis.litPropertyMetadata.get(i);
  if (n === void 0 && globalThis.litPropertyMetadata.set(i, n = /* @__PURE__ */ new Map()), s === "setter" && ((r = Object.create(r)).wrapped = !0), n.set(t.name, r), s === "accessor") {
    const { name: a } = t;
    return { set(l) {
      const c = e.get.call(this);
      e.set.call(this, l), this.requestUpdate(a, c, r, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(a, void 0, r, l), l;
    } };
  }
  if (s === "setter") {
    const { name: a } = t;
    return function(l) {
      const c = this[a];
      e.call(this, l), this.requestUpdate(a, c, r, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function g(r) {
  return (e, t) => typeof t == "object" ? Ut(r, e, t) : ((s, i, n) => {
    const a = i.hasOwnProperty(n);
    return i.constructor.createProperty(n, s), a ? Object.getOwnPropertyDescriptor(i, n) : void 0;
  })(r, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function p(r) {
  return g({ ...r, state: !0, attribute: !1 });
}
const m = "–";
function T(r, e, t) {
  return new Intl.NumberFormat(e, {
    minimumFractionDigits: t,
    maximumFractionDigits: t
  }).format(r);
}
function $(r, e, t = !1) {
  return r === null ? m : `${t ? "~" : ""}${T(r, e, 3)} kWh`;
}
function Ve(r, e, t = !1) {
  return r === null ? m : `${t ? "~" : ""}${T(r, e, 0)} kWh`;
}
function We(r, e, t) {
  if (r === null)
    return m;
  try {
    return new Intl.NumberFormat(e, {
      style: "currency",
      currency: t,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(r);
  } catch {
    return `${T(r, e, 0)} ${t}`;
  }
}
function Be(r) {
  if (r === null)
    return m;
  const e = Math.round(r);
  return e < 60 ? `${e} min` : `${Math.round(e / 60)} h`;
}
function V(r, e, t) {
  if (r === null)
    return m;
  try {
    return new Intl.NumberFormat(e, { style: "currency", currency: t }).format(r);
  } catch {
    return `${T(r, e, 2)} ${t}`;
  }
}
function Ot(r, e, t) {
  if (r === null)
    return m;
  try {
    return `${new Intl.NumberFormat(e, {
      style: "currency",
      currency: t,
      minimumFractionDigits: 3,
      maximumFractionDigits: 4
    }).format(r)} / kWh`;
  } catch {
    return `${T(r, e, 4)} ${t} / kWh`;
  }
}
function S(r) {
  if (r === null)
    return m;
  const e = Math.round(r);
  if (e < 60)
    return `${e} min`;
  const t = Math.floor(e / 60), s = String(e % 60).padStart(2, "0");
  return `${t}:${s} h`;
}
function k(r, e) {
  return r === null ? m : `${T(r, e, 0)} %`;
}
function Rt(r, e) {
  return r === null ? m : `${T(r, e, 0)} km`;
}
function Qe(r, e) {
  return r === null ? m : `${T(r, e, 1)} kW`;
}
function J(r, e, t) {
  return r === null ? m : new Intl.DateTimeFormat(e, {
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: t
  }).format(new Date(r));
}
function le(r, e, t) {
  return r === null ? m : new Intl.DateTimeFormat(e, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: t
  }).format(new Date(r));
}
function me(r, e, t) {
  return new Intl.DateTimeFormat(e, { month: t, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, r - 1, 1))
  );
}
const Nt = "component.ev_charging.selector.panel.options.";
function H(r) {
  return (e, t) => {
    const s = r[Nt + e];
    return s === void 0 ? e : t ? s.replace(
      /\{(\w+)\}/g,
      (i, n) => n in t ? String(t[n]) : i
    ) : s;
  };
}
const ve = /* @__PURE__ */ new Map();
function ee(r) {
  const e = r.language;
  let t = ve.get(e);
  return t === void 0 && (t = r.callWS({
    type: "frontend/get_translations",
    language: e,
    category: "selector",
    integration: ["ev_charging"]
  }).then((s) => H(s.resources)), t.catch(() => ve.delete(e)), ve.set(e, t)), t;
}
const et = 6e4;
function zt(r, e, t) {
  if (r.net_duration_min === null)
    return null;
  const s = r.state === "charging";
  return r.net_duration_min + (s ? (t - e) / et : 0);
}
function Dt(r, e) {
  return r.session_start === null ? null : Math.max((e - new Date(r.session_start).getTime()) / et, 0);
}
function Ht(r) {
  const e = r.energy_grid_kwh, t = r.energy_solar_kwh;
  return e === null || t === null || e + t <= 0 ? null : t / (e + t) * 100;
}
function It(r) {
  let e = 0, t = 0;
  for (const s of r)
    s.energy_grid_kwh !== null && s.energy_solar_kwh !== null && (e += s.energy_grid_kwh, t += s.energy_solar_kwh);
  return e + t > 0 ? t / (e + t) * 100 : null;
}
function ye(r, e) {
  const t = (s) => new Intl.DateTimeFormat("en-CA", {
    timeZone: e.timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(s);
  return t(new Date(r).getTime()) === t(e.now) ? le(r, e.locale, e.timeZone) : J(r, e.locale, e.timeZone);
}
function Lt(r, e) {
  switch (r.plug.state) {
    case "not_connected":
      return e("live_idle_not_connected");
    case "unavailable":
      return e("live_idle_plug_unavailable");
    default:
      return e("live_idle");
  }
}
function Ft(r, e, t) {
  const s = r.state_since === null ? null : ye(r.state_since, t);
  switch (r.state) {
    case "candidate":
      return e("live_status_candidate");
    case "charging":
      return s === null ? e("live_state_charging") : e("live_status_charging", { time: s });
    case "paused":
      return r.waiting_for_power ? e("live_status_waiting_for_power") : s === null ? e("live_status_paused") : e("live_status_paused_since", { time: s });
    case "error":
      return s === null ? e("live_state_error") : e("live_status_error", { time: s });
    case "awaiting_final":
      return e("live_status_awaiting_final");
    default:
      return e("live_idle");
  }
}
function jt(r, e) {
  return r.phase_count === 0 ? null : r.phase_count === 1 ? e("live_phase_one") : e("live_phase_other", { count: r.phase_count });
}
function Vt(r, e, t) {
  const { plug: s } = r;
  switch (s.state) {
    case "connected":
      return e("live_plug_connected");
    case "not_connected":
      return e("live_plug_not_connected");
    default:
      return s.unavailable_since !== null && s.timeout_at !== null ? e("live_plug_unavailable_timeout", {
        since: ye(s.unavailable_since, t),
        timeout: ye(s.timeout_at, t)
      }) : e("live_plug_unavailable");
  }
}
function Wt(r, e) {
  return r.vehicle_guest ? e("live_vehicle_guest") : r.vehicle !== null ? r.vehicle.name : r.identification_decided ? e("unassigned") : e("live_assign_detecting");
}
const Bt = {
  rfid: "identification_rfid",
  emaid: "identification_emaid",
  vehicle_api: "identification_vehicle_api",
  manual: "identification_manual"
};
function qt(r, e) {
  const t = r.identification_source;
  if (!r.identification_decided || r.vehicle === null || t === null)
    return null;
  const s = Bt[t];
  return s === void 0 ? null : e("live_assign_via", { source: e(s) });
}
function Kt(r, e) {
  const t = r.identification_read;
  if (t === null)
    return null;
  switch (t.state) {
    case "reading":
      return e("live_read_reading", {
        sequence: t.sequence,
        attempt: t.attempt,
        max: t.max_attempts
      });
    case "waiting":
      return e("live_read_waiting");
    case "read":
      return e("live_read_done");
    default:
      return e("live_read_unreadable");
  }
}
function Yt(r, e) {
  const { authoritative: t, switched: s } = r.counter;
  if (t === null)
    return null;
  const i = e(t === "total" ? "live_counter_total" : "live_counter_session");
  return s ? e("live_counter_switched", { counter: i }) : e("live_counter", { counter: i });
}
function Zt(r, e, t) {
  const s = r.energy_unallocated_kwh;
  return s === null || s <= 0 ? null : e("live_unallocated", { energy: $(s, t) });
}
function Gt(r, e) {
  return {
    split: r.energy_grid_kwh === null && !r.sources.grid_balance ? e("live_missing_split") : null,
    cost: r.cost === null && !r.sources.grid_price ? e("live_missing_cost") : null
  };
}
const P = b`
  :host {
    color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, inherit);
    --ev-muted: var(--secondary-text-color);
    --ev-line: var(--divider-color, rgba(127, 127, 127, 0.3));
    --ev-surface: var(--card-background-color, var(--ha-card-background, #fff));
    --ev-radius: var(--ha-card-border-radius, 12px);
    --ev-accent: var(--primary-color, #03a9f4);
    --ev-head-bg: color-mix(in srgb, var(--primary-text-color, #000) 5%, transparent);
  }

  * {
    box-sizing: border-box;
  }

  .muted {
    color: var(--ev-muted);
  }

  .spinner {
    width: 28px;
    height: 28px;
    margin: 32px auto;
    border: 3px solid var(--ev-line);
    border-top-color: var(--ev-accent);
    border-radius: 50%;
    animation: ev-spin 0.9s linear infinite;
  }

  @keyframes ev-spin {
    to {
      transform: rotate(360deg);
    }
  }

  .message {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 24px 8px;
    color: var(--ev-muted);
    text-align: center;
  }

  button,
  select {
    font: inherit;
    color: inherit;
  }

  select {
    max-width: 100%;
    padding: 6px 8px;
    background: var(--ev-surface);
    border: 1px solid var(--ev-line);
    border-radius: 8px;
  }

  button.text {
    padding: 6px 14px;
    background: transparent;
    border: 1px solid var(--ev-accent);
    border-radius: 8px;
    color: var(--ev-accent);
    cursor: pointer;
  }

  button:focus-visible,
  select:focus-visible,
  summary:focus-visible,
  a:focus-visible {
    outline: 2px solid var(--ev-accent);
    outline-offset: 2px;
  }

  .chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--ev-accent) 20%, transparent);
    color: var(--primary-text-color);
    font-size: 0.9em;
    font-weight: 500;
    line-height: 1.3;
    white-space: nowrap;
  }

  .chip.warn {
    background: var(--warning-color, #ff9800);
    color: #1b1b1b;
  }

  .chip.alert {
    background: var(--error-color, #db4437);
    color: #fff;
  }

  .vehicle.unassigned {
    color: var(--ev-muted);
    font-style: italic;
  }
`;
var Jt = Object.defineProperty, M = (r, e, t, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(e, t, i) || i);
  return i && Jt(e, t, i), i;
};
const Xt = "ev_charging/live/subscribe", Qt = 1e3;
class A extends v {
  constructor() {
    super(...arguments), this._config = {}, this._received = 0, this._now = Date.now(), this._failed = !1, this._noWallbox = !1, this._started = !1;
  }
  setConfig(e) {
    this._config = e;
  }
  getCardSize() {
    return 5;
  }
  static getStubConfig() {
    return {};
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => {
      this._live?.active && (this._now = Date.now());
    }, Qt), this.hass && this._started && this._subscribe(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._started);
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass));
  }
  async _start(e) {
    try {
      this._t = await ee(e);
    } catch (t) {
      console.error("ev_charging: loading translations failed", t), this._t = H({});
    }
    await this._subscribe(e);
  }
  async _subscribe(e) {
    this._release(), this._failed = !1, this._noWallbox = !1;
    const t = e.connection.subscribeMessage(
      (s) => {
        this._live = s, this._received = Date.now(), this._now = this._received;
      },
      { type: Xt }
    );
    this._unsubscribe = t;
    try {
      await t;
    } catch (s) {
      this._unsubscribe = void 0, s.code === "not_found" ? this._noWallbox = !0 : (console.error("ev_charging: subscribing to the live values failed", s), this._failed = !0);
    }
  }
  _release() {
    const e = this._unsubscribe;
    this._unsubscribe = void 0, e?.then(
      (t) => t(),
      () => {
      }
    );
  }
  _retry() {
    this.hass && this._subscribe(this.hass);
  }
  _row(e, t) {
    return o`<div class="row">
      <dt>${e}</dt>
      <dd>${t}</dd>
    </div>`;
  }
  _vehicle(e, t) {
    const s = !e.vehicle_guest && e.vehicle === null;
    return o`<div class="vehicle ${s ? "unassigned" : ""}">${Wt(e, t)}</div>`;
  }
  _format(e) {
    return {
      locale: e.locale?.language ?? e.language,
      timeZone: e.config.time_zone,
      now: this._now
    };
  }
  // The state of the session and where it came from: what it is doing, the plug,
  // the assignment and the reading of the identification.
  _status(e, t, s) {
    const i = jt(e, t), n = [
      qt(e, t),
      Vt(e, t, s),
      Kt(e, t)
    ].filter((a) => a !== null);
    return o`<div class="status">
      <div class="state">
        ${Ft(e, t, s)}${i === null ? d : o` · ${i}`}
      </div>
      ${n.map((a) => o`<div class="line">${a}</div>`)}
    </div>`;
  }
  // The data situation: which counter carries the energy, and energy that could
  // not be assigned.
  _situation(e, t, s) {
    const i = [Yt(e, t), Zt(e, t, s)].filter(
      (n) => n !== null
    );
    return i.length === 0 ? d : o`<div class="situation">${i.map((n) => o`<div>${n}</div>`)}</div>`;
  }
  _soc(e, t, s) {
    if (e.soc_start === null && e.soc === null)
      return d;
    const i = e.soc_start !== null && e.soc !== null ? `${k(e.soc_start, s)} → ${k(e.soc, s)}` : k(e.soc ?? e.soc_start, s), n = e.soc_target === null ? "" : ` (${t("live_soc_target", { target: e.soc_target })})`;
    return this._row(t("live_soc"), `${i}${n}`);
  }
  _flags(e, t) {
    const s = [];
    return e.charge_error && s.push(o`<span class="chip alert">${t("flag_charge_error")}</span>`), e.location_conflict && s.push(o`<span class="chip warn">${t("flag_location_conflict")}</span>`), e.identification_conflict && s.push(o`<span class="chip warn">${t("flag_identification_conflict")}</span>`), e.flagged && s.push(o`<span class="chip warn">${t("status_flagged")}</span>`), s.length === 0 ? d : o`<div class="flags">${s}</div>`;
  }
  _details(e, t, s) {
    const i = s.locale?.language ?? s.language, n = e.currency || s.config.currency, a = Ht(e), l = Gt(e, t), c = e.energy_grid_kwh === null || e.energy_solar_kwh === null ? l.split === null ? d : this._row(`${t("detail_energy_grid")} / ${t("detail_energy_solar")}`, l.split) : this._row(
      `${t("detail_energy_grid")} / ${t("detail_energy_solar")}`,
      `${$(e.energy_grid_kwh, i)} / ${$(
        e.energy_solar_kwh,
        i
      )}${a === null ? "" : ` (${t("live_solar_share", { percent: Math.round(a) })})`}`
    ), h = e.effective_price === null ? d : this._row(
      t("live_price"),
      Ot(e.effective_price, i, n)
    ), _ = e.charge_end === null ? d : this._row(t("live_charge_end"), le(e.charge_end, i, s.config.time_zone));
    return o`<dl>
      ${this._soc(e, t, i)}
      ${this._row(t("live_power"), Qe(e.charge_power_kw, i))}
      ${this._row(t("live_energy"), $(e.energy_kwh, i))} ${c}
      ${this._row(t("live_cost"), l.cost ?? V(e.cost, i, n))} ${h}
      ${this._row(
      t("live_charge_time"),
      S(zt(e, this._received, this._now))
    )}
      ${this._row(t("live_plug_time"), S(Dt(e, this._now)))}
      ${_}
    </dl>`;
  }
  render() {
    const e = this._t, t = this.hass;
    if (!e || !t)
      return o`<div class="spinner" role="progressbar"></div>`;
    const s = this._config.title ?? e("live_title");
    if (this._noWallbox)
      return o`<h2>${s}</h2>
        <div class="message">${e("live_no_wallbox")}</div>`;
    if (this._failed)
      return o`<h2>${s}</h2>
        <div class="message">
          <span>${e("load_error")}</span>
          <button class="text" @click=${() => this._retry()}>${e("retry")}</button>
        </div>`;
    const i = this._live;
    if (i === void 0)
      return o`<h2>${s}</h2>
        <div class="spinner" role="progressbar"></div>`;
    if (!i.active)
      return o`<h2>${s}</h2>
        <div class="message">${Lt(i, e)}</div>`;
    const n = `live_state_${i.state}`;
    return o`
      <h2>
        <span>${s}</span>
        <span class="chip ${i.state === "error" ? "alert" : ""}"
          >${e(n)}</span
        >
      </h2>
      ${this._vehicle(i, e)} ${this._status(i, e, this._format(t))}
      ${this._details(i, e, t)}
      ${this._situation(i, e, t.locale?.language ?? t.language)} ${this._flags(i, e)}
    `;
  }
  static {
    this.styles = [
      P,
      b`
      :host {
        display: block;
        padding: 16px;
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border: var(--ha-card-border-width, 1px) solid
          var(--ha-card-border-color, var(--divider-color, transparent));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
      }

      h2 {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin: 0 0 8px;
        font-size: 1.1em;
        font-weight: 500;
      }

      .vehicle {
        margin-bottom: 8px;
        font-size: 1.3em;
        font-weight: 500;
      }

      .status {
        margin-bottom: 12px;
      }

      .status .state {
        font-weight: 500;
      }

      .status .line,
      .situation {
        color: var(--ev-muted);
        font-size: 0.9em;
      }

      .situation {
        margin-top: 12px;
      }

      dl {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 8px 16px;
        margin: 0;
      }

      .row {
        display: flex;
        flex-direction: column;
      }

      dt {
        color: var(--ev-muted);
        font-size: 0.85em;
      }

      dd {
        margin: 0;
        font-variant-numeric: tabular-nums;
      }

      .flags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 12px;
      }
    `
    ];
  }
}
M([
  g({ attribute: !1 })
], A.prototype, "hass");
M([
  p()
], A.prototype, "_config");
M([
  p()
], A.prototype, "_t");
M([
  p()
], A.prototype, "_live");
M([
  p()
], A.prototype, "_received");
M([
  p()
], A.prototype, "_now");
M([
  p()
], A.prototype, "_failed");
M([
  p()
], A.prototype, "_noWallbox");
async function Ce(r, e) {
  return (await r.callWS({
    type: "ev_charging/sessions/list",
    ...e
  })).sessions;
}
function er(r, e) {
  return r.callWS({ type: "ev_charging/sessions/list", year: e });
}
async function tr(r) {
  return (await r.callWS({
    type: "ev_charging/vehicles/list"
  })).vehicles;
}
const tt = "__unassigned__", ke = "__none__", ce = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: ""
};
function X(r, e) {
  const t = new Intl.DateTimeFormat("en-US", {
    timeZone: e,
    year: "numeric",
    month: "numeric"
  }).formatToParts(r), s = (i) => Number(t.find((n) => n.type === i)?.value ?? 0);
  return { year: s("year"), month: s("month") };
}
function rr(r, e) {
  return { view: "overview", ...X(r, e), filters: { ...ce } };
}
function sr(r, e, t) {
  const s = r * 12 + (e - 1) + t;
  return { year: Math.floor(s / 12), month: s % 12 + 1 };
}
const rt = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"]
];
function ir(r) {
  const e = new URLSearchParams({ year: String(r.year), month: String(r.month) });
  for (const [t, s] of rt)
    r.filters[t] !== "" && e.set(s, r.filters[t]);
  return `/${r.view}?${e.toString()}`;
}
function nr(r, e) {
  const t = {}, s = r.split("/").filter((h) => h !== "")[0];
  (s === "overview" || s === "detail" || s === "recent") && (t.view = s);
  const i = new URLSearchParams(e), n = Number(i.get("year")), a = Number(i.get("month"));
  Number.isInteger(n) && n >= 1e3 && n <= 9999 && Number.isInteger(a) && a >= 1 && a <= 12 && (t.year = n, t.month = a);
  const l = { ...ce };
  let c = !1;
  for (const [h, _] of rt) {
    const u = i.get(_);
    u && (l[h] = u, c = !0);
  }
  return c && (t.filters = l), t;
}
function $e(r) {
  const e = r.reduce((t, s) => t + (s ?? 0), 0);
  return Math.round(e * 1e4) / 1e4;
}
function F(r) {
  return {
    count: r.length,
    energy_kwh: $e(r.map((e) => e.energy_kwh)),
    energy_is_estimate: r.some((e) => e.energy_is_estimate),
    cost: $e(r.map((e) => e.cost)),
    charge_duration_min: $e(r.map((e) => e.charge_duration_min)),
    open_followups: r.filter(
      (e) => e.status === "followup_open" || e.open_fields.length > 0
    ).length
  };
}
function ar(r, e) {
  return X(new Date(r.plug_start), e).month;
}
function st(r, e, t) {
  return r.filter((s) => ar(s, t) === e);
}
function or(r, e) {
  return Array.from({ length: 12 }, (t, s) => ({
    month: s + 1,
    ...F(st(r, s + 1, e))
  }));
}
function lr(r) {
  const e = r.filter((s) => s.location === "external"), t = r.filter((s) => s.location !== "external");
  return {
    all: F(r),
    internal: F(t),
    external: F(e)
  };
}
function cr(r) {
  let e = null;
  return r.latitude !== null && r.longitude !== null ? e = `${r.latitude},${r.longitude}` : r.address && (e = r.address), e === null ? null : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(e)}`;
}
function dr(r) {
  return Object.values(r).some((e) => e !== "");
}
function qe(r, e) {
  return r.filter((t) => {
    if (e.vehicle === tt) {
      if (t.vehicle_id !== null) return !1;
    } else if (e.vehicle !== "" && t.vehicle_id !== e.vehicle)
      return !1;
    if (e.location !== "" && t.location !== e.location || e.chargeType !== "" && t.charge_type !== e.chargeType || e.status !== "" && t.status !== e.status) return !1;
    if (e.card === ke) {
      if (t.card_uid !== null) return !1;
    } else if (e.card !== "" && t.card_uid !== e.card)
      return !1;
    return !0;
  });
}
function hr(r, e) {
  const t = /* @__PURE__ */ new Map();
  for (const s of r)
    t.set(s.id, s.name);
  for (const s of e)
    s.vehicle_id !== null && !t.has(s.vehicle_id) && t.set(s.vehicle_id, s.vehicle_name ?? s.vehicle_id);
  return [...t].map(([s, i]) => ({ value: s, label: i }));
}
function ur(r, e, t) {
  const s = new Set(
    e.map((n) => n.card_uid).filter((n) => n !== null)
  ), i = /* @__PURE__ */ new Map();
  for (const n of r) {
    const a = [...s].find((l) => l !== "" && n.uid.endsWith(l));
    i.set(a ?? n.uid, n.label || n.uid);
  }
  for (const n of e)
    n.card_uid !== null && !i.has(n.card_uid) && i.set(n.card_uid, n.card_label || n.card_uid);
  return t !== "" && t !== ke && !i.has(t) && i.set(t, t), [...i].map(([n, a]) => ({ value: n, label: a }));
}
function pr(r, e, t) {
  return [.../* @__PURE__ */ new Set([...r, e, t])].sort((s, i) => i - s);
}
function _r(r) {
  return r.phases_recorded ? r.phases.length === 0 ? "detail_no_phases" : null : "detail_phases_not_recorded";
}
var fr = Object.defineProperty, te = (r, e, t, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(e, t, i) || i);
  return i && fr(e, t, i), i;
};
const gr = 600 * 1e3, mr = "ev_charging/live/subscribe";
class W extends v {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1, this._wasActive = !1;
  }
  setConfig(e) {
    this._config = e;
  }
  getCardSize() {
    return 3;
  }
  static getStubConfig() {
    return {};
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => {
      this.hass && this._started && !this._failed && this._load(this.hass, !0);
    }, gr), this.hass && this._started && this._watchSessions(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._started);
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass));
  }
  async _start(e) {
    try {
      this._t = await ee(e);
    } catch (t) {
      console.error("ev_charging: loading translations failed", t), this._t = H({}), this._failed = !0;
      return;
    }
    this._watchSessions(e), await this._load(e, !1);
  }
  // A running session ending changes the month, so it is worth a reload.
  _watchSessions(e) {
    this._release(), this._unsubscribe = e.connection.subscribeMessage(
      (t) => {
        this._wasActive && !t.active && this.hass && this._load(this.hass, !0), this._wasActive = t.active;
      },
      { type: mr }
    ), this._unsubscribe.catch(() => {
      this._unsubscribe = void 0;
    });
  }
  _release() {
    const e = this._unsubscribe;
    this._unsubscribe = void 0, e?.then(
      (t) => t(),
      () => {
      }
    );
  }
  async _load(e, t) {
    const { year: s, month: i } = X(/* @__PURE__ */ new Date(), e.config.time_zone);
    try {
      this._sessions = await Ce(e, { year: s, month: i }), this._failed = !1;
    } catch (n) {
      console.error("ev_charging: loading sessions failed", n), t || (this._failed = !0);
    }
  }
  _retry() {
    this.hass && (this._failed = !1, this._started = !1, this.requestUpdate());
  }
  _row(e, t) {
    return o`<div class="row">
      <dt>${e}</dt>
      <dd>${t}</dd>
    </div>`;
  }
  render() {
    const e = this._t, t = this.hass;
    if (!e || !t)
      return o`<div class="spinner" role="progressbar"></div>`;
    if (this._failed)
      return o`<div class="message">
        <span>${e("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${e("retry")}</button>
      </div>`;
    const s = t.locale?.language ?? t.language, { year: i, month: n } = X(/* @__PURE__ */ new Date(), t.config.time_zone), a = this._config.title ?? new Intl.DateTimeFormat(s, { month: "long", year: "numeric", timeZone: "UTC" }).format(
      new Date(Date.UTC(i, n - 1, 1))
    );
    if (this._sessions === void 0)
      return o`<h2>${a}</h2>
        <div class="spinner" role="progressbar"></div>`;
    const l = F(this._sessions), c = It(this._sessions);
    return o`
      <h2>${a}</h2>
      <dl>
        ${this._row(e("total_energy"), $(l.energy_kwh, s, l.energy_is_estimate))}
        ${this._row(e("total_cost"), V(l.cost, s, t.config.currency))}
        ${this._row(e("month_solar_share"), k(c, s))}
      </dl>
    `;
  }
  static {
    this.styles = [
      P,
      b`
      :host {
        display: block;
        padding: 16px;
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border: var(--ha-card-border-width, 1px) solid
          var(--ha-card-border-color, var(--divider-color, transparent));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
      }

      h2 {
        margin: 0 0 8px;
        font-size: 1.1em;
        font-weight: 500;
      }

      dl {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 8px 16px;
        margin: 0;
      }

      .row {
        display: flex;
        flex-direction: column;
      }

      dt {
        color: var(--ev-muted);
        font-size: 0.85em;
      }

      dd {
        margin: 0;
        font-size: 1.2em;
        font-variant-numeric: tabular-nums;
      }
    `
    ];
  }
}
te([
  g({ attribute: !1 })
], W.prototype, "hass");
te([
  p()
], W.prototype, "_config");
te([
  p()
], W.prototype, "_t");
te([
  p()
], W.prototype, "_sessions");
te([
  p()
], W.prototype, "_failed");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const vr = { ATTRIBUTE: 1 }, $r = (r) => (...e) => ({ _$litDirective$: r, values: e });
class yr {
  constructor(e) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(e, t, s) {
    this._$Ct = e, this._$AM = t, this._$Ci = s;
  }
  _$AS(e, t) {
    return this.update(e, t);
  }
  update(e, t) {
    return this.render(...t);
  }
}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ne = $r(class extends yr {
  constructor(r) {
    if (super(r), r.type !== vr.ATTRIBUTE || r.name !== "class" || r.strings?.length > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
  }
  render(r) {
    return " " + Object.keys(r).filter((e) => r[e]).join(" ") + " ";
  }
  update(r, [e]) {
    if (this.st === void 0) {
      this.st = /* @__PURE__ */ new Set(), r.strings !== void 0 && (this.nt = new Set(r.strings.join(" ").split(/\s/).filter((s) => s !== "")));
      for (const s in e) e[s] && !this.nt?.has(s) && this.st.add(s);
      return this.render(e);
    }
    const t = r.element.classList;
    for (const s of this.st) s in e || (t.remove(s), this.st.delete(s));
    for (const s in e) {
      const i = !!e[s];
      i === this.st.has(s) || this.nt?.has(s) || (i ? (t.add(s), this.st.add(s)) : (t.remove(s), this.st.delete(s)));
    }
    return D;
  }
});
function it(r, e) {
  return r.vehicle_id === null ? e("unassigned") : r.vehicle_name ?? r.vehicle_id;
}
const br = [
  "vehicle_id",
  "soc_start",
  "soc_end",
  "odometer_km",
  "energy_kwh",
  "energy_grid_kwh",
  "energy_solar_kwh",
  "cost",
  "address"
];
function wr(r) {
  return br.includes(r);
}
function xr(r, e) {
  return wr(r) ? e(`field_${r}`) : r;
}
const Sr = "M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z";
function f(r, e) {
  return e === null || e === "" || e === m ? d : o`<dt class="muted">${r}</dt>
    <dd>${e}</dd>`;
}
function Ar(r, e) {
  const t = cr(r);
  return r.address === null && t === null ? null : o`${r.address ?? d}${t === null ? d : o`<a
        class="map"
        href=${t}
        target="_blank"
        rel="noopener noreferrer"
        title=${e("detail_map_link")}
        aria-label=${e("detail_map_link")}
        ><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d=${Sr} fill="currentColor"></path></svg
        >${r.address === null ? e("detail_map_link") : d}</a
      >`}`;
}
function Er(r, e, t) {
  const s = _r(r);
  if (s !== null)
    return o`<p class="muted">${e(s)}</p>`;
  const i = t.locale.language, n = t.config.time_zone;
  return o`<table class="phases">
    <caption>
      ${e("detail_phases")}
    </caption>
    <thead>
      <tr>
        <th>${e("phase_start")}</th>
        <th>${e("phase_end")}</th>
        <th class="num">${e("phase_duration")}</th>
        <th class="num">${e("total_energy")}</th>
        <th class="num">${e("total_cost")}</th>
      </tr>
    </thead>
    <tbody>
      ${r.phases.map(
    (a) => o`<tr>
          <td>${le(a.start, i, n)}</td>
          <td>${le(a.end, i, n)}</td>
          <td class="num">${S(a.duration_min)}</td>
          <td class="num">${$(a.energy_kwh, i)}</td>
          <td class="num">${V(a.cost, i, t.config.currency)}</td>
        </tr>`
  )}
    </tbody>
  </table>`;
}
function nt(r, e, t) {
  const s = t.locale.language, i = t.config.time_zone, n = e("detail_not_recorded"), a = r.soc_start === null && r.soc_end === null ? null : `${k(r.soc_start, s)} → ${k(r.soc_end, s)}`;
  return o`<div class="body">
    <dl>
      ${f(e("detail_plug_start"), J(r.plug_start, s, i))}
      ${f(e("detail_plug_end"), J(r.plug_end, s, i))}
      ${f(e("detail_plug_duration"), S(r.plug_duration_min))}
      ${f(e("detail_charge_duration"), S(r.charge_duration_min))}
      ${r.pause_duration_min ? f(e("detail_pause_duration"), S(r.pause_duration_min)) : d}
      ${f(e("detail_soc"), a)}
      ${f(e("detail_odometer"), Rt(r.odometer_km, s))}
      ${f(e("detail_power_avg"), Qe(r.power_avg_kw, s))}
      ${r.location === "home" ? o`${f(
    e("detail_energy_grid"),
    r.energy_grid_kwh === null ? n : $(r.energy_grid_kwh, s)
  )}
          ${f(
    e("detail_energy_solar"),
    r.energy_solar_kwh === null ? n : $(r.energy_solar_kwh, s)
  )}` : d}
      ${r.energy_unallocated_kwh > 0 ? f(e("detail_energy_unallocated"), $(r.energy_unallocated_kwh, s)) : d}
      ${f(e("detail_card"), r.card_label ?? r.card_uid)}
      ${f(e("detail_identification"), e(`identification_${r.identification_source}`))}
      ${f(e("detail_address"), Ar(r, e))}
      ${f(e("detail_provider"), r.provider)}
      ${f(e("detail_note"), r.note)}
      ${r.open_fields.length > 0 ? f(
    e("detail_open_fields"),
    r.open_fields.map((l) => xr(l, e)).join(", ")
  ) : d}
    </dl>
    ${Er(r, e, t)}
  </div>`;
}
const at = b`
  .body {
    padding: 4px 14px 14px;
    background: var(--ev-head-bg);
    border-top: 1px solid var(--ev-line);
  }

  dl {
    display: grid;
    grid-template-columns: minmax(120px, max-content) 1fr;
    gap: 4px 16px;
    margin: 8px 0 0;
  }

  dd {
    margin: 0;
    overflow-wrap: anywhere;
  }

  .map {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-left: 6px;
    vertical-align: middle;
    color: var(--ev-accent);
    text-decoration: none;
  }

  .map:hover {
    text-decoration: underline;
  }

  .phases {
    width: 100%;
    margin-top: 12px;
    border-collapse: collapse;
    font-size: 0.9em;
  }

  .phases caption {
    padding-bottom: 4px;
    color: var(--ev-muted);
    text-align: left;
  }

  .phases th,
  .phases td {
    padding: 4px 8px 4px 0;
    text-align: left;
  }

  .phases .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
`;
var Cr = Object.defineProperty, Te = (r, e, t, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(e, t, i) || i);
  return i && Cr(e, t, i), i;
};
class pe extends v {
  constructor() {
    super(...arguments), this.sessions = [];
  }
  render() {
    const e = this.t;
    return !e || !this.hass ? d : o`<ul>
      ${this.sessions.map((t) => this._renderSession(t, e))}
    </ul>`;
  }
  _renderSession(e, t) {
    const s = this.hass, i = s.locale.language, n = e.soc_start !== null && e.soc_end !== null ? `${k(e.soc_start, i)} → ${k(e.soc_end, i)}` : d;
    return o`<li>
      <details>
        <summary>
          <div class="line">
            <span class=${ne({ vehicle: !0, unassigned: e.vehicle_id === null })}
              >${it(e, t)}</span
            >
            <span class="muted"
              >${J(e.plug_start, i, s.config.time_zone)}</span
            >
          </div>
          <div class="line">
            <span>
              ${$(e.energy_kwh, i, e.energy_is_estimate)} ·
              ${V(e.cost, i, s.config.currency)} ·
              ${S(e.charge_duration_min)}
            </span>
            <span class="muted">${n}</span>
          </div>
          <div class="line">
            <span class="chips">
              <span class="chip">${t(`location_${e.location}`)}</span>
              ${e.status === "complete" ? d : o`<span class="chip warn">${t(`status_${e.status}`)}</span>`}
            </span>
          </div>
        </summary>
        ${nt(e, t, s)}
      </details>
    </li>`;
  }
  static {
    this.styles = [
      P,
      at,
      b`
      :host {
        display: block;
      }

      ul {
        display: flex;
        flex-direction: column;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      li + li {
        border-top: 1px solid var(--ev-line);
      }

      summary {
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 10px 28px 10px 0;
        cursor: pointer;
        list-style: none;
      }

      summary::-webkit-details-marker {
        display: none;
      }

      summary::after {
        content: "";
        position: absolute;
        top: 50%;
        right: 6px;
        width: 7px;
        height: 7px;
        margin-top: -6px;
        border-right: 2px solid var(--ev-muted);
        border-bottom: 2px solid var(--ev-muted);
        transform: rotate(45deg);
      }

      details[open] > summary::after {
        margin-top: -2px;
        transform: rotate(-135deg);
      }

      .line {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 4px 12px;
      }

      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .vehicle {
        font-weight: 500;
      }

      .body {
        margin-bottom: 10px;
        border-radius: var(--ev-radius);
      }
    `
    ];
  }
}
Te([
  g({ attribute: !1 })
], pe.prototype, "hass");
Te([
  g({ attribute: !1 })
], pe.prototype, "t");
Te([
  g({ attribute: !1 })
], pe.prototype, "sessions");
var kr = Object.defineProperty, w = (r, e, t, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(e, t, i) || i);
  return i && kr(e, t, i), i;
};
const Tr = 600 * 1e3, Pr = 5, Mr = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z", Ur = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z", Or = [
  { id: "overview", label: "view_overview" },
  { id: "recent", label: "view_recent" },
  { id: "detail", label: "view_detail" }
], Rr = ["home", "home_no_wallbox", "external"], Nr = ["ac", "dc", "unknown"], zr = ["complete", "followup_open", "flagged"], Dr = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" }
];
function Ke(r) {
  return o`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${r} fill="currentColor"></path>
  </svg>`;
}
class y extends v {
  constructor() {
    super(...arguments), this._years = [], this._vehicles = [], this._failed = !1, this._metric = "energy", this._started = !1, this._recentRequested = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => this._refresh(), Tr);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), super.disconnectedCallback();
  }
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._state !== void 0);
  }
  willUpdate(e) {
    if (e.has("hass") && this.hass && this._state === void 0) {
      const t = this.initialState;
      this._state = {
        ...rr(/* @__PURE__ */ new Date(), this.hass.config.time_zone),
        ...t,
        filters: { ...ce, ...t?.filters }
      };
    }
    this._sync();
  }
  _sync() {
    const e = this.hass, t = this._state;
    !e || !t || (this._started || (this._started = !0, this._loadShared(e, !1)), t.view !== "recent" && this._yearKey !== t.year && (this._yearKey = t.year, this._yearSessions = void 0, this._loadYear(e, t.year, !1)), t.view === "recent" && !this._recentRequested && (this._recentRequested = !0, this._loadRecent(e, !1)));
  }
  _refresh() {
    const e = this.hass, t = this._state;
    !e || !t || !this._started || this._failed || (this._loadShared(e, !0), t.view !== "recent" && this._loadYear(e, t.year, !0), t.view === "recent" && this._loadRecent(e, !0));
  }
  _fail(e, t) {
    console.error("ev_charging: loading data failed", e), t || (this._failed = !0);
  }
  _retry() {
    this._failed = !1, this._started = !1, this._yearKey = void 0, this._recentRequested = !1, this.requestUpdate();
  }
  async _loadShared(e, t) {
    try {
      this._t = await ee(e);
    } catch (s) {
      this._t = H({}), this._fail(s, t);
      return;
    }
    try {
      this._vehicles = await tr(e);
    } catch (s) {
      this._fail(s, t);
    }
  }
  async _loadYear(e, t, s) {
    try {
      const i = await er(e, t);
      this._yearKey === t && (this._yearSessions = i.sessions, this._years = i.years);
    } catch (i) {
      this._yearKey === t && this._fail(i, s);
    }
  }
  async _loadRecent(e, t) {
    try {
      this._recent = await Ce(e, { limit: Pr });
    } catch (s) {
      this._fail(s, t);
    }
  }
  _setState(e) {
    this._state && (this._state = { ...this._state, ...e }, this.dispatchEvent(new CustomEvent("ev-state-changed", { detail: this._state })));
  }
  _setFilter(e, t) {
    this._state && this._setState({ filters: { ...this._state.filters, [e]: t } });
  }
  _shift(e) {
    this._state && this._setState(sr(this._state.year, this._state.month, e));
  }
  render() {
    const e = this._state;
    if (!e || !this.hass)
      return d;
    if (this._failed)
      return this._renderError(this._t ?? H({}));
    const t = this._t;
    return t ? o`
      <div class="view">
        ${this._renderTabs(t, e)}
        ${e.view === "recent" ? d : this._renderFilters(t, e)}
        ${e.view === "recent" ? d : this._renderPeriod(t, e)}
        ${e.view === "overview" ? this._renderOverview(t, e) : e.view === "detail" ? this._renderDetail(t, e) : this._renderRecent(t)}
        <p class="hint muted">${t("multi_day_hint")} ${t("estimate_hint")}</p>
      </div>
    ` : o`<div class="spinner" role="progressbar"></div>`;
  }
  _renderError(e) {
    return o`<div class="message">
      <span>${e("load_error")}</span>
      <button class="text" @click=${() => this._retry()}>${e("retry")}</button>
    </div>`;
  }
  _renderTabs(e, t) {
    return o`<nav class="tabs">
      ${Or.map(
      (s) => o`<button
          class=${ne({ tab: !0, active: s.id === t.view })}
          aria-current=${s.id === t.view ? "page" : "false"}
          @click=${() => this._setState({ view: s.id })}
        >
          ${e(s.label)}
        </button>`
    )}
    </nav>`;
  }
  _renderPeriod(e, t) {
    const s = this.hass, i = s.locale.language, n = X(/* @__PURE__ */ new Date(), s.config.time_zone), a = pr(this._years, n.year, t.year);
    return o`<div class="period">
      <button class="icon" aria-label=${e("period_previous")} @click=${() => this._shift(-1)}>
        ${Ke(Mr)}
      </button>
      <select
        aria-label=${e("period_month")}
        @change=${(l) => this._setState({ month: Number(l.target.value) })}
      >
        ${Array.from({ length: 12 }, (l, c) => c + 1).map(
      (l) => o`<option value=${l} .selected=${l === t.month}>
              ${me(l, i, "long")}
            </option>`
    )}
      </select>
      <select
        aria-label=${e("period_year")}
        @change=${(l) => this._setState({ year: Number(l.target.value) })}
      >
        ${a.map(
      (l) => o`<option value=${l} .selected=${l === t.year}>${l}</option>`
    )}
      </select>
      <button class="icon" aria-label=${e("period_next")} @click=${() => this._shift(1)}>
        ${Ke(Ur)}
      </button>
    </div>`;
  }
  _renderTiles(e, t) {
    const s = this.hass, i = s.locale.language, n = [
      ["total_energy", $(t.energy_kwh, i, t.energy_is_estimate)],
      ["total_cost", V(t.cost, i, s.config.currency)],
      ["total_duration", S(t.charge_duration_min)],
      ["total_sessions", String(t.count)],
      ["open_followups", String(t.open_followups)]
    ];
    return o`<div class="tiles">
      ${n.map(
      ([a, l]) => o`<div class="tile">
          <span class="tile-label muted">${e(a)}</span>
          <span class="tile-value">${l}</span>
        </div>`
    )}
    </div>`;
  }
  // Sessions of the selected year that pass the filters.
  _filteredYear(e) {
    return qe(this._yearSessions ?? [], e.filters);
  }
  _renderOverview(e, t) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const s = this._filteredYear(t), i = this.hass.config.time_zone, n = or(s, i);
    return o`
      ${this._renderTiles(e, n[t.month - 1])}
      ${this._renderChart(e, t, n)}
      ${this._renderYearSummary(e, t, lr(s))}
    `;
  }
  _metricValue(e) {
    switch (this._metric) {
      case "cost":
        return e.cost;
      case "duration":
        return e.charge_duration_min;
      default:
        return e.energy_kwh;
    }
  }
  _formatMetric(e) {
    const t = this.hass, s = t.locale.language;
    switch (this._metric) {
      case "cost":
        return We(e.cost, s, t.config.currency);
      case "duration":
        return Be(e.charge_duration_min);
      default:
        return Ve(e.energy_kwh, s, e.energy_is_estimate);
    }
  }
  _renderChart(e, t, s) {
    const i = this.hass.locale.language, n = Math.max(...s.map((a) => this._metricValue(a)), 0);
    return o`<section class="chart">
      <div class="chart-head">
        <h3>${e("chart_title", { year: t.year })}</h3>
        <label class="metric">
          <span class="muted">${e("chart_metric")}</span>
          <select
            @change=${(a) => {
      this._metric = a.target.value;
    }}
          >
            ${Dr.map(
      (a) => o`<option value=${a.id} .selected=${a.id === this._metric}>
                  ${e(a.label)}
                </option>`
    )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${s.map((a) => {
      const l = n > 0 ? this._metricValue(a) / n * 100 : 0, c = me(a.month, i, "long"), h = a.count === 0 ? m : this._formatMetric(a);
      return o`<button
            class=${ne({ bar: !0, selected: a.month === t.month })}
            title=${`${c}: ${h}`}
            aria-label=${`${c}: ${h}`}
            aria-pressed=${a.month === t.month ? "true" : "false"}
            @click=${() => this._setState({ month: a.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${l}%`}></span></span>
            <span class="bar-label muted">${me(a.month, i, "short")}</span>
            <span class="bar-value">${h}</span>
          </button>`;
    })}
      </div>
    </section>`;
  }
  _renderYearSummary(e, t, s) {
    const i = this.hass, n = i.locale.language, a = [
      ["scope_total", s.all],
      ["scope_internal", s.internal],
      ["scope_external", s.external]
    ], l = [
      ["total_energy", (c) => Ve(c.energy_kwh, n, c.energy_is_estimate)],
      ["total_cost", (c) => We(c.cost, n, i.config.currency)],
      ["total_duration", (c) => Be(c.charge_duration_min)],
      ["total_sessions", (c) => String(c.count)]
    ];
    return o`<section class="year-summary">
      <h3>${e("year_summary_title", { year: t.year })}</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            ${a.map(([c]) => o`<th class="num">${e(c)}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${l.map(
      ([c, h]) => o`<tr>
              <th>${e(c)}</th>
              ${a.map(([, _]) => o`<td class="num">${h(_)}</td>`)}
            </tr>`
    )}
        </tbody>
      </table>
    </section>`;
  }
  _renderFilters(e, t) {
    const s = this._yearSessions ?? [], i = t.filters, n = [
      ...hr(this._vehicles, s),
      { value: tt, label: e("unassigned") }
    ], a = [
      { value: ke, label: e("filter_no_card") },
      ...ur(
        this._vehicles.flatMap((l) => l.cards),
        s,
        i.card
      )
    ];
    return o`<div class="filters">
      ${this._renderFilter(e("filter_vehicle"), "vehicle", n, e)}
      ${this._renderFilter(
      e("filter_location"),
      "location",
      Rr.map((l) => ({ value: l, label: e(`location_${l}`) })),
      e
    )}
      ${this._renderFilter(
      e("filter_charge_type"),
      "chargeType",
      Nr.map((l) => ({ value: l, label: e(`charge_type_${l}`) })),
      e
    )}
      ${this._renderFilter(e("filter_card"), "card", a, e)}
      ${this._renderFilter(
      e("filter_status"),
      "status",
      zr.map((l) => ({ value: l, label: e(`status_${l}`) })),
      e
    )}
      ${dr(i) ? o`<button
            class="text reset"
            @click=${() => this._setState({ filters: { ...ce } })}
          >
            ${e("filter_reset")}
          </button>` : d}
    </div>`;
  }
  _renderDetail(e, t) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const s = this.hass.config.time_zone, i = st(this._yearSessions, t.month, s), n = qe(i, t.filters);
    return o`
      ${this._renderTiles(e, F(n))}
      <p class="count muted">
        ${e("filter_count", { shown: n.length, total: i.length })}
      </p>
      ${n.length === 0 ? o`<div class="message">
            ${i.length === 0 ? e("no_sessions") : e("no_sessions_filtered")}
          </div>` : this._renderTable(n, e)}
    `;
  }
  _renderRecent(e) {
    const t = this._recent;
    return t ? t.length === 0 ? o`<div class="message">${e("no_sessions")}</div>` : o`<ev-charging-session-list
          .hass=${this.hass}
          .t=${e}
          .sessions=${t}
        ></ev-charging-session-list>` : o`<div class="spinner" role="progressbar"></div>`;
  }
  _renderFilter(e, t, s, i) {
    const n = this._state.filters[t];
    return o`<label class="filter">
      <span class="muted">${e}</span>
      <select
        @change=${(a) => this._setFilter(t, a.target.value)}
      >
        <option value="" .selected=${n === ""}>${i("filter_all")}</option>
        ${s.map(
      (a) => o`<option value=${a.value} .selected=${a.value === n}>
              ${a.label}
            </option>`
    )}
      </select>
    </label>`;
  }
  _renderTable(e, t) {
    return o`<div class="table" role="table">
      <div class="head" role="row">
        <span>${t("col_date")}</span>
        <span>${t("filter_vehicle")}</span>
        <span>${t("filter_location")}</span>
        <span>${t("filter_charge_type")}</span>
        <span class="num">${t("total_energy")}</span>
        <span class="num">${t("total_cost")}</span>
        <span class="num">${t("total_duration")}</span>
        <span>${t("filter_status")}</span>
      </div>
      ${e.map((s) => this._renderSession(s, t))}
    </div>`;
  }
  _renderSession(e, t) {
    const s = this.hass, i = s.locale.language, n = s.config.time_zone, a = e.vehicle_id === null;
    return o`<details class="session">
      <summary>
        <span class="c-date">${J(e.plug_start, i, n)}</span>
        <span class=${ne({ "c-vehicle": !0, vehicle: !0, unassigned: a })}
          >${it(e, t)}</span
        >
        <span class="c-location"><span class="chip">${t(`location_${e.location}`)}</span></span>
        <span class="c-type"><span class="chip">${t(`charge_type_${e.charge_type}`)}</span></span>
        <span class="c-energy num"
          >${$(e.energy_kwh, i, e.energy_is_estimate)}</span
        >
        <span class="c-cost num">${V(e.cost, i, s.config.currency)}</span>
        <span class="c-duration num">${S(e.charge_duration_min)}</span>
        <span class="c-status">
          ${e.status === "complete" ? d : o`<span class="chip warn">${t(`status_${e.status}`)}</span>`}
          ${e.location_conflict ? o`<span class="chip alert">${t("flag_location_conflict")}</span>` : d}
          ${e.identification_conflict ? o`<span class="chip alert">${t("flag_identification_conflict")}</span>` : d}
          ${e.charge_error ? o`<span class="chip alert">${t("flag_charge_error")}</span>` : d}
          ${e.energy_unallocated_kwh > 0 ? o`<span class="chip warn">${t("flag_unallocated_energy")}</span>` : d}
        </span>
      </summary>
      ${nt(e, t, s)}
    </details>`;
  }
  static {
    this.styles = [
      P,
      at,
      b`
      :host {
        display: block;
        --ev-columns: minmax(150px, 1.3fr) minmax(120px, 1.2fr) minmax(140px, 1.2fr) 56px
          minmax(110px, 0.9fr) minmax(90px, 0.7fr) minmax(80px, 0.6fr) minmax(110px, 1fr);
      }

      .view {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }

      .tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        border-bottom: 1px solid var(--ev-line);
      }

      .tab {
        padding: 10px 16px;
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: var(--ev-muted);
        cursor: pointer;
      }

      .tab.active {
        border-bottom-color: var(--ev-accent);
        color: var(--primary-text-color);
      }

      .period {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }

      button.icon {
        display: inline-flex;
        padding: 4px;
        background: transparent;
        border: none;
        border-radius: 50%;
        cursor: pointer;
      }

      .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
      }

      .tile {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px 14px;
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
      }

      .tile-value {
        font-size: 1.4em;
        font-weight: 500;
      }

      .chart-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
      }

      .chart h3,
      .year-summary h3 {
        margin: 0;
        font-size: 1em;
        font-weight: 500;
      }

      .metric {
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }

      .plot {
        display: flex;
        gap: 4px;
        margin-top: 12px;
      }

      .bar {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: stretch;
        min-width: 0;
        padding: 0;
        background: transparent;
        border: none;
        cursor: pointer;
      }

      .fill-area {
        height: 170px;
        display: flex;
        align-items: flex-end;
      }

      .fill {
        display: block;
        width: 100%;
        min-height: 2px;
        background: var(--ev-line);
        border-radius: 4px 4px 0 0;
      }

      .bar.selected .fill,
      .bar:hover .fill {
        background: var(--ev-accent);
      }

      .bar-label {
        padding-top: 4px;
        font-size: 0.75em;
      }

      .bar-value {
        padding-top: 2px;
        font-size: 0.75em;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
      }

      .bar.selected .bar-value {
        font-weight: 500;
      }

      .year-summary {
        display: flex;
        flex-direction: column;
        gap: 0;
        margin-top: 24px;
      }

      .year-summary h3 {
        margin-bottom: 2px;
      }

      .year-summary table {
        width: 100%;
        border-collapse: collapse;
      }

      .year-summary th,
      .year-summary td {
        padding: 8px 12px;
        white-space: nowrap;
        border-bottom: 1px solid var(--ev-line);
        text-align: left;
        font-weight: 400;
      }

      .year-summary thead th {
        padding-top: 2px;
        color: var(--ev-muted);
        font-size: 0.85em;
      }

      .year-summary tbody th {
        color: var(--ev-muted);
      }

      .year-summary .num {
        text-align: right;
      }

      .filters {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        align-items: end;
        gap: 12px;
      }

      .filter {
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 0;
        font-size: 0.85em;
      }

      .filter select {
        width: 100%;
      }

      .count {
        margin: 0;
      }

      .table {
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
        overflow: hidden;
      }

      .head,
      summary {
        display: grid;
        grid-template-columns: var(--ev-columns);
        column-gap: 16px;
        align-items: center;
        padding: 10px 44px 10px 14px;
      }

      .head {
        background: var(--ev-head-bg);
        border-bottom: 1px solid var(--ev-line);
        color: var(--ev-muted);
        font-size: 0.85em;
        font-weight: 500;
        text-transform: none;
      }

      .session + .session {
        border-top: 1px solid var(--ev-line);
      }

      summary {
        position: relative;
        cursor: pointer;
        list-style: none;
      }

      summary::-webkit-details-marker {
        display: none;
      }

      summary::after {
        content: "";
        position: absolute;
        top: 50%;
        right: 18px;
        width: 7px;
        height: 7px;
        margin-top: -6px;
        border-right: 2px solid var(--ev-muted);
        border-bottom: 2px solid var(--ev-muted);
        transform: rotate(45deg);
      }

      details[open] > summary::after {
        margin-top: -2px;
        transform: rotate(-135deg);
      }

      .c-status {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .head span:last-child,
      .c-status {
        padding-left: 8px;
      }

      .c-location .chip {
        white-space: normal;
      }

      .c-type .chip {
        background: color-mix(in srgb, var(--primary-text-color) 12%, transparent);
      }

      .hint {
        margin: 0;
        font-size: 0.85em;
      }

      @media (max-width: 800px) {
        .head {
          display: none;
        }

        summary {
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px 12px;
        }

        .c-date {
          grid-column: 1 / 3;
          font-weight: 500;
        }

        .c-vehicle {
          text-align: right;
        }

        .c-energy,
        .c-cost,
        .c-duration {
          order: 1;
        }

        .c-location,
        .c-type,
        .c-status {
          order: 2;
        }

        .c-energy {
          text-align: left;
        }

        .c-duration {
          text-align: right;
        }

        .c-cost {
          text-align: center;
        }

        .c-type {
          text-align: center;
        }

        .c-status {
          justify-content: flex-end;
          padding-left: 0;
        }

        .year-summary th,
        .year-summary td {
          padding: 8px 6px;
          font-size: 0.9em;
        }

        .bar-value {
          writing-mode: vertical-rl;
          transform: rotate(180deg);
          align-self: center;
          padding-top: 6px;
        }
      }
    `
    ];
  }
}
w([
  g({ attribute: !1 })
], y.prototype, "hass");
w([
  g({ attribute: !1 })
], y.prototype, "initialState");
w([
  p()
], y.prototype, "_state");
w([
  p()
], y.prototype, "_t");
w([
  p()
], y.prototype, "_yearSessions");
w([
  p()
], y.prototype, "_years");
w([
  p()
], y.prototype, "_recent");
w([
  p()
], y.prototype, "_vehicles");
w([
  p()
], y.prototype, "_failed");
w([
  p()
], y.prototype, "_metric");
var Hr = Object.defineProperty, _e = (r, e, t, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(e, t, i) || i);
  return i && Hr(e, t, i), i;
};
const Ir = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
class re extends v {
  constructor() {
    super(...arguments), this.narrow = !1;
  }
  willUpdate() {
    this._initialState === void 0 && (this._initialState = nr(this.route?.path ?? "", window.location.search));
  }
  _toggleMenu() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: !0, composed: !0 }));
  }
  _onStateChanged(e) {
    const t = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${t}${ir(e.detail)}`);
  }
  render() {
    return o`
      <header>
        ${this.narrow ? o`<button class="menu" @click=${() => this._toggleMenu()}>
              <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d=${Ir} fill="currentColor"></path>
              </svg>
            </button>` : d}
        <h1>${this.panel?.title ?? ""}</h1>
      </header>
      <main>
        <ev-charging-panel-view
          .hass=${this.hass}
          .initialState=${this._initialState}
          @ev-state-changed=${this._onStateChanged}
        ></ev-charging-panel-view>
      </main>
    `;
  }
  static {
    this.styles = [
      P,
      b`
      :host {
        display: block;
        height: 100%;
        overflow-y: auto;
        background: var(--primary-background-color);
      }

      header {
        position: sticky;
        top: 0;
        z-index: 1;
        display: flex;
        align-items: center;
        gap: 8px;
        height: 56px;
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color));
        color: var(--app-header-text-color, #fff);
      }

      h1 {
        margin: 0;
        font-size: 1.25em;
        font-weight: 400;
      }

      button.menu {
        display: inline-flex;
        padding: 8px;
        margin-left: -8px;
        background: transparent;
        border: none;
        border-radius: 50%;
        color: inherit;
        cursor: pointer;
      }

      main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 16px;
      }
    `
    ];
  }
}
_e([
  g({ attribute: !1 })
], re.prototype, "hass");
_e([
  g({ type: Boolean })
], re.prototype, "narrow");
_e([
  g({ attribute: !1 })
], re.prototype, "route");
_e([
  g({ attribute: !1 })
], re.prototype, "panel");
var Lr = Object.defineProperty, ot = (r, e, t, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(e, t, i) || i);
  return i && Lr(e, t, i), i;
};
class Pe extends v {
  constructor() {
    super(...arguments), this.isPanel = !1;
  }
  setConfig(e) {
  }
  getCardSize() {
    return 8;
  }
  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }
  static getStubConfig() {
    return {};
  }
  render() {
    return o`<div class="card">
      <ev-charging-panel-view .hass=${this.hass}></ev-charging-panel-view>
    </div>`;
  }
  static {
    this.styles = [
      P,
      b`
      :host {
        display: block;
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border: var(--ha-card-border-width, 1px) solid
          var(--ha-card-border-color, var(--divider-color, transparent));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
      }

      :host([is-panel]) {
        height: 100%;
        overflow-y: auto;
        border: none;
        border-radius: 0;
      }

      .card {
        padding: 16px;
      }
    `
    ];
  }
}
ot([
  g({ attribute: !1 })
], Pe.prototype, "hass");
ot([
  g({ type: Boolean, reflect: !0, attribute: "is-panel" })
], Pe.prototype, "isPanel");
var Fr = Object.defineProperty, U = (r, e, t, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(e, t, i) || i);
  return i && Fr(e, t, i), i;
};
const L = 3, Me = 20, jr = 600 * 1e3;
function lt(r) {
  return Number.isInteger(r) && r >= 1 && r <= Me;
}
class B extends v {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1;
  }
  setConfig(e) {
    if (!lt(e.count ?? L))
      throw new Error(`count must be a whole number from 1 to ${Me}`);
    this._config = e, this._started && this.hass && this._load(this.hass, !0);
  }
  getCardSize() {
    return 1 + (this._config.count ?? L) * 2;
  }
  static getStubConfig() {
    return { count: L };
  }
  static getConfigElement() {
    return document.createElement("ev-charging-recent-card-editor");
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => {
      this.hass && this._started && !this._failed && this._load(this.hass, !0);
    }, jr);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one loads.
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._started);
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass));
  }
  async _start(e) {
    try {
      this._t = await ee(e);
    } catch (t) {
      console.error("ev_charging: loading translations failed", t), this._t = H({}), this._failed = !0;
      return;
    }
    await this._load(e, !1);
  }
  async _load(e, t) {
    try {
      this._sessions = await Ce(e, { limit: this._config.count ?? L }), this._failed = !1;
    } catch (s) {
      console.error("ev_charging: loading sessions failed", s), t || (this._failed = !0);
    }
  }
  _retry() {
    this.hass && (this._failed = !1, this._started = !1, this.requestUpdate());
  }
  render() {
    const e = this._t;
    return !e || !this.hass ? o`<div class="spinner" role="progressbar"></div>` : this._failed ? o`<div class="message">
        <span>${e("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${e("retry")}</button>
      </div>` : o`
      <h2>${this._config.title ?? e("recent_title")}</h2>
      ${this._sessions === void 0 ? o`<div class="spinner" role="progressbar"></div>` : this._sessions.length === 0 ? o`<div class="message">${e("no_sessions")}</div>` : o`<ev-charging-session-list
              .hass=${this.hass}
              .t=${e}
              .sessions=${this._sessions}
            ></ev-charging-session-list>`}
    `;
  }
  static {
    this.styles = [
      P,
      b`
      :host {
        display: block;
        padding: 16px;
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border: var(--ha-card-border-width, 1px) solid
          var(--ha-card-border-color, var(--divider-color, transparent));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
      }

      h2 {
        margin: 0 0 8px;
        font-size: 1.1em;
        font-weight: 500;
      }
    `
    ];
  }
}
U([
  g({ attribute: !1 })
], B.prototype, "hass");
U([
  p()
], B.prototype, "_config");
U([
  p()
], B.prototype, "_t");
U([
  p()
], B.prototype, "_sessions");
U([
  p()
], B.prototype, "_failed");
class fe extends v {
  constructor() {
    super(...arguments), this._config = {}, this._started = !1;
  }
  setConfig(e) {
    this._config = e;
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, ee(this.hass).then(
      (t) => this._t = t,
      () => this._t = H({})
    ));
  }
  _changed(e) {
    const t = Number(e.target.value);
    if (!lt(t)) {
      e.target.value = String(this._config.count ?? L);
      return;
    }
    this._config = { ...this._config, count: t }, this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: !0,
        composed: !0
      })
    );
  }
  render() {
    const e = this._t;
    return e ? o`<label>
      <span>${e("card_count")}</span>
      <input
        type="number"
        min="1"
        max=${Me}
        step="1"
        .value=${String(this._config.count ?? L)}
        @change=${(t) => this._changed(t)}
      />
    </label>` : o``;
  }
  static {
    this.styles = [
      P,
      b`
      label {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }

      input {
        width: 80px;
        padding: 6px 8px;
        font: inherit;
        color: inherit;
        background: var(--ev-surface);
        border: 1px solid var(--ev-line);
        border-radius: 8px;
      }
    `
    ];
  }
}
U([
  g({ attribute: !1 })
], fe.prototype, "hass");
U([
  p()
], fe.prototype, "_config");
U([
  p()
], fe.prototype, "_t");
function O(r, e) {
  customElements.get(r) || customElements.define(r, e);
}
O("ev-charging-panel-view", y);
O("ev-charging-session-list", pe);
O("ev-charging-panel", re);
O("ev-charging-panel-card", Pe);
O("ev-charging-recent-card", B);
O("ev-charging-recent-card-editor", fe);
O("ev-charging-live-card", A);
O("ev-charging-month-card", W);
const de = window;
de.customCards = de.customCards ?? [];
for (const r of [
  "ev-charging-panel-card",
  "ev-charging-recent-card",
  "ev-charging-live-card",
  "ev-charging-month-card"
])
  de.customCards.some((e) => e.type === r) || de.customCards.push({ type: r, name: r });
