/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const oe = globalThis, Pe = oe.ShadowRoot && (oe.ShadyCSS === void 0 || oe.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Me = Symbol(), We = /* @__PURE__ */ new WeakMap();
let lt = class {
  constructor(e, t, r) {
    if (this._$cssResult$ = !0, r !== Me) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (Pe && e === void 0) {
      const r = t !== void 0 && t.length === 1;
      r && (e = We.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), r && We.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const xt = (i) => new lt(typeof i == "string" ? i : i + "", void 0, Me), x = (i, ...e) => {
  const t = i.length === 1 ? i[0] : e.reduce((r, s, n) => r + ((a) => {
    if (a._$cssResult$ === !0) return a.cssText;
    if (typeof a == "number") return a;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + a + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s) + i[n + 1], i[0]);
  return new lt(t, i, Me);
}, St = (i, e) => {
  if (Pe) i.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const r = document.createElement("style"), s = oe.litNonce;
    s !== void 0 && r.setAttribute("nonce", s), r.textContent = t.cssText, i.appendChild(r);
  }
}, qe = Pe ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const r of e.cssRules) t += r.cssText;
  return xt(t);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: kt, defineProperty: Et, getOwnPropertyDescriptor: Ct, getOwnPropertyNames: At, getOwnPropertySymbols: Tt, getPrototypeOf: Ut } = Object, pe = globalThis, Be = pe.trustedTypes, Pt = Be ? Be.emptyScript : "", Mt = pe.reactiveElementPolyfillSupport, J = (i, e) => i, le = { toAttribute(i, e) {
  switch (e) {
    case Boolean:
      i = i ? Pt : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, e) {
  let t = i;
  switch (e) {
    case Boolean:
      t = i !== null;
      break;
    case Number:
      t = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(i);
      } catch {
        t = null;
      }
  }
  return t;
} }, Oe = (i, e) => !kt(i, e), Ye = { attribute: !0, type: String, converter: le, reflect: !1, useDefault: !1, hasChanged: Oe };
Symbol.metadata ??= Symbol("metadata"), pe.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let F = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ??= []).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Ye) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const r = Symbol(), s = this.getPropertyDescriptor(e, r, t);
      s !== void 0 && Et(this.prototype, e, s);
    }
  }
  static getPropertyDescriptor(e, t, r) {
    const { get: s, set: n } = Ct(this.prototype, e) ?? { get() {
      return this[t];
    }, set(a) {
      this[t] = a;
    } };
    return { get: s, set(a) {
      const c = s?.call(this);
      n?.call(this, a), this.requestUpdate(e, c, r);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Ye;
  }
  static _$Ei() {
    if (this.hasOwnProperty(J("elementProperties"))) return;
    const e = Ut(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(J("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(J("properties"))) {
      const t = this.properties, r = [...At(t), ...Tt(t)];
      for (const s of r) this.createProperty(s, t[s]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [r, s] of t) this.elementProperties.set(r, s);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, r] of this.elementProperties) {
      const s = this._$Eu(t, r);
      s !== void 0 && this._$Eh.set(s, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const r = new Set(e.flat(1 / 0).reverse());
      for (const s of r) t.unshift(qe(s));
    } else e !== void 0 && t.push(qe(e));
    return t;
  }
  static _$Eu(e, t) {
    const r = t.attribute;
    return r === !1 ? void 0 : typeof r == "string" ? r : typeof e == "string" ? e.toLowerCase() : void 0;
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
    for (const r of t.keys()) this.hasOwnProperty(r) && (e.set(r, this[r]), delete this[r]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return St(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((e) => e.hostDisconnected?.());
  }
  attributeChangedCallback(e, t, r) {
    this._$AK(e, r);
  }
  _$ET(e, t) {
    const r = this.constructor.elementProperties.get(e), s = this.constructor._$Eu(e, r);
    if (s !== void 0 && r.reflect === !0) {
      const n = (r.converter?.toAttribute !== void 0 ? r.converter : le).toAttribute(t, r.type);
      this._$Em = e, n == null ? this.removeAttribute(s) : this.setAttribute(s, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const r = this.constructor, s = r._$Eh.get(e);
    if (s !== void 0 && this._$Em !== s) {
      const n = r.getPropertyOptions(s), a = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : le;
      this._$Em = s;
      const c = a.fromAttribute(t, n.type);
      this[s] = c ?? this._$Ej?.get(s) ?? c, this._$Em = null;
    }
  }
  requestUpdate(e, t, r, s = !1, n) {
    if (e !== void 0) {
      const a = this.constructor;
      if (s === !1 && (n = this[e]), r ??= a.getPropertyOptions(e), !((r.hasChanged ?? Oe)(n, t) || r.useDefault && r.reflect && n === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, r)))) return;
      this.C(e, t, r);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: r, reflect: s, wrapped: n }, a) {
    r && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, a ?? t ?? this[e]), n !== !0 || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || r || (t = void 0), this._$AL.set(e, t)), s === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
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
        for (const [s, n] of this._$Ep) this[s] = n;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [s, n] of r) {
        const { wrapped: a } = n, c = this[s];
        a !== !0 || this._$AL.has(s) || c === void 0 || this.C(s, void 0, n, c);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((r) => r.hostUpdate?.()), this.update(t)) : this._$EM();
    } catch (r) {
      throw e = !1, this._$EM(), r;
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
F.elementStyles = [], F.shadowRootOptions = { mode: "open" }, F[J("elementProperties")] = /* @__PURE__ */ new Map(), F[J("finalized")] = /* @__PURE__ */ new Map(), Mt?.({ ReactiveElement: F }), (pe.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const De = globalThis, Ke = (i) => i, ce = De.trustedTypes, Ze = ce ? ce.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, ct = "$lit$", A = `lit$${Math.random().toFixed(9).slice(2)}$`, dt = "?" + A, Ot = `<${dt}>`, I = document, X = () => I.createComment(""), Q = (i) => i === null || typeof i != "object" && typeof i != "function", Re = Array.isArray, Dt = (i) => Re(i) || typeof i?.[Symbol.iterator] == "function", $e = `[ 	
\f\r]`, K = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Ge = /-->/g, Je = />/g, R = RegExp(`>|${$e}(?:([^\\s"'>=/]+)(${$e}*=${$e}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Xe = /'/g, Qe = /"/g, ht = /^(?:script|style|textarea|title)$/i, Rt = (i) => (e, ...t) => ({ _$litType$: i, strings: e, values: t }), o = Rt(1), z = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), et = /* @__PURE__ */ new WeakMap(), N = I.createTreeWalker(I, 129);
function ut(i, e) {
  if (!Re(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Ze !== void 0 ? Ze.createHTML(e) : e;
}
const Nt = (i, e) => {
  const t = i.length - 1, r = [];
  let s, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", a = K;
  for (let c = 0; c < t; c++) {
    const l = i[c];
    let h, _, u = -1, y = 0;
    for (; y < l.length && (a.lastIndex = y, _ = a.exec(l), _ !== null); ) y = a.lastIndex, a === K ? _[1] === "!--" ? a = Ge : _[1] !== void 0 ? a = Je : _[2] !== void 0 ? (ht.test(_[2]) && (s = RegExp("</" + _[2], "g")), a = R) : _[3] !== void 0 && (a = R) : a === R ? _[0] === ">" ? (a = s ?? K, u = -1) : _[1] === void 0 ? u = -2 : (u = a.lastIndex - _[2].length, h = _[1], a = _[3] === void 0 ? R : _[3] === '"' ? Qe : Xe) : a === Qe || a === Xe ? a = R : a === Ge || a === Je ? a = K : (a = R, s = void 0);
    const S = a === R && i[c + 1].startsWith("/>") ? " " : "";
    n += a === K ? l + Ot : u >= 0 ? (r.push(h), l.slice(0, u) + ct + l.slice(u) + A + S) : l + A + (u === -2 ? c : S);
  }
  return [ut(i, n + (i[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), r];
};
class ee {
  constructor({ strings: e, _$litType$: t }, r) {
    let s;
    this.parts = [];
    let n = 0, a = 0;
    const c = e.length - 1, l = this.parts, [h, _] = Nt(e, t);
    if (this.el = ee.createElement(h, r), N.currentNode = this.el.content, t === 2 || t === 3) {
      const u = this.el.content.firstChild;
      u.replaceWith(...u.childNodes);
    }
    for (; (s = N.nextNode()) !== null && l.length < c; ) {
      if (s.nodeType === 1) {
        if (s.hasAttributes()) for (const u of s.getAttributeNames()) if (u.endsWith(ct)) {
          const y = _[a++], S = s.getAttribute(u).split(A), ae = /([.?@])?(.*)/.exec(y);
          l.push({ type: 1, index: n, name: ae[2], strings: S, ctor: ae[1] === "." ? zt : ae[1] === "?" ? Ht : ae[1] === "@" ? Ft : _e }), s.removeAttribute(u);
        } else u.startsWith(A) && (l.push({ type: 6, index: n }), s.removeAttribute(u));
        if (ht.test(s.tagName)) {
          const u = s.textContent.split(A), y = u.length - 1;
          if (y > 0) {
            s.textContent = ce ? ce.emptyScript : "";
            for (let S = 0; S < y; S++) s.append(u[S], X()), N.nextNode(), l.push({ type: 2, index: ++n });
            s.append(u[y], X());
          }
        }
      } else if (s.nodeType === 8) if (s.data === dt) l.push({ type: 2, index: n });
      else {
        let u = -1;
        for (; (u = s.data.indexOf(A, u + 1)) !== -1; ) l.push({ type: 7, index: n }), u += A.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const r = I.createElement("template");
    return r.innerHTML = e, r;
  }
}
function j(i, e, t = i, r) {
  if (e === z) return e;
  let s = r !== void 0 ? t._$Co?.[r] : t._$Cl;
  const n = Q(e) ? void 0 : e._$litDirective$;
  return s?.constructor !== n && (s?._$AO?.(!1), n === void 0 ? s = void 0 : (s = new n(i), s._$AT(i, t, r)), r !== void 0 ? (t._$Co ??= [])[r] = s : t._$Cl = s), s !== void 0 && (e = j(i, s._$AS(i, e.values), s, r)), e;
}
class It {
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
    const { el: { content: t }, parts: r } = this._$AD, s = (e?.creationScope ?? I).importNode(t, !0);
    N.currentNode = s;
    let n = N.nextNode(), a = 0, c = 0, l = r[0];
    for (; l !== void 0; ) {
      if (a === l.index) {
        let h;
        l.type === 2 ? h = new re(n, n.nextSibling, this, e) : l.type === 1 ? h = new l.ctor(n, l.name, l.strings, this, e) : l.type === 6 && (h = new Vt(n, this, e)), this._$AV.push(h), l = r[++c];
      }
      a !== l?.index && (n = N.nextNode(), a++);
    }
    return N.currentNode = I, s;
  }
  p(e) {
    let t = 0;
    for (const r of this._$AV) r !== void 0 && (r.strings !== void 0 ? (r._$AI(e, r, t), t += r.strings.length - 2) : r._$AI(e[t])), t++;
  }
}
class re {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, r, s) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = r, this.options = s, this._$Cv = s?.isConnected ?? !0;
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
    e = j(this, e, t), Q(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== z && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Dt(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && Q(this._$AH) ? this._$AA.nextSibling.data = e : this.T(I.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: r } = e, s = typeof r == "number" ? this._$AC(e) : (r.el === void 0 && (r.el = ee.createElement(ut(r.h, r.h[0]), this.options)), r);
    if (this._$AH?._$AD === s) this._$AH.p(t);
    else {
      const n = new It(s, this), a = n.u(this.options);
      n.p(t), this.T(a), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = et.get(e.strings);
    return t === void 0 && et.set(e.strings, t = new ee(e)), t;
  }
  k(e) {
    Re(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let r, s = 0;
    for (const n of e) s === t.length ? t.push(r = new re(this.O(X()), this.O(X()), this, this.options)) : r = t[s], r._$AI(n), s++;
    s < t.length && (this._$AR(r && r._$AB.nextSibling, s), t.length = s);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const r = Ke(e).nextSibling;
      Ke(e).remove(), e = r;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class _e {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, r, s, n) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = e, this.name = t, this._$AM = s, this.options = n, r.length > 2 || r[0] !== "" || r[1] !== "" ? (this._$AH = Array(r.length - 1).fill(new String()), this.strings = r) : this._$AH = d;
  }
  _$AI(e, t = this, r, s) {
    const n = this.strings;
    let a = !1;
    if (n === void 0) e = j(this, e, t, 0), a = !Q(e) || e !== this._$AH && e !== z, a && (this._$AH = e);
    else {
      const c = e;
      let l, h;
      for (e = n[0], l = 0; l < n.length - 1; l++) h = j(this, c[r + l], t, l), h === z && (h = this._$AH[l]), a ||= !Q(h) || h !== this._$AH[l], h === d ? e = d : e !== d && (e += (h ?? "") + n[l + 1]), this._$AH[l] = h;
    }
    a && !s && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class zt extends _e {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class Ht extends _e {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class Ft extends _e {
  constructor(e, t, r, s, n) {
    super(e, t, r, s, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = j(this, e, t, 0) ?? d) === z) return;
    const r = this._$AH, s = e === d && r !== d || e.capture !== r.capture || e.once !== r.once || e.passive !== r.passive, n = e !== d && (r === d || s);
    s && this.element.removeEventListener(this.name, this, r), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Vt {
  constructor(e, t, r) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = r;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    j(this, e);
  }
}
const Lt = De.litHtmlPolyfillSupport;
Lt?.(ee, re), (De.litHtmlVersions ??= []).push("3.3.3");
const jt = (i, e, t) => {
  const r = t?.renderBefore ?? e;
  let s = r._$litPart$;
  if (s === void 0) {
    const n = t?.renderBefore ?? null;
    r._$litPart$ = s = new re(e.insertBefore(X(), n), n, void 0, t ?? {});
  }
  return s._$AI(i), s;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ne = globalThis;
let b = class extends F {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const e = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= e.firstChild, e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = jt(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return z;
  }
};
b._$litElement$ = !0, b.finalized = !0, Ne.litElementHydrateSupport?.({ LitElement: b });
const Wt = Ne.litElementPolyfillSupport;
Wt?.({ LitElement: b });
(Ne.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const qt = { attribute: !0, type: String, converter: le, reflect: !1, hasChanged: Oe }, Bt = (i = qt, e, t) => {
  const { kind: r, metadata: s } = t;
  let n = globalThis.litPropertyMetadata.get(s);
  if (n === void 0 && globalThis.litPropertyMetadata.set(s, n = /* @__PURE__ */ new Map()), r === "setter" && ((i = Object.create(i)).wrapped = !0), n.set(t.name, i), r === "accessor") {
    const { name: a } = t;
    return { set(c) {
      const l = e.get.call(this);
      e.set.call(this, c), this.requestUpdate(a, l, i, !0, c);
    }, init(c) {
      return c !== void 0 && this.C(a, void 0, i, c), c;
    } };
  }
  if (r === "setter") {
    const { name: a } = t;
    return function(c) {
      const l = this[a];
      e.call(this, c), this.requestUpdate(a, l, i, !0, c);
    };
  }
  throw Error("Unsupported decorator location: " + r);
};
function v(i) {
  return (e, t) => typeof t == "object" ? Bt(i, e, t) : ((r, s, n) => {
    const a = s.hasOwnProperty(n);
    return s.constructor.createProperty(n, r), a ? Object.getOwnPropertyDescriptor(s, n) : void 0;
  })(i, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function p(i) {
  return v({ ...i, state: !0, attribute: !1 });
}
const $ = "–";
function U(i, e, t) {
  return new Intl.NumberFormat(e, {
    minimumFractionDigits: t,
    maximumFractionDigits: t
  }).format(i);
}
function w(i, e, t = !1) {
  return i === null ? $ : `${t ? "~" : ""}${U(i, e, 3)} kWh`;
}
function tt(i, e, t = !1) {
  return i === null ? $ : `${t ? "~" : ""}${U(i, e, 0)} kWh`;
}
function rt(i, e, t) {
  if (i === null)
    return $;
  try {
    return new Intl.NumberFormat(e, {
      style: "currency",
      currency: t,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(i);
  } catch {
    return `${U(i, e, 0)} ${t}`;
  }
}
function it(i) {
  if (i === null)
    return $;
  const e = Math.round(i);
  return e < 60 ? `${e} min` : `${Math.round(e / 60)} h`;
}
function W(i, e, t) {
  if (i === null)
    return $;
  try {
    return new Intl.NumberFormat(e, { style: "currency", currency: t }).format(i);
  } catch {
    return `${U(i, e, 2)} ${t}`;
  }
}
function Yt(i, e, t) {
  if (i === null)
    return $;
  try {
    return `${new Intl.NumberFormat(e, {
      style: "currency",
      currency: t,
      minimumFractionDigits: 3,
      maximumFractionDigits: 4
    }).format(i)} / kWh`;
  } catch {
    return `${U(i, e, 4)} ${t} / kWh`;
  }
}
function E(i) {
  if (i === null)
    return $;
  const e = Math.round(i);
  if (e < 60)
    return `${e} min`;
  const t = Math.floor(e / 60), r = String(e % 60).padStart(2, "0");
  return `${t}:${r} h`;
}
function T(i, e) {
  return i === null ? $ : `${U(i, e, 0)} %`;
}
function Ie(i, e) {
  return i === null ? $ : `${U(i, e, 0)} km`;
}
function pt(i, e) {
  return i === null ? $ : `${U(i, e, 1)} kW`;
}
function q(i, e, t) {
  return i === null ? $ : new Intl.DateTimeFormat(e, {
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: t
  }).format(new Date(i));
}
function de(i, e, t) {
  return i === null ? $ : new Intl.DateTimeFormat(e, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: t
  }).format(new Date(i));
}
function ye(i, e, t) {
  return new Intl.DateTimeFormat(e, { month: t, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, i - 1, 1))
  );
}
function fe(i, e) {
  const t = () => e();
  return i.connection.addEventListener("ready", t), () => i.connection.removeEventListener("ready", t);
}
const Kt = "component.ev_charging.selector.panel.options.";
function H(i) {
  return (e, t) => {
    const r = i[Kt + e];
    return r === void 0 ? e : t ? r.replace(
      /\{(\w+)\}/g,
      (s, n) => n in t ? String(t[n]) : s
    ) : r;
  };
}
const be = /* @__PURE__ */ new Map();
function ie(i) {
  const e = i.language;
  let t = be.get(e);
  return t === void 0 && (t = i.callWS({
    type: "frontend/get_translations",
    language: e,
    category: "selector",
    integration: ["ev_charging"]
  }).then((r) => H(r.resources)), t.catch(() => be.delete(e)), be.set(e, t)), t;
}
const ze = 6e4;
function Zt(i, e, t) {
  if (i.net_duration_min === null)
    return null;
  const r = i.state === "charging";
  return i.net_duration_min + (r ? (t - e) / ze : 0);
}
function Gt(i, e) {
  return i.session_start === null ? null : Math.max((e - new Date(i.session_start).getTime()) / ze, 0);
}
function Jt(i, e) {
  if (i.charge_end === null)
    return null;
  const t = (new Date(i.charge_end).getTime() - e) / ze;
  return t > 0 ? t : null;
}
function Xt(i) {
  const e = i.energy_grid_kwh, t = i.energy_solar_kwh;
  return e === null || t === null || e + t <= 0 ? null : t / (e + t) * 100;
}
function Qt(i) {
  let e = 0, t = 0;
  for (const r of i)
    r.energy_grid_kwh !== null && r.energy_solar_kwh !== null && (e += r.energy_grid_kwh, t += r.energy_solar_kwh);
  return e + t > 0 ? t / (e + t) * 100 : null;
}
function Ce(i, e) {
  const t = (r) => new Intl.DateTimeFormat("en-CA", {
    timeZone: e.timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(r);
  return t(new Date(i).getTime()) === t(e.now) ? de(i, e.locale, e.timeZone) : q(i, e.locale, e.timeZone);
}
function er(i) {
  return i("live_title");
}
function tr(i, e) {
  if (i.kind === "external")
    return e("live_block_external");
  const t = i.wallbox?.name.trim();
  return t || e("live_title");
}
function rr(i, e, t) {
  if (i.soc_start === null && i.soc === null)
    return null;
  const r = i.soc_start !== null && i.soc !== null ? `${T(i.soc_start, t)} → ${T(i.soc, t)}` : T(i.soc ?? i.soc_start, t);
  return i.soc_target === null ? r : `${r} (${e("live_soc_target", { target: i.soc_target })})`;
}
function ir(i, e, t) {
  const r = [
    i.odometer_km === null ? null : Ie(i.odometer_km, t),
    rr(i, e, t)
  ].filter((s) => s !== null);
  return r.length === 0 ? null : r.join(" · ");
}
function sr(i, e, t) {
  return i.charge_end !== null ? de(i.charge_end, t.locale, t.timeZone) : i.charge_end_missing === "no_power" ? e("live_charge_end_no_power") : null;
}
const nr = {
  ac: "charge_type_ac",
  dc: "charge_type_dc"
};
function ar(i, e) {
  return i.charge_type === null ? null : e(nr[i.charge_type]);
}
function or(i, e) {
  switch (i.plug?.state) {
    case "not_connected":
      return e("live_idle_not_connected");
    case "unavailable":
      return e("live_idle_plug_unavailable");
    default:
      return e("live_idle");
  }
}
function lr(i, e, t) {
  const r = i.state_since === null ? null : Ce(i.state_since, t);
  switch (i.state) {
    case "candidate":
      return e("live_status_candidate");
    case "charging":
      return r === null ? e("live_state_charging") : e("live_status_charging", { time: r });
    case "paused":
      return i.waiting_for_power ? e("live_status_waiting_for_power") : r === null ? e("live_status_paused") : e("live_status_paused_since", { time: r });
    case "error":
      return r === null ? e("live_state_error") : e("live_status_error", { time: r });
    case "awaiting_final":
      return e("live_status_awaiting_final");
    default:
      return e("live_idle");
  }
}
function cr(i, e) {
  return i.phase_count === 0 ? null : i.phase_count === 1 ? e("live_phase_one") : e("live_phase_other", { count: i.phase_count });
}
function dr(i, e, t) {
  const r = i.plug;
  if (r === null)
    return "";
  switch (r.state) {
    case "connected":
      return e("live_plug_connected");
    case "not_connected":
      return e("live_plug_not_connected");
    default:
      return r.unavailable_since !== null && r.timeout_at !== null ? e("live_plug_unavailable_timeout", {
        since: Ce(r.unavailable_since, t),
        timeout: Ce(r.timeout_at, t)
      }) : e("live_plug_unavailable");
  }
}
function hr(i, e) {
  return i.vehicle_guest ? e("live_vehicle_guest") : i.vehicle !== null ? i.vehicle.name : i.identification_decided ? e("unassigned") : e("live_assign_detecting");
}
const ur = {
  rfid: "identification_rfid",
  emaid: "identification_emaid",
  vehicle_api: "identification_vehicle_api",
  manual: "identification_manual"
};
function _t(i, e) {
  const t = i.identification_source;
  if (!i.identification_decided || i.vehicle === null || t === null)
    return null;
  const r = ur[t];
  return r === void 0 ? null : e("live_assign_via", { source: e(r) });
}
function pr(i, e) {
  const t = i.identification_read;
  if (t === null || t.state === "read" && _t(i, e) !== null)
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
function _r(i, e) {
  if (i.counter === null || i.counter.authoritative === null)
    return null;
  const { authoritative: t, switched: r } = i.counter, s = e(t === "total" ? "live_counter_total" : "live_counter_session");
  return r ? e("live_counter_switched", { counter: s }) : e("live_counter", { counter: s });
}
function fr(i, e, t) {
  const r = i.energy_unallocated_kwh;
  return r === null || r <= 0 ? null : e("live_unallocated", { energy: w(r, t) });
}
function gr(i, e) {
  return i.sources === null ? { split: null, cost: null } : {
    split: i.energy_grid_kwh === null && !i.sources.grid_balance ? e("live_missing_split") : null,
    cost: i.cost === null && !i.sources.grid_price ? e("live_missing_cost") : null
  };
}
const P = x`
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
var mr = Object.defineProperty, M = (i, e, t, r) => {
  for (var s = void 0, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (s = a(e, t, s) || s);
  return s && mr(e, t, s), s;
};
const vr = "ev_charging/live/subscribe", $r = 1e3;
class C extends b {
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
      this._live?.some((e) => e.active) && (this._now = Date.now());
    }, $r), this.hass && this._started && this._subscribe(this.hass), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._started);
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass), this._watchConnection(this.hass));
  }
  // A load that raced a reconnect leaves the card failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(e) {
    this._connectionUnsub || (this._connectionUnsub = fe(e, () => {
      (this._failed || this._noWallbox) && this.hass && this._subscribe(this.hass);
    }));
  }
  async _start(e) {
    try {
      this._t = await ie(e);
    } catch (t) {
      console.error("ev_charging: loading translations failed", t), this._t = H({});
    }
    await this._subscribe(e);
  }
  async _subscribe(e) {
    this._release(), this._failed = !1, this._noWallbox = !1;
    const t = e.connection.subscribeMessage(
      (r) => {
        this._live = r, this._received = Date.now(), this._now = this._received;
      },
      { type: vr }
    );
    this._unsubscribe = t;
    try {
      await t;
    } catch (r) {
      this._unsubscribe = void 0, r.code === "not_found" ? this._noWallbox = !0 : (console.error("ev_charging: subscribing to the live values failed", r), this._failed = !0);
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
  // The vehicle with its odometer and state of charge in a muted line below.
  _vehicle(e, t, r) {
    const s = !e.vehicle_guest && e.vehicle === null, n = ir(e, t, r);
    return o`<div class="vehicle ${s ? "unassigned" : ""}">${hr(e, t)}</div>
      ${n === null ? d : o`<div class="vehicle-details">${n}</div>`}`;
  }
  _format(e) {
    return {
      locale: e.locale?.language ?? e.language,
      timeZone: e.config.time_zone,
      now: this._now
    };
  }
  // The state of the session and where it came from: what it is doing, the plug,
  // the assignment and the reading of the identification. The plug only applies
  // to the wallbox block; an external block never carries one.
  _status(e, t, r) {
    const s = cr(e, t), n = [
      _t(e, t),
      e.kind === "wallbox" ? dr(e, t, r) : null,
      pr(e, t)
    ].filter((a) => a !== null && a !== "");
    return o`<div class="status">
      <div class="state">
        ${lr(e, t, r)}${s === null ? d : o` · ${s}`}
      </div>
      ${n.map((a) => o`<div class="line">${a}</div>`)}
    </div>`;
  }
  // The data situation: which counter carries the energy, and energy that could
  // not be assigned. Wallbox blocks only; an external block has neither.
  _situation(e, t, r) {
    const s = [_r(e, t), fr(e, t, r)].filter(
      (n) => n !== null
    );
    return s.length === 0 ? d : o`<div class="situation">${s.map((n) => o`<div>${n}</div>`)}</div>`;
  }
  _flags(e, t) {
    const r = [];
    return e.charge_error && r.push(o`<span class="chip alert">${t("flag_charge_error")}</span>`), e.location_conflict && r.push(o`<span class="chip warn">${t("flag_location_conflict")}</span>`), e.identification_conflict && r.push(o`<span class="chip warn">${t("flag_identification_conflict")}</span>`), e.flagged && r.push(o`<span class="chip warn">${t("status_flagged")}</span>`), r.length === 0 ? d : o`<div class="flags">${r}</div>`;
  }
  // Wallbox blocks show the grid/solar split, the cost and the price; external
  // blocks never have those and show the address, charge type and range instead.
  _details(e, t, r) {
    const s = r.locale?.language ?? r.language, n = e.currency || r.config.currency, a = sr(e, t, {
      locale: s,
      timeZone: r.config.time_zone,
      now: this._now
    }), c = a === null ? d : this._row(t("live_charge_end"), a);
    let l = d, h = d;
    if (e.kind === "wallbox") {
      const _ = Xt(e), u = gr(e, t), y = e.energy_grid_kwh === null || e.energy_solar_kwh === null ? u.split === null ? d : this._row(`${t("detail_energy_grid")} / ${t("detail_energy_solar")}`, u.split) : this._row(
        `${t("detail_energy_grid")} / ${t("detail_energy_solar")}`,
        `${w(e.energy_grid_kwh, s)} / ${w(
          e.energy_solar_kwh,
          s
        )}${_ === null ? "" : ` (${t("live_solar_share", { percent: Math.round(_) })})`}`
      ), S = e.effective_price === null ? d : this._row(t("live_price"), Yt(e.effective_price, s, n));
      l = o`${y}
        ${this._row(t("live_cost"), u.cost ?? W(e.cost, s, n))}
        ${S}`;
    } else {
      const _ = ar(e, t), u = Jt(e, this._now);
      l = o`
        ${e.address === null ? d : this._row(t("live_address"), e.address)}
        ${_ === null ? d : this._row(t("live_charge_type"), _)}
        ${e.range_km === null ? d : this._row(t("live_range"), Ie(e.range_km, s))}
      `, h = u === null ? d : this._row(t("live_remaining_time"), E(u));
    }
    return o`<dl>
      ${this._row(t("live_power"), pt(e.charge_power_kw, s))}
      ${this._row(t("live_energy"), w(e.energy_kwh, s, e.energy_is_estimate))}
      ${l}
      ${this._row(
      t("live_charge_time"),
      E(Zt(e, this._received, this._now))
    )}
      ${this._row(t("live_plug_time"), E(Gt(e, this._now)))}
      ${c} ${h}
    </dl>`;
  }
  // One block: the wallbox's own session, or one vehicle's own external session.
  _block(e, t, r) {
    const s = tr(e, t);
    if (!e.active)
      return o`<div class="block">
        <h3><span>${s}</span></h3>
        <div class="message">${or(e, t)}</div>
      </div>`;
    const n = `live_state_${e.state}`;
    return o`<div class="block">
      <h3>
        <span>${s}</span>
        <span class="chip ${e.state === "error" ? "alert" : ""}">${t(n)}</span>
      </h3>
      ${this._vehicle(e, t, r.locale?.language ?? r.language)}
      ${this._status(e, t, this._format(r))}
      ${this._details(e, t, r)}
      ${this._situation(e, t, r.locale?.language ?? r.language)}
      ${this._flags(e, t)}
    </div>`;
  }
  render() {
    const e = this._t, t = this.hass;
    if (!e || !t)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = this._config.title ?? er(e);
    if (this._noWallbox)
      return o`<h2>${r}</h2>
        <div class="message">${e("live_no_wallbox")}</div>`;
    if (this._failed)
      return o`<h2>${r}</h2>
        <div class="message">
          <span>${e("load_error")}</span>
          <button class="text" @click=${() => this._retry()}>${e("retry")}</button>
        </div>`;
    const s = this._live;
    return s === void 0 ? o`<h2>${r}</h2>
        <div class="spinner" role="progressbar"></div>` : o`<h2>${r}</h2>
      ${s.map((n) => this._block(n, e, t))}`;
  }
  static {
    this.styles = [
      P,
      x`
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

      .block + .block {
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12));
      }

      h3 {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin: 0 0 8px;
        font-size: 1em;
        font-weight: 500;
      }

      .vehicle {
        font-size: 1.3em;
        font-weight: 500;
      }

      .vehicle-details {
        color: var(--ev-muted);
        font-size: 0.9em;
      }

      .vehicle,
      .vehicle-details {
        overflow-wrap: anywhere;
      }

      .status {
        margin: 8px 0 12px;
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
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px 16px;
        margin: 0;
      }

      .row {
        display: flex;
        flex-direction: column;
        min-width: 0;
      }


      dt {
        color: var(--ev-muted);
        font-size: 0.85em;
      }

      dd {
        margin: 0;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
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
  v({ attribute: !1 })
], C.prototype, "hass");
M([
  p()
], C.prototype, "_config");
M([
  p()
], C.prototype, "_t");
M([
  p()
], C.prototype, "_live");
M([
  p()
], C.prototype, "_received");
M([
  p()
], C.prototype, "_now");
M([
  p()
], C.prototype, "_failed");
M([
  p()
], C.prototype, "_noWallbox");
async function He(i, e) {
  return (await i.callWS({
    type: "ev_charging/sessions/list",
    ...e
  })).sessions;
}
function yr(i, e) {
  return i.callWS({ type: "ev_charging/sessions/list", year: e });
}
async function br(i) {
  return (await i.callWS({
    type: "ev_charging/vehicles/list"
  })).vehicles;
}
async function wr(i) {
  return (await i.callWS({ type: "ev_charging/sessions/open" })).sessions;
}
async function xr(i, e, t) {
  return (await i.callWS({
    type: "ev_charging/sessions/update",
    session_id: e,
    ...t
  })).session;
}
async function Sr(i, e) {
  await i.callWS({ type: "ev_charging/sessions/delete", session_id: e });
}
async function kr(i, e) {
  return (await i.callWS({
    type: "ev_charging/sessions/close_followup",
    session_id: e
  })).session;
}
async function Er(i, e, t) {
  return (await i.callWS({
    type: "ev_charging/sessions/correct_vehicle",
    session_id: e,
    vehicle_id: t
  })).session;
}
async function Cr(i, e) {
  return (await i.callWS({
    type: "ev_charging/sessions/create",
    ...e
  })).session;
}
const ft = "__unassigned__", Fe = "__none__", he = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: ""
};
function te(i, e) {
  const t = new Intl.DateTimeFormat("en-US", {
    timeZone: e,
    year: "numeric",
    month: "numeric"
  }).formatToParts(i), r = (s) => Number(t.find((n) => n.type === s)?.value ?? 0);
  return { year: r("year"), month: r("month") };
}
function Ar(i, e) {
  return { view: "overview", ...te(i, e), filters: { ...he } };
}
function Tr(i, e, t) {
  const r = i * 12 + (e - 1) + t;
  return { year: Math.floor(r / 12), month: r % 12 + 1 };
}
const gt = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"]
];
function Ur(i) {
  const e = new URLSearchParams({ year: String(i.year), month: String(i.month) });
  for (const [t, r] of gt)
    i.filters[t] !== "" && e.set(r, i.filters[t]);
  return `/${i.view}?${e.toString()}`;
}
function Pr(i, e) {
  const t = {}, r = i.split("/").filter((h) => h !== "")[0];
  (r === "overview" || r === "detail" || r === "recent" || r === "followup" || r === "correction") && (t.view = r);
  const s = new URLSearchParams(e), n = Number(s.get("year")), a = Number(s.get("month"));
  Number.isInteger(n) && n >= 1e3 && n <= 9999 && Number.isInteger(a) && a >= 1 && a <= 12 && (t.year = n, t.month = a);
  const c = { ...he };
  let l = !1;
  for (const [h, _] of gt) {
    const u = s.get(_);
    u && (c[h] = u, l = !0);
  }
  return l && (t.filters = c), t;
}
function we(i) {
  const e = i.reduce((t, r) => t + (r ?? 0), 0);
  return Math.round(e * 1e4) / 1e4;
}
function L(i) {
  return {
    count: i.length,
    energy_kwh: we(i.map((e) => e.energy_kwh)),
    energy_is_estimate: i.some((e) => e.energy_is_estimate),
    cost: we(i.map((e) => e.cost)),
    charge_duration_min: we(i.map((e) => e.charge_duration_min)),
    open_followups: i.filter(
      (e) => e.status === "followup_open" || e.open_fields.length > 0
    ).length
  };
}
function Mr(i, e) {
  return te(new Date(i.plug_start), e).month;
}
function Ae(i, e, t) {
  return i.filter((r) => Mr(r, t) === e);
}
function Or(i, e) {
  return Array.from({ length: 12 }, (t, r) => ({
    month: r + 1,
    ...L(Ae(i, r + 1, e))
  }));
}
function Dr(i) {
  const e = i.filter((r) => r.location === "external"), t = i.filter((r) => r.location !== "external");
  return {
    all: L(i),
    internal: L(t),
    external: L(e)
  };
}
function Rr(i) {
  let e = null;
  return i.latitude !== null && i.longitude !== null ? e = `${i.latitude},${i.longitude}` : i.address && (e = i.address), e === null ? null : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(e)}`;
}
function Nr(i) {
  return Object.values(i).some((e) => e !== "");
}
function xe(i, e) {
  return i.filter((t) => {
    if (e.vehicle === ft) {
      if (t.vehicle_id !== null) return !1;
    } else if (e.vehicle !== "" && t.vehicle_id !== e.vehicle)
      return !1;
    if (e.location !== "" && t.location !== e.location || e.chargeType !== "" && t.charge_type !== e.chargeType || e.status !== "" && t.status !== e.status) return !1;
    if (e.card === Fe) {
      if (t.card_uid !== null) return !1;
    } else if (e.card !== "" && t.card_uid !== e.card)
      return !1;
    return !0;
  });
}
function Ir(i, e) {
  const t = /* @__PURE__ */ new Map();
  for (const r of i)
    t.set(r.id, r.name);
  for (const r of e)
    r.vehicle_id !== null && !t.has(r.vehicle_id) && t.set(r.vehicle_id, r.vehicle_name ?? r.vehicle_id);
  return [...t].map(([r, s]) => ({ value: r, label: s }));
}
function zr(i, e, t) {
  const r = new Set(
    e.map((n) => n.card_uid).filter((n) => n !== null)
  ), s = /* @__PURE__ */ new Map();
  for (const n of i) {
    const a = [...r].find(
      (c) => c !== "" && (n.uid.startsWith(c) || n.uid.endsWith(c))
    );
    s.set(a ?? n.uid, n.label || n.uid);
  }
  for (const n of e)
    n.card_uid !== null && !s.has(n.card_uid) && s.set(n.card_uid, n.card_label || n.card_uid);
  return t !== "" && t !== Fe && !s.has(t) && s.set(t, t), [...s].map(([n, a]) => ({ value: n, label: a }));
}
function Hr(i, e, t) {
  return [.../* @__PURE__ */ new Set([...i, e, t])].sort((r, s) => s - r);
}
function Fr(i) {
  return i.phases_recorded ? i.phases.length === 0 ? "detail_no_phases" : null : "detail_phases_not_recorded";
}
var Vr = Object.defineProperty, se = (i, e, t, r) => {
  for (var s = void 0, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (s = a(e, t, s) || s);
  return s && Vr(e, t, s), s;
};
const Lr = 600 * 1e3, jr = "ev_charging/live/subscribe";
class B extends b {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1, this._activeCount = 0;
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
    }, Lr), this.hass && this._started && this._watchSessions(this.hass), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._started);
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass), this._watchConnection(this.hass));
  }
  // A load that raced a reconnect leaves the card failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(e) {
    this._connectionUnsub || (this._connectionUnsub = fe(e, () => {
      this._failed && this._retry();
    }));
  }
  async _start(e) {
    try {
      this._t = await ie(e);
    } catch (t) {
      console.error("ev_charging: loading translations failed", t), this._t = H({}), this._failed = !0;
      return;
    }
    this._watchSessions(e), await this._load(e, !1);
  }
  // Any running session ending changes the month, so it is worth a reload.
  _watchSessions(e) {
    this._release(), this._unsubscribe = e.connection.subscribeMessage(
      (t) => {
        const r = t.filter((s) => s.active).length;
        r < this._activeCount && this.hass && this._load(this.hass, !0), this._activeCount = r;
      },
      { type: jr }
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
    const { year: r, month: s } = te(/* @__PURE__ */ new Date(), e.config.time_zone);
    try {
      this._sessions = await He(e, { year: r, month: s }), this._failed = !1;
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
    const r = t.locale?.language ?? t.language, { year: s, month: n } = te(/* @__PURE__ */ new Date(), t.config.time_zone), a = this._config.title ?? new Intl.DateTimeFormat(r, { month: "long", year: "numeric", timeZone: "UTC" }).format(
      new Date(Date.UTC(s, n - 1, 1))
    );
    if (this._sessions === void 0)
      return o`<h2>${a}</h2>
        <div class="spinner" role="progressbar"></div>`;
    const c = L(this._sessions), l = Qt(this._sessions);
    return o`
      <h2>${a}</h2>
      <dl>
        ${this._row(e("total_energy"), w(c.energy_kwh, r, c.energy_is_estimate))}
        ${this._row(e("total_cost"), W(c.cost, r, t.config.currency))}
        ${this._row(e("month_solar_share"), T(l, r))}
      </dl>
    `;
  }
  static {
    this.styles = [
      P,
      x`
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
se([
  v({ attribute: !1 })
], B.prototype, "hass");
se([
  p()
], B.prototype, "_config");
se([
  p()
], B.prototype, "_t");
se([
  p()
], B.prototype, "_sessions");
se([
  p()
], B.prototype, "_failed");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Wr = { ATTRIBUTE: 1 }, qr = (i) => (...e) => ({ _$litDirective$: i, values: e });
class Br {
  constructor(e) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(e, t, r) {
    this._$Ct = e, this._$AM = t, this._$Ci = r;
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
const G = qr(class extends Br {
  constructor(i) {
    if (super(i), i.type !== Wr.ATTRIBUTE || i.name !== "class" || i.strings?.length > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
  }
  render(i) {
    return " " + Object.keys(i).filter((e) => i[e]).join(" ") + " ";
  }
  update(i, [e]) {
    if (this.st === void 0) {
      this.st = /* @__PURE__ */ new Set(), i.strings !== void 0 && (this.nt = new Set(i.strings.join(" ").split(/\s/).filter((r) => r !== "")));
      for (const r in e) e[r] && !this.nt?.has(r) && this.st.add(r);
      return this.render(e);
    }
    const t = i.element.classList;
    for (const r of this.st) r in e || (t.remove(r), this.st.delete(r));
    for (const r in e) {
      const s = !!e[r];
      s === this.st.has(r) || this.nt?.has(r) || (s ? (t.add(r), this.st.add(r)) : (t.remove(r), this.st.delete(r)));
    }
    return z;
  }
});
function Te(i, e) {
  return i.vehicle_id === null ? e("unassigned") : i.vehicle_name ?? i.vehicle_id;
}
const Yr = [
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
function Kr(i) {
  return Yr.includes(i);
}
function Zr(i, e) {
  return Kr(i) ? e(`field_${i}`) : i;
}
const Gr = "M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z";
function m(i, e) {
  return e === null || e === "" || e === $ ? d : o`<dt class="muted">${i}</dt>
    <dd>${e}</dd>`;
}
function Jr(i, e) {
  const t = Rr(i);
  return i.address === null && t === null ? null : o`${i.address ?? d}${t === null ? d : o`<a
        class="map"
        href=${t}
        target="_blank"
        rel="noopener noreferrer"
        title=${e("detail_map_link")}
        aria-label=${e("detail_map_link")}
        ><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d=${Gr} fill="currentColor"></path></svg
        >${i.address === null ? e("detail_map_link") : d}</a
      >`}`;
}
function Xr(i, e, t) {
  const r = Fr(i);
  if (r !== null)
    return o`<p class="muted">${e(r)}</p>`;
  const s = t.locale.language, n = t.config.time_zone;
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
      ${i.phases.map(
    (a) => o`<tr>
          <td>${de(a.start, s, n)}</td>
          <td>${de(a.end, s, n)}</td>
          <td class="num">${E(a.duration_min)}</td>
          <td class="num">${w(a.energy_kwh, s)}</td>
          <td class="num">${W(a.cost, s, t.config.currency)}</td>
        </tr>`
  )}
    </tbody>
  </table>`;
}
function mt(i, e, t) {
  const r = t.locale.language, s = t.config.time_zone, n = e("detail_not_recorded"), a = i.soc_start === null && i.soc_end === null ? null : `${T(i.soc_start, r)} → ${T(i.soc_end, r)}`;
  return o`<div class="body">
    <dl>
      ${m(e("detail_plug_start"), q(i.plug_start, r, s))}
      ${m(e("detail_plug_end"), q(i.plug_end, r, s))}
      ${m(e("detail_plug_duration"), E(i.plug_duration_min))}
      ${m(e("detail_charge_duration"), E(i.charge_duration_min))}
      ${i.pause_duration_min ? m(e("detail_pause_duration"), E(i.pause_duration_min)) : d}
      ${m(e("detail_soc"), a)}
      ${m(e("detail_odometer"), Ie(i.odometer_km, r))}
      ${m(e("detail_power_avg"), pt(i.power_avg_kw, r))}
      ${i.location === "home" ? o`${m(
    e("detail_energy_grid"),
    i.energy_grid_kwh === null ? n : w(i.energy_grid_kwh, r)
  )}
          ${m(
    e("detail_energy_solar"),
    i.energy_solar_kwh === null ? n : w(i.energy_solar_kwh, r)
  )}` : d}
      ${i.energy_unallocated_kwh > 0 ? m(e("detail_energy_unallocated"), w(i.energy_unallocated_kwh, r)) : d}
      ${m(e("detail_card"), i.card_label ?? i.card_uid)}
      ${m(e("detail_identification"), e(`identification_${i.identification_source}`))}
      ${m(e("detail_address"), Jr(i, e))}
      ${m(e("detail_provider"), i.provider)}
      ${m(e("detail_note"), i.note)}
      ${i.open_fields.length > 0 ? m(
    e("detail_open_fields"),
    i.open_fields.map((c) => Zr(c, e)).join(", ")
  ) : d}
    </dl>
    ${Xr(i, e, t)}
  </div>`;
}
const vt = x`
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
var Qr = Object.defineProperty, Ve = (i, e, t, r) => {
  for (var s = void 0, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (s = a(e, t, s) || s);
  return s && Qr(e, t, s), s;
};
class ge extends b {
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
    const r = this.hass, s = r.locale.language, n = e.soc_start !== null && e.soc_end !== null ? `${T(e.soc_start, s)} → ${T(e.soc_end, s)}` : d;
    return o`<li>
      <details>
        <summary>
          <div class="line">
            <span class=${G({ vehicle: !0, unassigned: e.vehicle_id === null })}
              >${Te(e, t)}</span
            >
            <span class="muted"
              >${q(e.plug_start, s, r.config.time_zone)}</span
            >
          </div>
          <div class="line">
            <span>
              ${w(e.energy_kwh, s, e.energy_is_estimate)} ·
              ${W(e.cost, s, r.config.currency)} ·
              ${E(e.charge_duration_min)}
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
        ${mt(e, t, r)}
      </details>
    </li>`;
  }
  static {
    this.styles = [
      P,
      vt,
      x`
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
Ve([
  v({ attribute: !1 })
], ge.prototype, "hass");
Ve([
  v({ attribute: !1 })
], ge.prototype, "t");
Ve([
  v({ attribute: !1 })
], ge.prototype, "sessions");
const $t = [
  "soc_start",
  "soc_end",
  "odometer_km",
  "energy_billed_kwh",
  "cost",
  "charge_type",
  "address",
  "note",
  "provider",
  "plug_end"
], ei = {
  soc_start: ["soc_start"],
  soc_end: ["soc_end"],
  odometer_km: ["odometer_km"],
  cost: ["cost"],
  energy_kwh: ["soc_start", "soc_end", "energy_billed_kwh"]
};
function ti(i) {
  const e = /* @__PURE__ */ new Set();
  for (const t of i.open_fields)
    for (const r of ei[t] ?? [])
      e.add(r);
  return $t.filter((t) => e.has(t));
}
function ri(i) {
  return $t.filter((e) => e === "charge_type" ? i.charge_type_source === "heuristic" : e === "plug_end" ? i.plug_end === null : !0);
}
function k(i, e) {
  return o`<label class="edit-row"><span class="muted">${i}</span>${e}</label>`;
}
function Z(i, e, t, r, s, n) {
  return o`<input
    type="number"
    min=${r}
    max=${s ?? d}
    step=${n}
    .value=${e}
    @input=${(a) => t(i, a.target.value)}
  />`;
}
function Se(i, e, t) {
  return o`<input
    type="text"
    .value=${e}
    @input=${(r) => t(i, r.target.value)}
  />`;
}
function ii(i, e, t, r, s) {
  const n = t[e] ?? "";
  switch (e) {
    case "soc_start":
      return k(s("field_soc_start"), Z(e, n, r, 0, 100, "0.1"));
    case "soc_end":
      return k(s("field_soc_end"), Z(e, n, r, 0, 100, "0.1"));
    case "odometer_km":
      return k(s("field_odometer_km"), Z(e, n, r, 0, void 0, "0.1"));
    case "energy_billed_kwh":
      return k(
        s("field_energy_billed_kwh"),
        Z(e, n, r, 0, void 0, "0.001")
      );
    case "cost":
      return k(s("field_cost"), Z(e, n, r, 0, void 0, "0.01"));
    case "charge_type":
      return i.charge_type_source !== "heuristic" ? d : k(
        s("filter_charge_type"),
        o`<select
          @change=${(a) => r(e, a.target.value)}
        >
          <option value="" .selected=${n === ""}>${s("filter_all")}</option>
          <option value="ac" .selected=${n === "ac"}>${s("charge_type_ac")}</option>
          <option value="dc" .selected=${n === "dc"}>${s("charge_type_dc")}</option>
        </select>`
      );
    case "address":
      return k(s("detail_address"), Se(e, n, r));
    case "note":
      return k(s("detail_note"), Se(e, n, r));
    case "provider":
      return k(s("detail_provider"), Se(e, n, r));
    case "plug_end":
      return i.plug_end !== null ? d : k(
        s("detail_plug_end"),
        o`<input
          type="datetime-local"
          .value=${n}
          @input=${(a) => r(e, a.target.value)}
        />`
      );
    default:
      return d;
  }
}
function st(i, e, t, r, s) {
  return o`<div class="edit-fields">
    ${e.map((n) => ii(i, n, t, r, s))}
  </div>`;
}
function ke(i, e, t, r) {
  return o`<select
    @change=${(s) => t(s.target.value)}
  >
    <option value="" .selected=${e === ""}>${r("edit_select_vehicle")}</option>
    ${i.map(
    (s) => o`<option value=${s.id} .selected=${s.id === e}>
          ${s.name}
        </option>`
  )}
  </select>`;
}
function yt(i) {
  const e = {};
  return i.soc_start && (e.soc_start = Number(i.soc_start)), i.soc_end && (e.soc_end = Number(i.soc_end)), i.odometer_km && (e.odometer_km = Number(i.odometer_km)), i.energy_billed_kwh && (e.energy_billed_kwh = Number(i.energy_billed_kwh)), i.cost && (e.cost = Number(i.cost)), i.charge_type && (e.charge_type = i.charge_type), i.address && (e.address = i.address), i.note && (e.note = i.note), i.provider && (e.provider = i.provider), i.plug_end && (e.plug_end = new Date(i.plug_end).toISOString()), e;
}
function nt(i) {
  return Object.keys(yt(i)).length > 0;
}
const si = x`
  .edit-form {
    margin: 8px 0;
    padding: 12px 14px;
    background: var(--ev-head-bg);
    border: 1px solid var(--ev-line);
    border-radius: var(--ev-radius);
  }

  .edit-fields {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px 16px;
    margin: 8px 0;
  }

  .edit-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.9em;
  }

  .edit-row input,
  .edit-row select {
    padding: 6px 8px;
    background: var(--ev-surface);
    border: 1px solid var(--ev-line);
    border-radius: 8px;
    font: inherit;
    color: inherit;
  }

  .edit-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
  }

  .edit-vehicle {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  button.danger {
    border-color: var(--error-color, #db4437);
    color: var(--error-color, #db4437);
  }

  .edit-message {
    font-size: 0.85em;
  }

  .edit-message.error {
    color: var(--error-color, #db4437);
  }
`;
var ni = Object.defineProperty, g = (i, e, t, r) => {
  for (var s = void 0, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (s = a(e, t, s) || s);
  return s && ni(e, t, s), s;
};
const ai = 600 * 1e3, oi = 5, Ee = "__create__", li = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z", ci = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z", di = [
  { id: "overview", label: "view_overview" },
  { id: "recent", label: "view_recent" },
  { id: "detail", label: "view_detail" },
  { id: "followup", label: "view_followup" },
  { id: "correction", label: "view_correction" }
], at = ["home", "home_no_wallbox", "external"], hi = ["ac", "dc", "unknown"], ui = ["complete", "followup_open", "flagged"], pi = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" }
];
function ot(i) {
  return o`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${i} fill="currentColor"></path>
  </svg>`;
}
const f = class Ue extends b {
  constructor() {
    super(...arguments), this._years = [], this._vehicles = [], this._failed = !1, this._metric = "energy", this._editingId = null, this._editValues = {}, this._vehicleDraft = {}, this._busyId = null, this._editError = {}, this._creating = !1, this._createValues = {}, this._started = !1, this._recentRequested = !1, this._openRequested = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => this._refresh(), ai), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._state !== void 0);
  }
  willUpdate(e) {
    if (e.has("hass") && this.hass && this._state === void 0) {
      const t = this.initialState;
      this._state = {
        ...Ar(/* @__PURE__ */ new Date(), this.hass.config.time_zone),
        ...t,
        filters: { ...he, ...t?.filters }
      };
    }
    this._sync();
  }
  _sync() {
    const e = this.hass, t = this._state;
    !e || !t || (this._watchConnection(e), this._started || (this._started = !0, this._loadShared(e, !1)), t.view !== "recent" && t.view !== "followup" && this._yearKey !== t.year && (this._yearKey = t.year, this._yearSessions = void 0, this._loadYear(e, t.year, !1)), t.view === "recent" && !this._recentRequested && (this._recentRequested = !0, this._loadRecent(e, !1)), t.view === "followup" && !this._openRequested && (this._openRequested = !0, this._loadOpenSessions(e, !1)));
  }
  _refresh() {
    const e = this.hass, t = this._state;
    !e || !t || !this._started || this._failed || (this._loadShared(e, !0), t.view !== "recent" && t.view !== "followup" && this._loadYear(e, t.year, !0), t.view === "recent" && this._loadRecent(e, !0), t.view === "followup" && this._loadOpenSessions(e, !0));
  }
  _fail(e, t) {
    console.error("ev_charging: loading data failed", e), t || (this._failed = !0);
  }
  _retry() {
    this._failed = !1, this._started = !1, this._yearKey = void 0, this._recentRequested = !1, this._openRequested = !1, this.requestUpdate();
  }
  // A load that raced a reconnect leaves the view failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(e) {
    this._connectionUnsub || (this._connectionUnsub = fe(e, () => {
      this._failed && this._retry();
    }));
  }
  async _loadShared(e, t) {
    try {
      this._t = await ie(e);
    } catch (r) {
      this._t = H({}), this._fail(r, t);
      return;
    }
    try {
      this._vehicles = await br(e);
    } catch (r) {
      this._fail(r, t);
    }
  }
  async _loadYear(e, t, r) {
    try {
      const s = await yr(e, t);
      this._yearKey === t && (this._yearSessions = s.sessions, this._years = s.years);
    } catch (s) {
      this._yearKey === t && this._fail(s, r);
    }
  }
  async _loadRecent(e, t) {
    try {
      this._recent = await He(e, { limit: oi });
    } catch (r) {
      this._fail(r, t);
    }
  }
  async _loadOpenSessions(e, t) {
    try {
      this._openSessions = await wr(e);
    } catch (r) {
      this._fail(r, t);
    }
  }
  _setState(e) {
    this._state && (this._state = { ...this._state, ...e }, this.dispatchEvent(new CustomEvent("ev-state-changed", { detail: this._state })));
  }
  _setFilter(e, t) {
    this._state && this._setState({ filters: { ...this._state.filters, [e]: t } });
  }
  _shift(e) {
    this._state && this._setState(Tr(this._state.year, this._state.month, e));
  }
  render() {
    const e = this._state;
    if (!e || !this.hass)
      return d;
    if (this._failed)
      return this._renderError(this._t ?? H({}));
    const t = this._t;
    if (!t)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = e.view === "overview" || e.view === "detail" || e.view === "correction";
    return o`
      <div class="view">
        ${this._renderTabs(t, e)}
        ${r ? this._renderFilters(t, e) : d}
        ${r ? this._renderPeriod(t, e) : d}
        ${e.view === "overview" ? this._renderOverview(t, e) : e.view === "detail" ? this._renderDetail(t, e) : e.view === "followup" ? this._renderFollowup(t) : e.view === "correction" ? this._renderCorrection(t, e) : this._renderRecent(t)}
        <p class="hint muted">${t("multi_day_hint")} ${t("estimate_hint")}</p>
      </div>
    `;
  }
  _renderError(e) {
    return o`<div class="message">
      <span>${e("load_error")}</span>
      <button class="text" @click=${() => this._retry()}>${e("retry")}</button>
    </div>`;
  }
  _renderTabs(e, t) {
    return o`<nav class="tabs">
      ${di.map(
      (r) => o`<button
          class=${G({ tab: !0, active: r.id === t.view })}
          aria-current=${r.id === t.view ? "page" : "false"}
          @click=${() => this._setState({ view: r.id })}
        >
          ${e(r.label)}
        </button>`
    )}
    </nav>`;
  }
  _renderPeriod(e, t) {
    const r = this.hass, s = r.locale.language, n = te(/* @__PURE__ */ new Date(), r.config.time_zone), a = Hr(this._years, n.year, t.year);
    return o`<div class="period">
      <button class="icon" aria-label=${e("period_previous")} @click=${() => this._shift(-1)}>
        ${ot(li)}
      </button>
      <select
        aria-label=${e("period_month")}
        @change=${(c) => this._setState({ month: Number(c.target.value) })}
      >
        ${Array.from({ length: 12 }, (c, l) => l + 1).map(
      (c) => o`<option value=${c} .selected=${c === t.month}>
              ${ye(c, s, "long")}
            </option>`
    )}
      </select>
      <select
        aria-label=${e("period_year")}
        @change=${(c) => this._setState({ year: Number(c.target.value) })}
      >
        ${a.map(
      (c) => o`<option value=${c} .selected=${c === t.year}>${c}</option>`
    )}
      </select>
      <button class="icon" aria-label=${e("period_next")} @click=${() => this._shift(1)}>
        ${ot(ci)}
      </button>
    </div>`;
  }
  _renderTiles(e, t) {
    const r = this.hass, s = r.locale.language, n = [
      ["total_energy", w(t.energy_kwh, s, t.energy_is_estimate)],
      ["total_cost", W(t.cost, s, r.config.currency)],
      ["total_duration", E(t.charge_duration_min)],
      ["total_sessions", String(t.count)],
      ["open_followups", String(t.open_followups)]
    ];
    return o`<div class="tiles">
      ${n.map(
      ([a, c]) => o`<div class="tile">
          <span class="tile-label muted">${e(a)}</span>
          <span class="tile-value">${c}</span>
        </div>`
    )}
    </div>`;
  }
  // Sessions of the selected year that pass the filters.
  _filteredYear(e) {
    return xe(this._yearSessions ?? [], e.filters);
  }
  _renderOverview(e, t) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = this._filteredYear(t), s = this.hass.config.time_zone, n = Or(r, s);
    return o`
      ${this._renderTiles(e, n[t.month - 1])}
      ${this._renderChart(e, t, n)}
      ${this._renderYearSummary(e, t, Dr(r))}
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
    const t = this.hass, r = t.locale.language;
    switch (this._metric) {
      case "cost":
        return rt(e.cost, r, t.config.currency);
      case "duration":
        return it(e.charge_duration_min);
      default:
        return tt(e.energy_kwh, r, e.energy_is_estimate);
    }
  }
  _renderChart(e, t, r) {
    const s = this.hass.locale.language, n = Math.max(...r.map((a) => this._metricValue(a)), 0);
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
            ${pi.map(
      (a) => o`<option value=${a.id} .selected=${a.id === this._metric}>
                  ${e(a.label)}
                </option>`
    )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${r.map((a) => {
      const c = n > 0 ? this._metricValue(a) / n * 100 : 0, l = ye(a.month, s, "long"), h = a.count === 0 ? $ : this._formatMetric(a);
      return o`<button
            class=${G({ bar: !0, selected: a.month === t.month })}
            title=${`${l}: ${h}`}
            aria-label=${`${l}: ${h}`}
            aria-pressed=${a.month === t.month ? "true" : "false"}
            @click=${() => this._setState({ month: a.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${c}%`}></span></span>
            <span class="bar-label muted">${ye(a.month, s, "short")}</span>
            <span class="bar-value">${h}</span>
          </button>`;
    })}
      </div>
    </section>`;
  }
  _renderYearSummary(e, t, r) {
    const s = this.hass, n = s.locale.language, a = [
      ["scope_total", r.all],
      ["scope_internal", r.internal],
      ["scope_external", r.external]
    ], c = [
      ["total_energy", (l) => tt(l.energy_kwh, n, l.energy_is_estimate)],
      ["total_cost", (l) => rt(l.cost, n, s.config.currency)],
      ["total_duration", (l) => it(l.charge_duration_min)],
      ["total_sessions", (l) => String(l.count)]
    ];
    return o`<section class="year-summary">
      <h3>${e("year_summary_title", { year: t.year })}</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            ${a.map(([l]) => o`<th class="num">${e(l)}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${c.map(
      ([l, h]) => o`<tr>
              <th>${e(l)}</th>
              ${a.map(([, _]) => o`<td class="num">${h(_)}</td>`)}
            </tr>`
    )}
        </tbody>
      </table>
    </section>`;
  }
  _renderFilters(e, t) {
    const r = this._yearSessions ?? [], s = t.filters, n = [
      ...Ir(this._vehicles, r),
      { value: ft, label: e("unassigned") }
    ], a = [
      { value: Fe, label: e("filter_no_card") },
      ...zr(
        this._vehicles.flatMap((c) => c.cards),
        r,
        s.card
      )
    ];
    return o`<div class="filters">
      ${this._renderFilter(e("filter_vehicle"), "vehicle", n, e)}
      ${this._renderFilter(
      e("filter_location"),
      "location",
      at.map((c) => ({ value: c, label: e(`location_${c}`) })),
      e
    )}
      ${this._renderFilter(
      e("filter_charge_type"),
      "chargeType",
      hi.map((c) => ({ value: c, label: e(`charge_type_${c}`) })),
      e
    )}
      ${this._renderFilter(e("filter_card"), "card", a, e)}
      ${this._renderFilter(
      e("filter_status"),
      "status",
      ui.map((c) => ({ value: c, label: e(`status_${c}`) })),
      e
    )}
      ${Nr(s) ? o`<button
            class="text reset"
            @click=${() => this._setState({ filters: { ...he } })}
          >
            ${e("filter_reset")}
          </button>` : d}
    </div>`;
  }
  _renderDetail(e, t) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = this.hass.config.time_zone, s = Ae(this._yearSessions, t.month, r), n = xe(s, t.filters);
    return o`
      ${this._renderTiles(e, L(n))}
      <p class="count muted">
        ${e("filter_count", { shown: n.length, total: s.length })}
      </p>
      ${n.length === 0 ? o`<div class="message">
            ${s.length === 0 ? e("no_sessions") : e("no_sessions_filtered")}
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
  // ----------------------------------------------------------- nacherfassung
  _setDraft(e, t, r) {
    this._editValues = { ...this._editValues, [e]: { ...this._editValues[e], [t]: r } };
  }
  _setVehicleDraft(e, t) {
    this._vehicleDraft = { ...this._vehicleDraft, [e]: t };
  }
  static _omit(e, t) {
    const r = { ...e };
    return delete r[t], r;
  }
  async _run(e, t, r) {
    this._busyId = e;
    try {
      await t(), this._editValues = Ue._omit(this._editValues, e), this._editError = Ue._omit(this._editError, e), await r();
    } catch (s) {
      console.error("ev_charging: session correction failed", s), this._editError = { ...this._editError, [e]: this._t?.("edit_error") ?? "error" };
    } finally {
      this._busyId = null;
    }
  }
  async _saveUpdate(e, t) {
    const r = yt(this._editValues[e.id] ?? {});
    Object.keys(r).length !== 0 && await this._run(e.id, () => xr(this.hass, e.id, r), t);
  }
  async _saveVehicle(e, t) {
    const r = this._vehicleDraft[e.id];
    r && await this._run(e.id, () => Er(this.hass, e.id, r), t);
  }
  async _accept(e, t) {
    await this._run(e.id, () => kr(this.hass, e.id), t);
  }
  async _remove(e, t) {
    window.confirm(this._t?.("edit_delete_confirm") ?? "") && (this._editingId = null, await this._run(
      e.id,
      async () => {
        await Sr(this.hass, e.id);
      },
      t
    ));
  }
  _renderFollowup(e) {
    const t = this._openSessions;
    if (!t)
      return o`<div class="spinner" role="progressbar"></div>`;
    if (t.length === 0)
      return o`<div class="message">${e("followup_empty")}</div>`;
    const r = () => this._loadOpenSessions(this.hass, !0);
    return o`<div class="followup-list">
      ${t.map((s) => this._renderFollowupRow(s, e, r))}
    </div>`;
  }
  _renderFollowupRow(e, t, r) {
    const s = this.hass, n = s.locale.language, a = s.config.time_zone, c = ti(e), l = this._editValues[e.id] ?? {}, h = this._busyId === e.id, _ = this._editError[e.id];
    return o`<div class="followup-row">
      <div class="followup-head">
        <span class=${G({ vehicle: !0, unassigned: e.vehicle_id === null })}
          >${Te(e, t)}</span
        >
        <span class="muted">${q(e.plug_start, n, a)}</span>
        <span class="chip">${t(`location_${e.location}`)}</span>
      </div>
      ${e.open_fields.includes("vehicle_id") ? o`<div class="edit-vehicle">
            ${ke(
      this._vehicles,
      this._vehicleDraft[e.id] ?? "",
      (u) => this._setVehicleDraft(e.id, u),
      t
    )}
            <button
              class="text"
              ?disabled=${h || !this._vehicleDraft[e.id]}
              @click=${() => this._saveVehicle(e, r)}
            >
              ${t("edit_assign_vehicle")}
            </button>
          </div>` : d}
      ${c.length > 0 ? st(
      e,
      c,
      l,
      (u, y) => this._setDraft(e.id, u, y),
      t
    ) : d}
      <div class="edit-actions">
        ${c.length > 0 ? o`<button
              class="text"
              ?disabled=${h || !nt(l)}
              @click=${() => this._saveUpdate(e, r)}
            >
              ${t("edit_save")}
            </button>` : d}
        <button class="text" ?disabled=${h} @click=${() => this._accept(e, r)}>
          ${t("edit_accept")}
        </button>
        ${_ ? o`<span class="edit-message error">${_}</span>` : d}
      </div>
    </div>`;
  }
  // -------------------------------------------------------------- korrektur
  _toggleEdit(e) {
    this._editingId = this._editingId === e ? null : e;
  }
  _toggleCreate() {
    this._creating = !this._creating, this._creating || (this._createValues = {});
  }
  async _createNew(e) {
    const t = this._createValues;
    if (!t.location || !t.plug_start || !t.plug_end)
      return;
    const r = {
      location: t.location,
      plug_start: new Date(t.plug_start).toISOString(),
      plug_end: new Date(t.plug_end).toISOString()
    };
    t.vehicle_id && (r.vehicle_id = t.vehicle_id), t.soc_start && (r.soc_start = Number(t.soc_start)), t.soc_end && (r.soc_end = Number(t.soc_end)), t.odometer_km && (r.odometer_km = Number(t.odometer_km)), t.energy_billed_kwh && (r.energy_billed_kwh = Number(t.energy_billed_kwh)), t.charge_type && (r.charge_type = t.charge_type), t.cost && (r.cost = Number(t.cost)), t.address && (r.address = t.address), t.note && (r.note = t.note), t.provider && (r.provider = t.provider), await this._run(Ee, () => Cr(this.hass, r), e), this._creating = !1, this._createValues = {};
  }
  _renderCorrection(e, t) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = this.hass.config.time_zone, s = Ae(this._yearSessions, t.month, r), n = xe(s, t.filters), a = () => this._loadYear(this.hass, t.year, !0);
    return o`
      <div class="edit-actions">
        <button class="text" @click=${() => this._toggleCreate()}>
          ${e("edit_new_session")}
        </button>
      </div>
      ${this._creating ? this._renderCreateForm(e, a) : d}
      <p class="count muted">
        ${e("filter_count", { shown: n.length, total: s.length })}
      </p>
      ${n.length === 0 ? o`<div class="message">
            ${s.length === 0 ? e("no_sessions") : e("no_sessions_filtered")}
          </div>` : this._renderCorrectionTable(n, e, a)}
    `;
  }
  _renderCorrectionTable(e, t, r) {
    return o`<div class="correction-table">
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
      ${e.map((s) => this._renderCorrectionRow(s, t, r))}
    </div>`;
  }
  _renderCorrectionRow(e, t, r) {
    const s = this._editingId === e.id, n = this._editError[e.id];
    return o`<div class="correction-item">
      ${this._renderSession(e, t)}
      <div class="edit-actions">
        <button class="text" @click=${() => this._toggleEdit(e.id)}>
          ${t(s ? "edit_cancel" : "edit_edit")}
        </button>
        <button
          class="text danger"
          ?disabled=${this._busyId === e.id}
          @click=${() => this._remove(e, r)}
        >
          ${t("edit_delete")}
        </button>
        ${n ? o`<span class="edit-message error">${n}</span>` : d}
      </div>
      ${s ? this._renderCorrectionForm(e, t, r) : d}
    </div>`;
  }
  _renderCorrectionForm(e, t, r) {
    const s = this._editValues[e.id] ?? {}, n = this._busyId === e.id, a = ri(e), c = this._vehicleDraft[e.id] ?? e.vehicle_id ?? "";
    return o`<div class="edit-form">
      <div class="edit-vehicle">
        ${ke(
      this._vehicles,
      c,
      (l) => this._setVehicleDraft(e.id, l),
      t
    )}
        <button
          class="text"
          ?disabled=${n || !c || c === e.vehicle_id}
          @click=${() => this._saveVehicle(e, r)}
        >
          ${t("edit_assign_vehicle")}
        </button>
      </div>
      ${st(
      e,
      a,
      s,
      (l, h) => this._setDraft(e.id, l, h),
      t
    )}
      <div class="edit-actions">
        <button
          class="text"
          ?disabled=${n || !nt(s)}
          @click=${() => this._saveUpdate(e, r)}
        >
          ${t("edit_save")}
        </button>
        ${e.status === "followup_open" || e.open_fields.length > 0 ? o`<button class="text" ?disabled=${n} @click=${() => this._accept(e, r)}>
              ${t("edit_accept")}
            </button>` : d}
      </div>
    </div>`;
  }
  _renderCreateForm(e, t) {
    const r = this._createValues, s = (l, h) => {
      this._createValues = { ...this._createValues, [l]: h };
    }, n = this._busyId === Ee, a = this._editError[Ee], c = !!(r.location && r.plug_start && r.plug_end);
    return o`<div class="edit-form">
      <div class="edit-fields">
        <label class="edit-row">
          <span class="muted">${e("filter_location")}</span>
          <select @change=${(l) => s("location", l.target.value)}>
            <option value="" .selected=${!r.location}>${e("filter_all")}</option>
            ${at.map(
      (l) => o`<option value=${l} .selected=${r.location === l}>
                  ${e(`location_${l}`)}
                </option>`
    )}
          </select>
        </label>
        <label class="edit-row">
          <span class="muted">${e("detail_plug_start")}</span>
          <input
            type="datetime-local"
            .value=${r.plug_start ?? ""}
            @input=${(l) => s("plug_start", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("detail_plug_end")}</span>
          <input
            type="datetime-local"
            .value=${r.plug_end ?? ""}
            @input=${(l) => s("plug_end", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("filter_vehicle")}</span>
          ${ke(
      this._vehicles,
      r.vehicle_id ?? "",
      (l) => s("vehicle_id", l),
      e
    )}
        </label>
        <label class="edit-row">
          <span class="muted">${e("field_soc_start")}</span>
          <input
            type="number"
            min="0"
            max="100"
            step="0.1"
            .value=${r.soc_start ?? ""}
            @input=${(l) => s("soc_start", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("field_soc_end")}</span>
          <input
            type="number"
            min="0"
            max="100"
            step="0.1"
            .value=${r.soc_end ?? ""}
            @input=${(l) => s("soc_end", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("field_odometer_km")}</span>
          <input
            type="number"
            min="0"
            step="0.1"
            .value=${r.odometer_km ?? ""}
            @input=${(l) => s("odometer_km", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("field_energy_billed_kwh")}</span>
          <input
            type="number"
            min="0"
            step="0.001"
            .value=${r.energy_billed_kwh ?? ""}
            @input=${(l) => s("energy_billed_kwh", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("filter_charge_type")}</span>
          <select
            @change=${(l) => s("charge_type", l.target.value)}
          >
            <option value="" .selected=${!r.charge_type}>${e("filter_all")}</option>
            <option value="ac" .selected=${r.charge_type === "ac"}>${e("charge_type_ac")}</option>
            <option value="dc" .selected=${r.charge_type === "dc"}>${e("charge_type_dc")}</option>
          </select>
        </label>
        <label class="edit-row">
          <span class="muted">${e("field_cost")}</span>
          <input
            type="number"
            min="0"
            step="0.01"
            .value=${r.cost ?? ""}
            @input=${(l) => s("cost", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("detail_address")}</span>
          <input
            type="text"
            .value=${r.address ?? ""}
            @input=${(l) => s("address", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("detail_provider")}</span>
          <input
            type="text"
            .value=${r.provider ?? ""}
            @input=${(l) => s("provider", l.target.value)}
          />
        </label>
        <label class="edit-row">
          <span class="muted">${e("detail_note")}</span>
          <input
            type="text"
            .value=${r.note ?? ""}
            @input=${(l) => s("note", l.target.value)}
          />
        </label>
      </div>
      <div class="edit-actions">
        <button class="text" ?disabled=${n || !c} @click=${() => this._createNew(t)}>
          ${e("edit_create")}
        </button>
        ${a ? o`<span class="edit-message error">${a}</span>` : d}
      </div>
    </div>`;
  }
  _renderFilter(e, t, r, s) {
    const n = this._state.filters[t];
    return o`<label class="filter">
      <span class="muted">${e}</span>
      <select
        @change=${(a) => this._setFilter(t, a.target.value)}
      >
        <option value="" .selected=${n === ""}>${s("filter_all")}</option>
        ${r.map(
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
      ${e.map((r) => this._renderSession(r, t))}
    </div>`;
  }
  _renderSession(e, t) {
    const r = this.hass, s = r.locale.language, n = r.config.time_zone, a = e.vehicle_id === null;
    return o`<details class="session">
      <summary>
        <span class="c-date">${q(e.plug_start, s, n)}</span>
        <span class=${G({ "c-vehicle": !0, vehicle: !0, unassigned: a })}
          >${Te(e, t)}</span
        >
        <span class="c-location"><span class="chip">${t(`location_${e.location}`)}</span></span>
        <span class="c-type"><span class="chip">${t(`charge_type_${e.charge_type}`)}</span></span>
        <span class="c-energy num"
          >${w(e.energy_kwh, s, e.energy_is_estimate)}</span
        >
        <span class="c-cost num">${W(e.cost, s, r.config.currency)}</span>
        <span class="c-duration num">${E(e.charge_duration_min)}</span>
        <span class="c-status">
          ${e.status === "complete" ? d : o`<span class="chip warn">${t(`status_${e.status}`)}</span>`}
          ${e.location_conflict ? o`<span class="chip alert">${t("flag_location_conflict")}</span>` : d}
          ${e.identification_conflict ? o`<span class="chip alert">${t("flag_identification_conflict")}</span>` : d}
          ${e.charge_error ? o`<span class="chip alert">${t("flag_charge_error")}</span>` : d}
          ${e.energy_unallocated_kwh > 0 ? o`<span class="chip warn">${t("flag_unallocated_energy")}</span>` : d}
        </span>
      </summary>
      ${mt(e, t, r)}
    </details>`;
  }
  static {
    this.styles = [
      P,
      vt,
      si,
      x`
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

      .followup-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .followup-row {
        padding: 12px 14px;
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
      }

      .followup-head {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 12px;
      }

      .followup-head .vehicle {
        font-weight: 500;
      }

      .correction-table .head {
        margin-bottom: 12px;
        border-radius: var(--ev-radius) var(--ev-radius) 0 0;
      }

      .correction-item {
        margin-bottom: 12px;
        border: 1px solid var(--ev-line);
        border-radius: var(--ev-radius);
        overflow: hidden;
      }

      .correction-item .edit-actions,
      .correction-item .edit-form {
        margin: 0;
        padding: 10px 14px;
      }

      .correction-item .edit-form {
        border: none;
        border-top: 1px solid var(--ev-line);
        border-radius: 0;
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
};
g([
  v({ attribute: !1 })
], f.prototype, "hass");
g([
  v({ attribute: !1 })
], f.prototype, "initialState");
g([
  p()
], f.prototype, "_state");
g([
  p()
], f.prototype, "_t");
g([
  p()
], f.prototype, "_yearSessions");
g([
  p()
], f.prototype, "_years");
g([
  p()
], f.prototype, "_recent");
g([
  p()
], f.prototype, "_vehicles");
g([
  p()
], f.prototype, "_failed");
g([
  p()
], f.prototype, "_metric");
g([
  p()
], f.prototype, "_openSessions");
g([
  p()
], f.prototype, "_editingId");
g([
  p()
], f.prototype, "_editValues");
g([
  p()
], f.prototype, "_vehicleDraft");
g([
  p()
], f.prototype, "_busyId");
g([
  p()
], f.prototype, "_editError");
g([
  p()
], f.prototype, "_creating");
g([
  p()
], f.prototype, "_createValues");
let _i = f;
var fi = Object.defineProperty, me = (i, e, t, r) => {
  for (var s = void 0, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (s = a(e, t, s) || s);
  return s && fi(e, t, s), s;
};
const gi = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
class ne extends b {
  constructor() {
    super(...arguments), this.narrow = !1;
  }
  willUpdate() {
    this._initialState === void 0 && (this._initialState = Pr(this.route?.path ?? "", window.location.search));
  }
  _toggleMenu() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: !0, composed: !0 }));
  }
  _onStateChanged(e) {
    const t = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${t}${Ur(e.detail)}`);
  }
  render() {
    return o`
      <header>
        ${this.narrow ? o`<button class="menu" @click=${() => this._toggleMenu()}>
              <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d=${gi} fill="currentColor"></path>
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
      x`
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
me([
  v({ attribute: !1 })
], ne.prototype, "hass");
me([
  v({ type: Boolean })
], ne.prototype, "narrow");
me([
  v({ attribute: !1 })
], ne.prototype, "route");
me([
  v({ attribute: !1 })
], ne.prototype, "panel");
var mi = Object.defineProperty, bt = (i, e, t, r) => {
  for (var s = void 0, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (s = a(e, t, s) || s);
  return s && mi(e, t, s), s;
};
class Le extends b {
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
      x`
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
bt([
  v({ attribute: !1 })
], Le.prototype, "hass");
bt([
  v({ type: Boolean, reflect: !0, attribute: "is-panel" })
], Le.prototype, "isPanel");
var vi = Object.defineProperty, O = (i, e, t, r) => {
  for (var s = void 0, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (s = a(e, t, s) || s);
  return s && vi(e, t, s), s;
};
const V = 3, je = 20, $i = 600 * 1e3;
function wt(i) {
  return Number.isInteger(i) && i >= 1 && i <= je;
}
class Y extends b {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1;
  }
  setConfig(e) {
    if (!wt(e.count ?? V))
      throw new Error(`count must be a whole number from 1 to ${je}`);
    this._config = e, this._started && this.hass && this._load(this.hass, !0);
  }
  getCardSize() {
    return 1 + (this._config.count ?? V) * 2;
  }
  static getStubConfig() {
    return { count: V };
  }
  static getConfigElement() {
    return document.createElement("ev-charging-recent-card-editor");
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => {
      this.hass && this._started && !this._failed && this._load(this.hass, !0);
    }, $i), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one loads.
  shouldUpdate(e) {
    return !(e.size === 1 && e.has("hass") && this._started);
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass), this._watchConnection(this.hass));
  }
  // A load that raced a reconnect leaves the card failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(e) {
    this._connectionUnsub || (this._connectionUnsub = fe(e, () => {
      this._failed && this._retry();
    }));
  }
  async _start(e) {
    try {
      this._t = await ie(e);
    } catch (t) {
      console.error("ev_charging: loading translations failed", t), this._t = H({}), this._failed = !0;
      return;
    }
    await this._load(e, !1);
  }
  async _load(e, t) {
    try {
      this._sessions = await He(e, { limit: this._config.count ?? V }), this._failed = !1;
    } catch (r) {
      console.error("ev_charging: loading sessions failed", r), t || (this._failed = !0);
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
      x`
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
O([
  v({ attribute: !1 })
], Y.prototype, "hass");
O([
  p()
], Y.prototype, "_config");
O([
  p()
], Y.prototype, "_t");
O([
  p()
], Y.prototype, "_sessions");
O([
  p()
], Y.prototype, "_failed");
class ve extends b {
  constructor() {
    super(...arguments), this._config = {}, this._started = !1;
  }
  setConfig(e) {
    this._config = e;
  }
  willUpdate(e) {
    e.has("hass") && this.hass && !this._started && (this._started = !0, ie(this.hass).then(
      (t) => this._t = t,
      () => this._t = H({})
    ));
  }
  _changed(e) {
    const t = Number(e.target.value);
    if (!wt(t)) {
      e.target.value = String(this._config.count ?? V);
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
        max=${je}
        step="1"
        .value=${String(this._config.count ?? V)}
        @change=${(t) => this._changed(t)}
      />
    </label>` : o``;
  }
  static {
    this.styles = [
      P,
      x`
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
O([
  v({ attribute: !1 })
], ve.prototype, "hass");
O([
  p()
], ve.prototype, "_config");
O([
  p()
], ve.prototype, "_t");
function D(i, e) {
  customElements.get(i) || customElements.define(i, e);
}
D("ev-charging-panel-view", _i);
D("ev-charging-session-list", ge);
D("ev-charging-panel", ne);
D("ev-charging-panel-card", Le);
D("ev-charging-recent-card", Y);
D("ev-charging-recent-card-editor", ve);
D("ev-charging-live-card", C);
D("ev-charging-month-card", B);
const ue = window;
ue.customCards = ue.customCards ?? [];
for (const i of [
  "ev-charging-panel-card",
  "ev-charging-recent-card",
  "ev-charging-live-card",
  "ev-charging-month-card"
])
  ue.customCards.some((e) => e.type === i) || ue.customCards.push({ type: i, name: i });
