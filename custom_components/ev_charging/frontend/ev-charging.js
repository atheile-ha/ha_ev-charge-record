/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const W = globalThis, lt = W.ShadowRoot && (W.ShadyCSS === void 0 || W.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, ct = Symbol(), gt = /* @__PURE__ */ new WeakMap();
let Tt = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== ct) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (lt && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = gt.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && gt.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const jt = (r) => new Tt(typeof r == "string" ? r : r + "", void 0, ct), z = (r, ...t) => {
  const e = r.length === 1 ? r[0] : t.reduce((s, i, n) => s + ((a) => {
    if (a._$cssResult$ === !0) return a.cssText;
    if (typeof a == "number") return a;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + a + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + r[n + 1], r[0]);
  return new Tt(e, r, ct);
}, Vt = (r, t) => {
  if (lt) r.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), i = W.litNonce;
    i !== void 0 && s.setAttribute("nonce", i), s.textContent = e.cssText, r.appendChild(s);
  }
}, mt = lt ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return jt(e);
})(r) : r;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Bt, defineProperty: Wt, getOwnPropertyDescriptor: Kt, getOwnPropertyNames: qt, getOwnPropertySymbols: Zt, getPrototypeOf: Gt } = Object, tt = globalThis, $t = tt.trustedTypes, Yt = $t ? $t.emptyScript : "", Jt = tt.reactiveElementPolyfillSupport, N = (r, t) => r, Z = { toAttribute(r, t) {
  switch (t) {
    case Boolean:
      r = r ? Yt : null;
      break;
    case Object:
    case Array:
      r = r == null ? r : JSON.stringify(r);
  }
  return r;
}, fromAttribute(r, t) {
  let e = r;
  switch (t) {
    case Boolean:
      e = r !== null;
      break;
    case Number:
      e = r === null ? null : Number(r);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(r);
      } catch {
        e = null;
      }
  }
  return e;
} }, ht = (r, t) => !Bt(r, t), vt = { attribute: !0, type: String, converter: Z, reflect: !1, useDefault: !1, hasChanged: ht };
Symbol.metadata ??= Symbol("metadata"), tt.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let P = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = vt) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), i = this.getPropertyDescriptor(t, s, e);
      i !== void 0 && Wt(this.prototype, t, i);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: i, set: n } = Kt(this.prototype, t) ?? { get() {
      return this[e];
    }, set(a) {
      this[e] = a;
    } };
    return { get: i, set(a) {
      const l = i?.call(this);
      n?.call(this, a), this.requestUpdate(t, l, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? vt;
  }
  static _$Ei() {
    if (this.hasOwnProperty(N("elementProperties"))) return;
    const t = Gt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(N("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(N("properties"))) {
      const e = this.properties, s = [...qt(e), ...Zt(e)];
      for (const i of s) this.createProperty(i, e[i]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [s, i] of e) this.elementProperties.set(s, i);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, s] of this.elementProperties) {
      const i = this._$Eu(e, s);
      i !== void 0 && this._$Eh.set(i, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const s = new Set(t.flat(1 / 0).reverse());
      for (const i of s) e.unshift(mt(i));
    } else t !== void 0 && e.push(mt(t));
    return e;
  }
  static _$Eu(t, e) {
    const s = e.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof t == "string" ? t.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t) => t(this));
  }
  addController(t) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(t), this.renderRoot !== void 0 && this.isConnected && t.hostConnected?.();
  }
  removeController(t) {
    this._$EO?.delete(t);
  }
  _$E_() {
    const t = /* @__PURE__ */ new Map(), e = this.constructor.elementProperties;
    for (const s of e.keys()) this.hasOwnProperty(s) && (t.set(s, this[s]), delete this[s]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return Vt(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((t) => t.hostConnected?.());
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t) => t.hostDisconnected?.());
  }
  attributeChangedCallback(t, e, s) {
    this._$AK(t, s);
  }
  _$ET(t, e) {
    const s = this.constructor.elementProperties.get(t), i = this.constructor._$Eu(t, s);
    if (i !== void 0 && s.reflect === !0) {
      const n = (s.converter?.toAttribute !== void 0 ? s.converter : Z).toAttribute(e, s.type);
      this._$Em = t, n == null ? this.removeAttribute(i) : this.setAttribute(i, n), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, i = s._$Eh.get(t);
    if (i !== void 0 && this._$Em !== i) {
      const n = s.getPropertyOptions(i), a = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : Z;
      this._$Em = i;
      const l = a.fromAttribute(e, n.type);
      this[i] = l ?? this._$Ej?.get(i) ?? l, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, i = !1, n) {
    if (t !== void 0) {
      const a = this.constructor;
      if (i === !1 && (n = this[t]), s ??= a.getPropertyOptions(t), !((s.hasChanged ?? ht)(n, e) || s.useDefault && s.reflect && n === this._$Ej?.get(t) && !this.hasAttribute(a._$Eu(t, s)))) return;
      this.C(t, e, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: s, reflect: i, wrapped: n }, a) {
    s && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, a ?? e ?? this[t]), n !== !0 || a !== void 0) || (this._$AL.has(t) || (this.hasUpdated || s || (e = void 0), this._$AL.set(t, e)), i === !0 && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (e) {
      Promise.reject(e);
    }
    const t = this.scheduleUpdate();
    return t != null && await t, !this.isUpdatePending;
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
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), this._$EO?.forEach((s) => s.hostUpdate?.()), this.update(e)) : this._$EM();
    } catch (s) {
      throw t = !1, this._$EM(), s;
    }
    t && this._$AE(e);
  }
  willUpdate(t) {
  }
  _$AE(t) {
    this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
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
  shouldUpdate(t) {
    return !0;
  }
  update(t) {
    this._$Eq &&= this._$Eq.forEach((e) => this._$ET(e, this[e])), this._$EM();
  }
  updated(t) {
  }
  firstUpdated(t) {
  }
};
P.elementStyles = [], P.shadowRootOptions = { mode: "open" }, P[N("elementProperties")] = /* @__PURE__ */ new Map(), P[N("finalized")] = /* @__PURE__ */ new Map(), Jt?.({ ReactiveElement: P }), (tt.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const dt = globalThis, yt = (r) => r, G = dt.trustedTypes, bt = G ? G.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, Mt = "$lit$", x = `lit$${Math.random().toFixed(9).slice(2)}$`, Ut = "?" + x, Xt = `<${Ut}>`, C = document, H = () => C.createComment(""), R = (r) => r === null || typeof r != "object" && typeof r != "function", pt = Array.isArray, Qt = (r) => pt(r) || typeof r?.[Symbol.iterator] == "function", at = `[ 	
\f\r]`, U = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, wt = /-->/g, xt = />/g, A = RegExp(`>|${at}(?:([^\\s"'>=/]+)(${at}*=${at}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), St = /'/g, At = /"/g, Ot = /^(?:script|style|textarea|title)$/i, te = (r) => (t, ...e) => ({ _$litType$: r, strings: t, values: e }), c = te(1), k = Symbol.for("lit-noChange"), h = Symbol.for("lit-nothing"), Et = /* @__PURE__ */ new WeakMap(), E = C.createTreeWalker(C, 129);
function Nt(r, t) {
  if (!pt(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return bt !== void 0 ? bt.createHTML(t) : t;
}
const ee = (r, t) => {
  const e = r.length - 1, s = [];
  let i, n = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", a = U;
  for (let l = 0; l < e; l++) {
    const o = r[l];
    let p, u, d = -1, $ = 0;
    for (; $ < o.length && (a.lastIndex = $, u = a.exec(o), u !== null); ) $ = a.lastIndex, a === U ? u[1] === "!--" ? a = wt : u[1] !== void 0 ? a = xt : u[2] !== void 0 ? (Ot.test(u[2]) && (i = RegExp("</" + u[2], "g")), a = A) : u[3] !== void 0 && (a = A) : a === A ? u[0] === ">" ? (a = i ?? U, d = -1) : u[1] === void 0 ? d = -2 : (d = a.lastIndex - u[2].length, p = u[1], a = u[3] === void 0 ? A : u[3] === '"' ? At : St) : a === At || a === St ? a = A : a === wt || a === xt ? a = U : (a = A, i = void 0);
    const y = a === A && r[l + 1].startsWith("/>") ? " " : "";
    n += a === U ? o + Xt : d >= 0 ? (s.push(p), o.slice(0, d) + Mt + o.slice(d) + x + y) : o + x + (d === -2 ? l : y);
  }
  return [Nt(r, n + (r[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class L {
  constructor({ strings: t, _$litType$: e }, s) {
    let i;
    this.parts = [];
    let n = 0, a = 0;
    const l = t.length - 1, o = this.parts, [p, u] = ee(t, e);
    if (this.el = L.createElement(p, s), E.currentNode = this.el.content, e === 2 || e === 3) {
      const d = this.el.content.firstChild;
      d.replaceWith(...d.childNodes);
    }
    for (; (i = E.nextNode()) !== null && o.length < l; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const d of i.getAttributeNames()) if (d.endsWith(Mt)) {
          const $ = u[a++], y = i.getAttribute(d).split(x), V = /([.?@])?(.*)/.exec($);
          o.push({ type: 1, index: n, name: V[2], strings: y, ctor: V[1] === "." ? re : V[1] === "?" ? ie : V[1] === "@" ? ae : et }), i.removeAttribute(d);
        } else d.startsWith(x) && (o.push({ type: 6, index: n }), i.removeAttribute(d));
        if (Ot.test(i.tagName)) {
          const d = i.textContent.split(x), $ = d.length - 1;
          if ($ > 0) {
            i.textContent = G ? G.emptyScript : "";
            for (let y = 0; y < $; y++) i.append(d[y], H()), E.nextNode(), o.push({ type: 2, index: ++n });
            i.append(d[$], H());
          }
        }
      } else if (i.nodeType === 8) if (i.data === Ut) o.push({ type: 2, index: n });
      else {
        let d = -1;
        for (; (d = i.data.indexOf(x, d + 1)) !== -1; ) o.push({ type: 7, index: n }), d += x.length - 1;
      }
      n++;
    }
  }
  static createElement(t, e) {
    const s = C.createElement("template");
    return s.innerHTML = t, s;
  }
}
function T(r, t, e = r, s) {
  if (t === k) return t;
  let i = s !== void 0 ? e._$Co?.[s] : e._$Cl;
  const n = R(t) ? void 0 : t._$litDirective$;
  return i?.constructor !== n && (i?._$AO?.(!1), n === void 0 ? i = void 0 : (i = new n(r), i._$AT(r, e, s)), s !== void 0 ? (e._$Co ??= [])[s] = i : e._$Cl = i), i !== void 0 && (t = T(r, i._$AS(r, t.values), i, s)), t;
}
class se {
  constructor(t, e) {
    this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = e;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const { el: { content: e }, parts: s } = this._$AD, i = (t?.creationScope ?? C).importNode(e, !0);
    E.currentNode = i;
    let n = E.nextNode(), a = 0, l = 0, o = s[0];
    for (; o !== void 0; ) {
      if (a === o.index) {
        let p;
        o.type === 2 ? p = new D(n, n.nextSibling, this, t) : o.type === 1 ? p = new o.ctor(n, o.name, o.strings, this, t) : o.type === 6 && (p = new ne(n, this, t)), this._$AV.push(p), o = s[++l];
      }
      a !== o?.index && (n = E.nextNode(), a++);
    }
    return E.currentNode = C, i;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class D {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, e, s, i) {
    this.type = 2, this._$AH = h, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = s, this.options = i, this._$Cv = i?.isConnected ?? !0;
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const e = this._$AM;
    return e !== void 0 && t?.nodeType === 11 && (t = e.parentNode), t;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, e = this) {
    t = T(this, t, e), R(t) ? t === h || t == null || t === "" ? (this._$AH !== h && this._$AR(), this._$AH = h) : t !== this._$AH && t !== k && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Qt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== h && R(this._$AH) ? this._$AA.nextSibling.data = t : this.T(C.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: s } = t, i = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = L.createElement(Nt(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === i) this._$AH.p(e);
    else {
      const n = new se(i, this), a = n.u(this.options);
      n.p(e), this.T(a), this._$AH = n;
    }
  }
  _$AC(t) {
    let e = Et.get(t.strings);
    return e === void 0 && Et.set(t.strings, e = new L(t)), e;
  }
  k(t) {
    pt(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, i = 0;
    for (const n of t) i === e.length ? e.push(s = new D(this.O(H()), this.O(H()), this, this.options)) : s = e[i], s._$AI(n), i++;
    i < e.length && (this._$AR(s && s._$AB.nextSibling, i), e.length = i);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const s = yt(t).nextSibling;
      yt(t).remove(), t = s;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class et {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, s, i, n) {
    this.type = 1, this._$AH = h, this._$AN = void 0, this.element = t, this.name = e, this._$AM = i, this.options = n, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = h;
  }
  _$AI(t, e = this, s, i) {
    const n = this.strings;
    let a = !1;
    if (n === void 0) t = T(this, t, e, 0), a = !R(t) || t !== this._$AH && t !== k, a && (this._$AH = t);
    else {
      const l = t;
      let o, p;
      for (t = n[0], o = 0; o < n.length - 1; o++) p = T(this, l[s + o], e, o), p === k && (p = this._$AH[o]), a ||= !R(p) || p !== this._$AH[o], p === h ? t = h : t !== h && (t += (p ?? "") + n[o + 1]), this._$AH[o] = p;
    }
    a && !i && this.j(t);
  }
  j(t) {
    t === h ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class re extends et {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === h ? void 0 : t;
  }
}
class ie extends et {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== h);
  }
}
class ae extends et {
  constructor(t, e, s, i, n) {
    super(t, e, s, i, n), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = T(this, t, e, 0) ?? h) === k) return;
    const s = this._$AH, i = t === h && s !== h || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, n = t !== h && (s === h || i);
    i && this.element.removeEventListener(this.name, this, s), n && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class ne {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    T(this, t);
  }
}
const oe = dt.litHtmlPolyfillSupport;
oe?.(L, D), (dt.litHtmlVersions ??= []).push("3.3.3");
const le = (r, t, e) => {
  const s = e?.renderBefore ?? t;
  let i = s._$litPart$;
  if (i === void 0) {
    const n = e?.renderBefore ?? null;
    s._$litPart$ = i = new D(t.insertBefore(H(), n), n, void 0, e ?? {});
  }
  return i._$AI(r), i;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ut = globalThis;
let S = class extends P {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t.firstChild, t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = le(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return k;
  }
};
S._$litElement$ = !0, S.finalized = !0, ut.litElementHydrateSupport?.({ LitElement: S });
const ce = ut.litElementPolyfillSupport;
ce?.({ LitElement: S });
(ut.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const he = { attribute: !0, type: String, converter: Z, reflect: !1, hasChanged: ht }, de = (r = he, t, e) => {
  const { kind: s, metadata: i } = e;
  let n = globalThis.litPropertyMetadata.get(i);
  if (n === void 0 && globalThis.litPropertyMetadata.set(i, n = /* @__PURE__ */ new Map()), s === "setter" && ((r = Object.create(r)).wrapped = !0), n.set(e.name, r), s === "accessor") {
    const { name: a } = e;
    return { set(l) {
      const o = t.get.call(this);
      t.set.call(this, l), this.requestUpdate(a, o, r, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(a, void 0, r, l), l;
    } };
  }
  if (s === "setter") {
    const { name: a } = e;
    return function(l) {
      const o = this[a];
      t.call(this, l), this.requestUpdate(a, o, r, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function g(r) {
  return (t, e) => typeof e == "object" ? de(r, t, e) : ((s, i, n) => {
    const a = i.hasOwnProperty(n);
    return i.constructor.createProperty(n, s), a ? Object.getOwnPropertyDescriptor(i, n) : void 0;
  })(r, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function _(r) {
  return g({ ...r, state: !0, attribute: !1 });
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const pe = { ATTRIBUTE: 1 }, ue = (r) => (...t) => ({ _$litDirective$: r, values: t });
class _e {
  constructor(t) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(t, e, s) {
    this._$Ct = t, this._$AM = e, this._$Ci = s;
  }
  _$AS(t, e) {
    return this.update(t, e);
  }
  update(t, e) {
    return this.render(...e);
  }
}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const K = ue(class extends _e {
  constructor(r) {
    if (super(r), r.type !== pe.ATTRIBUTE || r.name !== "class" || r.strings?.length > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
  }
  render(r) {
    return " " + Object.keys(r).filter((t) => r[t]).join(" ") + " ";
  }
  update(r, [t]) {
    if (this.st === void 0) {
      this.st = /* @__PURE__ */ new Set(), r.strings !== void 0 && (this.nt = new Set(r.strings.join(" ").split(/\s/).filter((s) => s !== "")));
      for (const s in t) t[s] && !this.nt?.has(s) && this.st.add(s);
      return this.render(t);
    }
    const e = r.element.classList;
    for (const s of this.st) s in t || (e.remove(s), this.st.delete(s));
    for (const s in t) {
      const i = !!t[s];
      i === this.st.has(s) || this.nt?.has(s) || (i ? (e.add(s), this.st.add(s)) : (e.remove(s), this.st.delete(s)));
    }
    return k;
  }
});
async function Ht(r, t) {
  return (await r.callWS({
    type: "ev_charging/sessions/list",
    ...t
  })).sessions;
}
function fe(r, t) {
  return r.callWS({ type: "ev_charging/sessions/stats", year: t });
}
async function ge(r) {
  return (await r.callWS({
    type: "ev_charging/sessions/open"
  })).sessions;
}
async function me(r) {
  return (await r.callWS({
    type: "ev_charging/vehicles/list"
  })).vehicles;
}
const v = "–";
function I(r, t, e) {
  return new Intl.NumberFormat(t, {
    minimumFractionDigits: e,
    maximumFractionDigits: e
  }).format(r);
}
function b(r, t, e = !1) {
  return r === null ? v : `${e ? "~" : ""}${I(r, t, 2)} kWh`;
}
function O(r, t, e) {
  if (r === null)
    return v;
  try {
    return new Intl.NumberFormat(t, { style: "currency", currency: e }).format(r);
  } catch {
    return `${I(r, t, 2)} ${e}`;
  }
}
function w(r) {
  if (r === null)
    return v;
  const t = Math.round(r);
  if (t < 60)
    return `${t} min`;
  const e = Math.floor(t / 60), s = String(t % 60).padStart(2, "0");
  return `${e}:${s} h`;
}
function Y(r, t) {
  return r === null ? v : `${I(r, t, 0)} %`;
}
function $e(r, t) {
  return r === null ? v : `${I(r, t, 0)} km`;
}
function ve(r, t) {
  return r === null ? v : `${I(r, t, 1)} kW`;
}
function q(r, t, e) {
  return r === null ? v : new Intl.DateTimeFormat(t, {
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(r));
}
function Ct(r, t, e) {
  return r === null ? v : new Intl.DateTimeFormat(t, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(r));
}
function nt(r, t, e) {
  return new Intl.DateTimeFormat(t, { month: e, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, r - 1, 1))
  );
}
const ye = "component.ev_charging.selector.panel.options.";
function J(r) {
  return (t, e) => {
    const s = r[ye + t];
    return s === void 0 ? t : e ? s.replace(
      /\{(\w+)\}/g,
      (i, n) => n in e ? String(e[n]) : i
    ) : s;
  };
}
const ot = /* @__PURE__ */ new Map();
function Rt(r) {
  const t = r.language;
  let e = ot.get(t);
  return e === void 0 && (e = r.callWS({
    type: "frontend/get_translations",
    language: t,
    category: "selector",
    integration: ["ev_charging"]
  }).then((s) => J(s.resources)), e.catch(() => ot.delete(t)), ot.set(t, e)), e;
}
function Lt(r, t) {
  return r.vehicle_id === null ? t("unassigned") : r.vehicle_name ?? r.vehicle_id;
}
const be = [
  "soc_start",
  "soc_end",
  "odometer_km",
  "energy_kwh",
  "energy_grid_kwh",
  "energy_solar_kwh",
  "cost",
  "address"
];
function we(r) {
  return be.includes(r);
}
function xe(r, t) {
  return we(r) ? t(`field_${r}`) : r;
}
const zt = "__unassigned__", _t = "__none__", X = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: ""
};
function Dt(r, t) {
  const e = new Intl.DateTimeFormat("en-US", {
    timeZone: t,
    year: "numeric",
    month: "numeric"
  }).formatToParts(r), s = (i) => Number(e.find((n) => n.type === i)?.value ?? 0);
  return { year: s("year"), month: s("month") };
}
function Se(r, t) {
  return { view: "overview", ...Dt(r, t), filters: { ...X } };
}
function Ae(r, t, e) {
  const s = r * 12 + (t - 1) + e;
  return { year: Math.floor(s / 12), month: s % 12 + 1 };
}
const It = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"]
];
function Ee(r) {
  const t = new URLSearchParams({ year: String(r.year), month: String(r.month) });
  for (const [e, s] of It)
    r.filters[e] !== "" && t.set(s, r.filters[e]);
  return `/${r.view}?${t.toString()}`;
}
function Ce(r, t) {
  const e = {}, s = r.split("/").filter((p) => p !== "")[0];
  (s === "overview" || s === "detail") && (e.view = s);
  const i = new URLSearchParams(t), n = Number(i.get("year")), a = Number(i.get("month"));
  Number.isInteger(n) && n >= 1e3 && n <= 9999 && Number.isInteger(a) && a >= 1 && a <= 12 && (e.year = n, e.month = a);
  const l = { ...X };
  let o = !1;
  for (const [p, u] of It) {
    const d = i.get(u);
    d && (l[p] = d, o = !0);
  }
  return o && (e.filters = l), e;
}
function ke(r) {
  return Object.values(r).some((t) => t !== "");
}
function Pe(r, t) {
  return r.filter((e) => {
    if (t.vehicle === zt) {
      if (e.vehicle_id !== null) return !1;
    } else if (t.vehicle !== "" && e.vehicle_id !== t.vehicle)
      return !1;
    if (t.location !== "" && e.location !== t.location || t.chargeType !== "" && e.charge_type !== t.chargeType || t.status !== "" && e.status !== t.status) return !1;
    if (t.card === _t) {
      if (e.card_uid !== null) return !1;
    } else if (t.card !== "" && e.card_uid !== t.card)
      return !1;
    return !0;
  });
}
function Te(r, t) {
  const e = /* @__PURE__ */ new Map();
  for (const s of r)
    e.set(s.id, s.name);
  for (const s of t)
    s.vehicle_id !== null && !e.has(s.vehicle_id) && e.set(s.vehicle_id, s.vehicle_name ?? s.vehicle_id);
  return [...e].map(([s, i]) => ({ value: s, label: i }));
}
function Me(r, t) {
  const e = /* @__PURE__ */ new Map();
  for (const s of r)
    s.card_uid !== null && !e.has(s.card_uid) && e.set(s.card_uid, s.card_label || s.card_uid);
  return t !== "" && t !== _t && !e.has(t) && e.set(t, t), [...e].map(([s, i]) => ({ value: s, label: i }));
}
function Ue(r, t, e) {
  return [.../* @__PURE__ */ new Set([...r, t, e])].sort((s, i) => i - s);
}
const st = z`
  :host {
    color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, inherit);
    --ev-muted: var(--secondary-text-color);
    --ev-line: var(--divider-color, rgba(127, 127, 127, 0.3));
    --ev-surface: var(--card-background-color, var(--ha-card-background, #fff));
    --ev-radius: var(--ha-card-border-radius, 12px);
    --ev-accent: var(--primary-color, #03a9f4);
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
    padding: 1px 8px;
    border: 1px solid var(--ev-line);
    border-radius: 999px;
    font-size: 0.8em;
    white-space: nowrap;
  }

  .chip.warn {
    border-color: var(--warning-color, #ff9800);
    color: var(--warning-color, #ff9800);
  }

  .chip.alert {
    border-color: var(--error-color, #db4437);
    color: var(--error-color, #db4437);
  }

  .vehicle.unassigned {
    color: var(--ev-muted);
    font-style: italic;
  }
`;
var Oe = Object.defineProperty, m = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && Oe(t, e, i), i;
};
const Ne = 600 * 1e3, He = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z", Re = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z", Le = [
  { id: "overview", label: "view_overview" },
  { id: "detail", label: "view_detail" }
], ze = ["home", "home_no_wallbox", "external"], De = ["ac", "dc", "unknown"], Ie = ["complete", "followup_open", "flagged"], Fe = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" }
];
function kt(r) {
  return c`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${r} fill="currentColor"></path>
  </svg>`;
}
class f extends S {
  constructor() {
    super(...arguments), this._vehicles = [], this._openCount = 0, this._failed = !1, this._metric = "energy", this._started = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => this._refresh(), Ne);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), super.disconnectedCallback();
  }
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._state !== void 0);
  }
  willUpdate(t) {
    if (t.has("hass") && this.hass && this._state === void 0) {
      const e = this.initialState;
      this._state = {
        ...Se(/* @__PURE__ */ new Date(), this.hass.config.time_zone),
        ...e,
        filters: { ...X, ...e?.filters }
      };
    }
    this._sync();
  }
  _sync() {
    const t = this.hass, e = this._state;
    if (!(!t || !e) && (this._started || (this._started = !0, this._loadShared(t, !1)), this._statsKey !== e.year && (this._statsKey = e.year, this._stats = void 0, this._loadStats(t, e.year, !1)), e.view === "detail")) {
      const s = `${e.year}-${e.month}`;
      this._sessionsKey !== s && (this._sessionsKey = s, this._sessions = void 0, this._loadSessions(t, e.year, e.month, !1));
    }
  }
  _refresh() {
    const t = this.hass, e = this._state;
    !t || !e || !this._started || this._failed || (this._loadShared(t, !0), this._loadStats(t, e.year, !0), e.view === "detail" && this._loadSessions(t, e.year, e.month, !0));
  }
  _fail(t, e) {
    console.error("ev_charging: loading data failed", t), e || (this._failed = !0);
  }
  _retry() {
    this._failed = !1, this._started = !1, this._statsKey = void 0, this._sessionsKey = void 0, this.requestUpdate();
  }
  async _loadShared(t, e) {
    try {
      this._t = await Rt(t);
    } catch (s) {
      this._t = J({}), this._fail(s, e);
      return;
    }
    try {
      const [s, i] = await Promise.all([me(t), ge(t)]);
      this._vehicles = s, this._openCount = i.length;
    } catch (s) {
      this._fail(s, e);
    }
  }
  async _loadStats(t, e, s) {
    try {
      const i = await fe(t, e);
      this._statsKey === e && (this._stats = i);
    } catch (i) {
      this._statsKey === e && this._fail(i, s);
    }
  }
  async _loadSessions(t, e, s, i) {
    const n = `${e}-${s}`;
    try {
      const a = await Ht(t, { year: e, month: s });
      this._sessionsKey === n && (this._sessions = a);
    } catch (a) {
      this._sessionsKey === n && this._fail(a, i);
    }
  }
  _setState(t) {
    this._state && (this._state = { ...this._state, ...t }, this.dispatchEvent(new CustomEvent("ev-state-changed", { detail: this._state })));
  }
  _setFilter(t, e) {
    this._state && this._setState({ filters: { ...this._state.filters, [t]: e } });
  }
  _shift(t) {
    this._state && this._setState(Ae(this._state.year, this._state.month, t));
  }
  render() {
    const t = this._state;
    if (!t || !this.hass)
      return h;
    if (this._failed)
      return this._renderError(this._t ?? J({}));
    const e = this._t;
    return e ? c`
      <div class="view">
        ${this._renderTabs(e, t)} ${this._renderPeriod(e, t)}
        ${t.view === "overview" ? this._renderOverview(e, t) : this._renderDetail(e, t)}
        <p class="hint muted">${e("multi_day_hint")} ${e("estimate_hint")}</p>
      </div>
    ` : c`<div class="spinner" role="progressbar"></div>`;
  }
  _renderError(t) {
    return c`<div class="message">
      <span>${t("load_error")}</span>
      <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
    </div>`;
  }
  _renderTabs(t, e) {
    return c`<nav class="tabs">
      ${Le.map(
      (s) => c`<button
          class=${K({ tab: !0, active: s.id === e.view })}
          aria-current=${s.id === e.view ? "page" : "false"}
          @click=${() => this._setState({ view: s.id })}
        >
          ${t(s.label)}
        </button>`
    )}
    </nav>`;
  }
  _renderPeriod(t, e) {
    const s = this.hass, i = s.locale.language, n = Dt(/* @__PURE__ */ new Date(), s.config.time_zone), a = Ue(this._stats?.years ?? [], n.year, e.year);
    return c`<div class="period">
      <button
        class="icon"
        aria-label=${t("period_previous")}
        @click=${() => this._shift(-1)}
      >
        ${kt(He)}
      </button>
      <select
        aria-label=${t("period_month")}
        @change=${(l) => this._setState({ month: Number(l.target.value) })}
      >
        ${Array.from({ length: 12 }, (l, o) => o + 1).map(
      (l) => c`<option value=${l} .selected=${l === e.month}>
              ${nt(l, i, "long")}
            </option>`
    )}
      </select>
      <select
        aria-label=${t("period_year")}
        @change=${(l) => this._setState({ year: Number(l.target.value) })}
      >
        ${a.map(
      (l) => c`<option value=${l} .selected=${l === e.year}>${l}</option>`
    )}
      </select>
      <button class="icon" aria-label=${t("period_next")} @click=${() => this._shift(1)}>
        ${kt(Re)}
      </button>
    </div>`;
  }
  _renderOverview(t, e) {
    const s = this._stats;
    if (!s)
      return c`<div class="spinner" role="progressbar"></div>`;
    const i = this.hass, n = i.locale.language, a = s.months[e.month - 1], l = [
      ["total_energy", b(a.energy_kwh, n, a.energy_is_estimate)],
      ["total_cost", O(a.cost, n, i.config.currency)],
      ["total_duration", w(a.charge_duration_min)],
      ["total_sessions", String(a.count)],
      ["open_followups", String(this._openCount)]
    ];
    return c`
      <div class="tiles">
        ${l.map(
      ([o, p]) => c`<div class="tile">
            <span class="tile-label muted">${t(o)}</span>
            <span class="tile-value">${p}</span>
          </div>`
    )}
      </div>
      ${this._renderChart(t, e, s)}
    `;
  }
  _metricValue(t) {
    switch (this._metric) {
      case "cost":
        return t.cost;
      case "duration":
        return t.charge_duration_min;
      default:
        return t.energy_kwh;
    }
  }
  _formatMetric(t) {
    const e = this.hass, s = e.locale.language;
    switch (this._metric) {
      case "cost":
        return O(t.cost, s, e.config.currency);
      case "duration":
        return w(t.charge_duration_min);
      default:
        return b(t.energy_kwh, s, t.energy_is_estimate);
    }
  }
  _renderChart(t, e, s) {
    const i = this.hass.locale.language, n = Math.max(...s.months.map((a) => this._metricValue(a)), 0);
    return c`<section class="chart">
      <div class="chart-head">
        <h3>${t("chart_title", { year: e.year })}</h3>
        <label class="metric">
          <span class="muted">${t("chart_metric")}</span>
          <select
            @change=${(a) => {
      this._metric = a.target.value;
    }}
          >
            ${Fe.map(
      (a) => c`<option value=${a.id} .selected=${a.id === this._metric}>
                  ${t(a.label)}
                </option>`
    )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${s.months.map((a) => {
      const l = n > 0 ? this._metricValue(a) / n * 100 : 0, o = nt(a.month, i, "long");
      return c`<button
            class=${K({ bar: !0, selected: a.month === e.month })}
            title=${`${o}: ${this._formatMetric(a)}`}
            aria-label=${`${o}: ${this._formatMetric(a)}`}
            aria-pressed=${a.month === e.month ? "true" : "false"}
            @click=${() => this._setState({ month: a.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${l}%`}></span></span>
            <span class="bar-label muted">${nt(a.month, i, "short")}</span>
          </button>`;
    })}
      </div>
    </section>`;
  }
  _renderDetail(t, e) {
    const s = this._sessions;
    if (!s)
      return c`<div class="spinner" role="progressbar"></div>`;
    const i = e.filters, n = Pe(s, i), a = [
      ...Te(this._vehicles, s),
      { value: zt, label: t("unassigned") }
    ], l = [
      { value: _t, label: t("filter_no_card") },
      ...Me(s, i.card)
    ];
    return c`
      <div class="filters">
        ${this._renderFilter(t("filter_vehicle"), "vehicle", a, t)}
        ${this._renderFilter(
      t("filter_location"),
      "location",
      ze.map((o) => ({ value: o, label: t(`location_${o}`) })),
      t
    )}
        ${this._renderFilter(
      t("filter_charge_type"),
      "chargeType",
      De.map((o) => ({ value: o, label: t(`charge_type_${o}`) })),
      t
    )}
        ${this._renderFilter(t("filter_card"), "card", l, t)}
        ${this._renderFilter(
      t("filter_status"),
      "status",
      Ie.map((o) => ({ value: o, label: t(`status_${o}`) })),
      t
    )}
        ${ke(i) ? c`<button
              class="text reset"
              @click=${() => this._setState({ filters: { ...X } })}
            >
              ${t("filter_reset")}
            </button>` : h}
      </div>
      <p class="count muted">
        ${t("filter_count", { shown: n.length, total: s.length })}
      </p>
      ${n.length === 0 ? c`<div class="message">
            ${s.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>` : c`<div class="sessions">${n.map((o) => this._renderSession(o, t))}</div>`}
    `;
  }
  _renderFilter(t, e, s, i) {
    const n = this._state.filters[e];
    return c`<label class="filter">
      <span class="muted">${t}</span>
      <select @change=${(a) => this._setFilter(e, a.target.value)}>
        <option value="" .selected=${n === ""}>${i("filter_all")}</option>
        ${s.map(
      (a) => c`<option value=${a.value} .selected=${a.value === n}>
              ${a.label}
            </option>`
    )}
      </select>
    </label>`;
  }
  _renderSession(t, e) {
    const s = this.hass, i = s.locale.language, n = s.config.time_zone, a = t.vehicle_id === null;
    return c`<details class="session">
      <summary>
        <span class="when">${q(t.plug_start, i, n)}</span>
        <span class=${K({ vehicle: !0, unassigned: a })}>${Lt(t, e)}</span>
        <span class="metrics">
          <span>${b(t.energy_kwh, i, t.energy_is_estimate)}</span>
          <span>${O(t.cost, i, s.config.currency)}</span>
          <span>${w(t.charge_duration_min)}</span>
        </span>
        <span class="chips">
          <span class="chip">${e(`location_${t.location}`)}</span>
          <span class="chip">${e(`charge_type_${t.charge_type}`)}</span>
          ${t.status === "complete" ? h : c`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
          ${t.location_conflict ? c`<span class="chip alert">${e("flag_location_conflict")}</span>` : h}
          ${t.identification_conflict ? c`<span class="chip alert">${e("flag_identification_conflict")}</span>` : h}
          ${t.charge_error ? c`<span class="chip alert">${e("flag_charge_error")}</span>` : h}
          ${t.energy_unallocated_kwh > 0 ? c`<span class="chip warn">${e("flag_unallocated_energy")}</span>` : h}
        </span>
      </summary>
      ${this._renderSessionBody(t, e)}
    </details>`;
  }
  _row(t, e) {
    return e === null || e === "" || e === v ? h : c`<dt class="muted">${t}</dt>
      <dd>${e}</dd>`;
  }
  _renderSessionBody(t, e) {
    const s = this.hass, i = s.locale.language, n = s.config.time_zone, a = t.location === "home", l = e("detail_not_recorded"), o = t.soc_start === null && t.soc_end === null ? null : `${Y(t.soc_start, i)} → ${Y(t.soc_end, i)}`, p = t.address ?? (t.latitude !== null && t.longitude !== null ? c`<a
            href=${`https://www.openstreetmap.org/?mlat=${t.latitude}&mlon=${t.longitude}#map=17/${t.latitude}/${t.longitude}`}
            target="_blank"
            rel="noopener noreferrer"
            >${e("detail_map_link")}</a
          >` : null);
    return c`<div class="body">
      <dl>
        ${this._row(e("detail_plug_start"), q(t.plug_start, i, n))}
        ${this._row(e("detail_plug_end"), q(t.plug_end, i, n))}
        ${this._row(e("detail_plug_duration"), w(t.plug_duration_min))}
        ${this._row(e("detail_charge_duration"), w(t.charge_duration_min))}
        ${t.pause_duration_min ? this._row(e("detail_pause_duration"), w(t.pause_duration_min)) : h}
        ${this._row(e("detail_soc"), o)}
        ${this._row(e("detail_odometer"), $e(t.odometer_km, i))}
        ${this._row(e("detail_power_avg"), ve(t.power_avg_kw, i))}
        ${a ? c`${this._row(
      e("detail_energy_grid"),
      t.energy_grid_kwh === null ? l : b(t.energy_grid_kwh, i)
    )}
            ${this._row(
      e("detail_energy_solar"),
      t.energy_solar_kwh === null ? l : b(t.energy_solar_kwh, i)
    )}` : h}
        ${t.energy_unallocated_kwh > 0 ? this._row(
      e("detail_energy_unallocated"),
      b(t.energy_unallocated_kwh, i)
    ) : h}
        ${this._row(e("detail_card"), t.card_label ?? t.card_uid)}
        ${this._row(e("detail_identification"), e(`identification_${t.identification_source}`))}
        ${this._row(e("detail_address"), p)}
        ${this._row(e("detail_provider"), t.provider)}
        ${this._row(e("detail_note"), t.note)}
        ${t.open_fields.length > 0 ? this._row(
      e("detail_open_fields"),
      t.open_fields.map((u) => xe(u, e)).join(", ")
    ) : h}
      </dl>
      ${this._renderPhases(t, e)}
    </div>`;
  }
  _renderPhases(t, e) {
    if (!t.phases_recorded || t.phases.length === 0)
      return c`<p class="muted">${e("detail_phases_not_recorded")}</p>`;
    const s = this.hass, i = s.locale.language, n = s.config.time_zone;
    return c`<table class="phases">
      <caption>
        ${e("detail_phases")}
      </caption>
      <thead>
        <tr>
          <th>${e("phase_start")}</th>
          <th>${e("phase_end")}</th>
          <th>${e("phase_duration")}</th>
          <th>${e("total_energy")}</th>
          <th>${e("total_cost")}</th>
        </tr>
      </thead>
      <tbody>
        ${t.phases.map(
      (a) => c`<tr>
            <td>${Ct(a.start, i, n)}</td>
            <td>${Ct(a.end, i, n)}</td>
            <td>${w(a.duration_min)}</td>
            <td>${b(a.energy_kwh, i)}</td>
            <td>${O(a.cost, i, s.config.currency)}</td>
          </tr>`
    )}
      </tbody>
    </table>`;
  }
  static {
    this.styles = [
      st,
      z`
      :host {
        display: block;
      }

      .view {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .tabs {
        display: flex;
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

      .chart h3 {
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
        height: 200px;
        margin-top: 12px;
      }

      .bar {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
        padding: 0;
        background: transparent;
        border: none;
        cursor: pointer;
      }

      .fill-area {
        flex: 1;
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

      .sessions {
        display: flex;
        flex-direction: column;
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
      }

      .session + .session {
        border-top: 1px solid var(--ev-line);
      }

      summary {
        position: relative;
        display: grid;
        grid-template-columns: minmax(150px, 1.2fr) minmax(90px, 1fr) minmax(220px, 2fr);
        gap: 4px 12px;
        align-items: center;
        padding: 10px 36px 10px 14px;
        cursor: pointer;
        list-style: none;
      }

      summary::after {
        content: "";
        position: absolute;
        top: 16px;
        right: 16px;
        width: 7px;
        height: 7px;
        border-right: 2px solid var(--ev-muted);
        border-bottom: 2px solid var(--ev-muted);
        transform: rotate(45deg);
      }

      details[open] > summary::after {
        top: 20px;
        transform: rotate(-135deg);
      }

      summary::-webkit-details-marker {
        display: none;
      }

      .metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 4px 14px;
      }

      .chips {
        grid-column: 1 / -1;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .body {
        padding: 0 14px 12px;
      }

      dl {
        display: grid;
        grid-template-columns: minmax(120px, max-content) 1fr;
        gap: 4px 16px;
        margin: 0;
      }

      dd {
        margin: 0;
        overflow-wrap: anywhere;
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

      .hint {
        margin: 0;
        font-size: 0.85em;
      }

      @media (max-width: 600px) {
        summary {
          grid-template-columns: 1fr 1fr;
        }

        .metrics {
          grid-column: 1 / -1;
        }
      }
    `
    ];
  }
}
m([
  g({ attribute: !1 })
], f.prototype, "hass");
m([
  g({ attribute: !1 })
], f.prototype, "initialState");
m([
  _()
], f.prototype, "_state");
m([
  _()
], f.prototype, "_t");
m([
  _()
], f.prototype, "_stats");
m([
  _()
], f.prototype, "_sessions");
m([
  _()
], f.prototype, "_vehicles");
m([
  _()
], f.prototype, "_openCount");
m([
  _()
], f.prototype, "_failed");
m([
  _()
], f.prototype, "_metric");
var je = Object.defineProperty, rt = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && je(t, e, i), i;
};
const Ve = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
class F extends S {
  constructor() {
    super(...arguments), this.narrow = !1;
  }
  willUpdate() {
    this._initialState === void 0 && (this._initialState = Ce(this.route?.path ?? "", window.location.search));
  }
  _toggleMenu() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: !0, composed: !0 }));
  }
  _onStateChanged(t) {
    const e = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${e}${Ee(t.detail)}`);
  }
  render() {
    return c`
      <header>
        ${this.narrow ? c`<button class="menu" @click=${() => this._toggleMenu()}>
              <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d=${Ve} fill="currentColor"></path>
              </svg>
            </button>` : h}
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
      st,
      z`
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
rt([
  g({ attribute: !1 })
], F.prototype, "hass");
rt([
  g({ type: Boolean })
], F.prototype, "narrow");
rt([
  g({ attribute: !1 })
], F.prototype, "route");
rt([
  g({ attribute: !1 })
], F.prototype, "panel");
var Be = Object.defineProperty, Ft = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && Be(t, e, i), i;
};
class ft extends S {
  constructor() {
    super(...arguments), this.isPanel = !1;
  }
  setConfig(t) {
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
    return c`<div class="card">
      <ev-charging-panel-view .hass=${this.hass}></ev-charging-panel-view>
    </div>`;
  }
  static {
    this.styles = [
      st,
      z`
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
Ft([
  g({ attribute: !1 })
], ft.prototype, "hass");
Ft([
  g({ type: Boolean, reflect: !0, attribute: "is-panel" })
], ft.prototype, "isPanel");
var We = Object.defineProperty, j = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && We(t, e, i), i;
};
const B = 3, Pt = 20, Ke = 600 * 1e3;
class M extends S {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1;
  }
  setConfig(t) {
    const e = t.count ?? B;
    if (!Number.isInteger(e) || e < 1 || e > Pt)
      throw new Error(`count must be a whole number from 1 to ${Pt}`);
    this._config = t, this._started && this.hass && this._load(this.hass, !0);
  }
  getCardSize() {
    return 1 + (this._config.count ?? B) * 2;
  }
  static getStubConfig() {
    return { count: B };
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => {
      this.hass && this._started && !this._failed && this._load(this.hass, !0);
    }, Ke);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one loads.
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._started);
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass));
  }
  async _start(t) {
    try {
      this._t = await Rt(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = J({}), this._failed = !0;
      return;
    }
    await this._load(t, !1);
  }
  async _load(t, e) {
    try {
      this._sessions = await Ht(t, { limit: this._config.count ?? B }), this._failed = !1;
    } catch (s) {
      console.error("ev_charging: loading sessions failed", s), e || (this._failed = !0);
    }
  }
  _retry() {
    this.hass && (this._failed = !1, this._started = !1, this.requestUpdate());
  }
  render() {
    const t = this._t;
    if (!t || !this.hass)
      return c`<div class="spinner" role="progressbar"></div>`;
    const e = this._config.title ?? t("recent_title");
    return this._failed ? c`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>` : c`
      <h2>${e}</h2>
      ${this._sessions === void 0 ? c`<div class="spinner" role="progressbar"></div>` : this._sessions.length === 0 ? c`<div class="message">${t("no_sessions")}</div>` : c`<ul>
              ${this._sessions.map((s) => this._renderSession(s, t))}
            </ul>`}
    `;
  }
  _renderSession(t, e) {
    const s = this.hass, i = s.locale.language, n = t.soc_start !== null && t.soc_end !== null ? `${Y(t.soc_start, i)} → ${Y(t.soc_end, i)}` : h;
    return c`<li>
      <div class="line">
        <span class=${K({ vehicle: !0, unassigned: t.vehicle_id === null })}
          >${Lt(t, e)}</span
        >
        <span class="muted">${q(t.plug_start, i, s.config.time_zone)}</span>
      </div>
      <div class="line">
        <span>
          ${b(t.energy_kwh, i, t.energy_is_estimate)} ·
          ${O(t.cost, i, s.config.currency)} ·
          ${w(t.charge_duration_min)}
        </span>
        <span class="muted">${n}</span>
      </div>
      <div class="line">
        <span class="chip">${e(`location_${t.location}`)}</span>
        ${t.status === "complete" ? h : c`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
      </div>
    </li>`;
  }
  static {
    this.styles = [
      st,
      z`
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

      ul {
        display: flex;
        flex-direction: column;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      li {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 10px 0;
      }

      li + li {
        border-top: 1px solid var(--ev-line);
      }

      .line {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 4px 12px;
      }

      .vehicle {
        font-weight: 500;
      }
    `
    ];
  }
}
j([
  g({ attribute: !1 })
], M.prototype, "hass");
j([
  _()
], M.prototype, "_config");
j([
  _()
], M.prototype, "_t");
j([
  _()
], M.prototype, "_sessions");
j([
  _()
], M.prototype, "_failed");
function it(r, t) {
  customElements.get(r) || customElements.define(r, t);
}
it("ev-charging-panel-view", f);
it("ev-charging-panel", F);
it("ev-charging-panel-card", ft);
it("ev-charging-recent-card", M);
const Q = window;
Q.customCards = Q.customCards ?? [];
for (const r of ["ev-charging-panel-card", "ev-charging-recent-card"])
  Q.customCards.some((t) => t.type === r) || Q.customCards.push({ type: r, name: r });
