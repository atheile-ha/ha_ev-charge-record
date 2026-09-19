/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Z = globalThis, pt = Z.ShadowRoot && (Z.ShadyCSS === void 0 || Z.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, _t = Symbol(), At = /* @__PURE__ */ new WeakMap();
let It = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== _t) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (pt && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = At.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && At.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const Qt = (r) => new It(typeof r == "string" ? r : r + "", void 0, _t), A = (r, ...t) => {
  const e = r.length === 1 ? r[0] : t.reduce((s, i, a) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + r[a + 1], r[0]);
  return new It(e, r, _t);
}, te = (r, t) => {
  if (pt) r.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), i = Z.litNonce;
    i !== void 0 && s.setAttribute("nonce", i), s.textContent = e.cssText, r.appendChild(s);
  }
}, St = pt ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return Qt(e);
})(r) : r;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: ee, defineProperty: re, getOwnPropertyDescriptor: se, getOwnPropertyNames: ie, getOwnPropertySymbols: ae, getPrototypeOf: ne } = Object, st = globalThis, Et = st.trustedTypes, oe = Et ? Et.emptyScript : "", le = st.reactiveElementPolyfillSupport, I = (r, t) => r, G = { toAttribute(r, t) {
  switch (t) {
    case Boolean:
      r = r ? oe : null;
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
} }, ft = (r, t) => !ee(r, t), Ct = { attribute: !0, type: String, converter: G, reflect: !1, useDefault: !1, hasChanged: ft };
Symbol.metadata ??= Symbol("metadata"), st.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let R = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = Ct) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), i = this.getPropertyDescriptor(t, s, e);
      i !== void 0 && re(this.prototype, t, i);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: i, set: a } = se(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: i, set(n) {
      const o = i?.call(this);
      a?.call(this, n), this.requestUpdate(t, o, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? Ct;
  }
  static _$Ei() {
    if (this.hasOwnProperty(I("elementProperties"))) return;
    const t = ne(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(I("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(I("properties"))) {
      const e = this.properties, s = [...ie(e), ...ae(e)];
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
      for (const i of s) e.unshift(St(i));
    } else t !== void 0 && e.push(St(t));
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
    return te(t, this.constructor.elementStyles), t;
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
      const a = (s.converter?.toAttribute !== void 0 ? s.converter : G).toAttribute(e, s.type);
      this._$Em = t, a == null ? this.removeAttribute(i) : this.setAttribute(i, a), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, i = s._$Eh.get(t);
    if (i !== void 0 && this._$Em !== i) {
      const a = s.getPropertyOptions(i), n = typeof a.converter == "function" ? { fromAttribute: a.converter } : a.converter?.fromAttribute !== void 0 ? a.converter : G;
      this._$Em = i;
      const o = n.fromAttribute(e, a.type);
      this[i] = o ?? this._$Ej?.get(i) ?? o, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, i = !1, a) {
    if (t !== void 0) {
      const n = this.constructor;
      if (i === !1 && (a = this[t]), s ??= n.getPropertyOptions(t), !((s.hasChanged ?? ft)(a, e) || s.useDefault && s.reflect && a === this._$Ej?.get(t) && !this.hasAttribute(n._$Eu(t, s)))) return;
      this.C(t, e, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: s, reflect: i, wrapped: a }, n) {
    s && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, n ?? e ?? this[t]), a !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || s || (e = void 0), this._$AL.set(t, e)), i === !0 && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
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
        for (const [i, a] of this._$Ep) this[i] = a;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [i, a] of s) {
        const { wrapped: n } = a, o = this[i];
        n !== !0 || this._$AL.has(i) || o === void 0 || this.C(i, void 0, a, o);
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
R.elementStyles = [], R.shadowRootOptions = { mode: "open" }, R[I("elementProperties")] = /* @__PURE__ */ new Map(), R[I("finalized")] = /* @__PURE__ */ new Map(), le?.({ ReactiveElement: R }), (st.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const gt = globalThis, kt = (r) => r, J = gt.trustedTypes, Pt = J ? J.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, Ft = "$lit$", w = `lit$${Math.random().toFixed(9).slice(2)}$`, jt = "?" + w, ce = `<${jt}>`, T = document, F = () => T.createComment(""), j = (r) => r === null || typeof r != "object" && typeof r != "function", mt = Array.isArray, de = (r) => mt(r) || typeof r?.[Symbol.iterator] == "function", lt = `[ 	
\f\r]`, L = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Tt = /-->/g, Mt = />/g, E = RegExp(`>|${lt}(?:([^\\s"'>=/]+)(${lt}*=${lt}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Ut = /'/g, Rt = /"/g, Vt = /^(?:script|style|textarea|title)$/i, he = (r) => (t, ...e) => ({ _$litType$: r, strings: t, values: e }), c = he(1), M = Symbol.for("lit-noChange"), h = Symbol.for("lit-nothing"), Ot = /* @__PURE__ */ new WeakMap(), C = T.createTreeWalker(T, 129);
function Bt(r, t) {
  if (!mt(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Pt !== void 0 ? Pt.createHTML(t) : t;
}
const ue = (r, t) => {
  const e = r.length - 1, s = [];
  let i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = L;
  for (let o = 0; o < e; o++) {
    const l = r[o];
    let d, p, u = -1, b = 0;
    for (; b < l.length && (n.lastIndex = b, p = n.exec(l), p !== null); ) b = n.lastIndex, n === L ? p[1] === "!--" ? n = Tt : p[1] !== void 0 ? n = Mt : p[2] !== void 0 ? (Vt.test(p[2]) && (i = RegExp("</" + p[2], "g")), n = E) : p[3] !== void 0 && (n = E) : n === E ? p[0] === ">" ? (n = i ?? L, u = -1) : p[1] === void 0 ? u = -2 : (u = n.lastIndex - p[2].length, d = p[1], n = p[3] === void 0 ? E : p[3] === '"' ? Rt : Ut) : n === Rt || n === Ut ? n = E : n === Tt || n === Mt ? n = L : (n = E, i = void 0);
    const x = n === E && r[o + 1].startsWith("/>") ? " " : "";
    a += n === L ? l + ce : u >= 0 ? (s.push(d), l.slice(0, u) + Ft + l.slice(u) + w + x) : l + w + (u === -2 ? o : x);
  }
  return [Bt(r, a + (r[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class V {
  constructor({ strings: t, _$litType$: e }, s) {
    let i;
    this.parts = [];
    let a = 0, n = 0;
    const o = t.length - 1, l = this.parts, [d, p] = ue(t, e);
    if (this.el = V.createElement(d, s), C.currentNode = this.el.content, e === 2 || e === 3) {
      const u = this.el.content.firstChild;
      u.replaceWith(...u.childNodes);
    }
    for (; (i = C.nextNode()) !== null && l.length < o; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const u of i.getAttributeNames()) if (u.endsWith(Ft)) {
          const b = p[n++], x = i.getAttribute(u).split(w), K = /([.?@])?(.*)/.exec(b);
          l.push({ type: 1, index: a, name: K[2], strings: x, ctor: K[1] === "." ? _e : K[1] === "?" ? fe : K[1] === "@" ? ge : it }), i.removeAttribute(u);
        } else u.startsWith(w) && (l.push({ type: 6, index: a }), i.removeAttribute(u));
        if (Vt.test(i.tagName)) {
          const u = i.textContent.split(w), b = u.length - 1;
          if (b > 0) {
            i.textContent = J ? J.emptyScript : "";
            for (let x = 0; x < b; x++) i.append(u[x], F()), C.nextNode(), l.push({ type: 2, index: ++a });
            i.append(u[b], F());
          }
        }
      } else if (i.nodeType === 8) if (i.data === jt) l.push({ type: 2, index: a });
      else {
        let u = -1;
        for (; (u = i.data.indexOf(w, u + 1)) !== -1; ) l.push({ type: 7, index: a }), u += w.length - 1;
      }
      a++;
    }
  }
  static createElement(t, e) {
    const s = T.createElement("template");
    return s.innerHTML = t, s;
  }
}
function N(r, t, e = r, s) {
  if (t === M) return t;
  let i = s !== void 0 ? e._$Co?.[s] : e._$Cl;
  const a = j(t) ? void 0 : t._$litDirective$;
  return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(r), i._$AT(r, e, s)), s !== void 0 ? (e._$Co ??= [])[s] = i : e._$Cl = i), i !== void 0 && (t = N(r, i._$AS(r, t.values), i, s)), t;
}
class pe {
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
    const { el: { content: e }, parts: s } = this._$AD, i = (t?.creationScope ?? T).importNode(e, !0);
    C.currentNode = i;
    let a = C.nextNode(), n = 0, o = 0, l = s[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let d;
        l.type === 2 ? d = new W(a, a.nextSibling, this, t) : l.type === 1 ? d = new l.ctor(a, l.name, l.strings, this, t) : l.type === 6 && (d = new me(a, this, t)), this._$AV.push(d), l = s[++o];
      }
      n !== l?.index && (a = C.nextNode(), n++);
    }
    return C.currentNode = T, i;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class W {
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
    t = N(this, t, e), j(t) ? t === h || t == null || t === "" ? (this._$AH !== h && this._$AR(), this._$AH = h) : t !== this._$AH && t !== M && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : de(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== h && j(this._$AH) ? this._$AA.nextSibling.data = t : this.T(T.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: s } = t, i = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = V.createElement(Bt(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === i) this._$AH.p(e);
    else {
      const a = new pe(i, this), n = a.u(this.options);
      a.p(e), this.T(n), this._$AH = a;
    }
  }
  _$AC(t) {
    let e = Ot.get(t.strings);
    return e === void 0 && Ot.set(t.strings, e = new V(t)), e;
  }
  k(t) {
    mt(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, i = 0;
    for (const a of t) i === e.length ? e.push(s = new W(this.O(F()), this.O(F()), this, this.options)) : s = e[i], s._$AI(a), i++;
    i < e.length && (this._$AR(s && s._$AB.nextSibling, i), e.length = i);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const s = kt(t).nextSibling;
      kt(t).remove(), t = s;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class it {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, s, i, a) {
    this.type = 1, this._$AH = h, this._$AN = void 0, this.element = t, this.name = e, this._$AM = i, this.options = a, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = h;
  }
  _$AI(t, e = this, s, i) {
    const a = this.strings;
    let n = !1;
    if (a === void 0) t = N(this, t, e, 0), n = !j(t) || t !== this._$AH && t !== M, n && (this._$AH = t);
    else {
      const o = t;
      let l, d;
      for (t = a[0], l = 0; l < a.length - 1; l++) d = N(this, o[s + l], e, l), d === M && (d = this._$AH[l]), n ||= !j(d) || d !== this._$AH[l], d === h ? t = h : t !== h && (t += (d ?? "") + a[l + 1]), this._$AH[l] = d;
    }
    n && !i && this.j(t);
  }
  j(t) {
    t === h ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class _e extends it {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === h ? void 0 : t;
  }
}
class fe extends it {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== h);
  }
}
class ge extends it {
  constructor(t, e, s, i, a) {
    super(t, e, s, i, a), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = N(this, t, e, 0) ?? h) === M) return;
    const s = this._$AH, i = t === h && s !== h || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, a = t !== h && (s === h || i);
    i && this.element.removeEventListener(this.name, this, s), a && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class me {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    N(this, t);
  }
}
const ve = gt.litHtmlPolyfillSupport;
ve?.(V, W), (gt.litHtmlVersions ??= []).push("3.3.3");
const $e = (r, t, e) => {
  const s = e?.renderBefore ?? t;
  let i = s._$litPart$;
  if (i === void 0) {
    const a = e?.renderBefore ?? null;
    s._$litPart$ = i = new W(t.insertBefore(F(), a), a, void 0, e ?? {});
  }
  return i._$AI(r), i;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const vt = globalThis;
let $ = class extends R {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t.firstChild, t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = $e(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return M;
  }
};
$._$litElement$ = !0, $.finalized = !0, vt.litElementHydrateSupport?.({ LitElement: $ });
const ye = vt.litElementPolyfillSupport;
ye?.({ LitElement: $ });
(vt.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const be = { attribute: !0, type: String, converter: G, reflect: !1, hasChanged: ft }, xe = (r = be, t, e) => {
  const { kind: s, metadata: i } = e;
  let a = globalThis.litPropertyMetadata.get(i);
  if (a === void 0 && globalThis.litPropertyMetadata.set(i, a = /* @__PURE__ */ new Map()), s === "setter" && ((r = Object.create(r)).wrapped = !0), a.set(e.name, r), s === "accessor") {
    const { name: n } = e;
    return { set(o) {
      const l = t.get.call(this);
      t.set.call(this, o), this.requestUpdate(n, l, r, !0, o);
    }, init(o) {
      return o !== void 0 && this.C(n, void 0, r, o), o;
    } };
  }
  if (s === "setter") {
    const { name: n } = e;
    return function(o) {
      const l = this[n];
      t.call(this, o), this.requestUpdate(n, l, r, !0, o);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function f(r) {
  return (t, e) => typeof e == "object" ? xe(r, t, e) : ((s, i, a) => {
    const n = i.hasOwnProperty(a);
    return i.constructor.createProperty(a, s), n ? Object.getOwnPropertyDescriptor(i, a) : void 0;
  })(r, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function g(r) {
  return f({ ...r, state: !0, attribute: !1 });
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const we = { ATTRIBUTE: 1 }, Ae = (r) => (...t) => ({ _$litDirective$: r, values: t });
class Se {
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
const Y = Ae(class extends Se {
  constructor(r) {
    if (super(r), r.type !== we.ATTRIBUTE || r.name !== "class" || r.strings?.length > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
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
    return M;
  }
});
async function ut(r, t) {
  return (await r.callWS({
    type: "ev_charging/sessions/list",
    ...t
  })).sessions;
}
function Ee(r, t) {
  return r.callWS({ type: "ev_charging/sessions/stats", year: t });
}
async function Ce(r) {
  return (await r.callWS({
    type: "ev_charging/vehicles/list"
  })).vehicles;
}
const m = "–";
function U(r, t, e) {
  return new Intl.NumberFormat(t, {
    minimumFractionDigits: e,
    maximumFractionDigits: e
  }).format(r);
}
function k(r, t, e = !1) {
  return r === null ? m : `${e ? "~" : ""}${U(r, t, 3)} kWh`;
}
function Nt(r, t, e = !1) {
  return r === null ? m : `${e ? "~" : ""}${U(r, t, 0)} kWh`;
}
function Ht(r, t, e) {
  if (r === null)
    return m;
  try {
    return new Intl.NumberFormat(t, {
      style: "currency",
      currency: e,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(r);
  } catch {
    return `${U(r, t, 0)} ${e}`;
  }
}
function zt(r) {
  if (r === null)
    return m;
  const t = Math.round(r);
  return t < 60 ? `${t} min` : `${Math.round(t / 60)} h`;
}
function X(r, t, e) {
  if (r === null)
    return m;
  try {
    return new Intl.NumberFormat(t, { style: "currency", currency: e }).format(r);
  } catch {
    return `${U(r, t, 2)} ${e}`;
  }
}
function P(r) {
  if (r === null)
    return m;
  const t = Math.round(r);
  if (t < 60)
    return `${t} min`;
  const e = Math.floor(t / 60), s = String(t % 60).padStart(2, "0");
  return `${e}:${s} h`;
}
function Q(r, t) {
  return r === null ? m : `${U(r, t, 0)} %`;
}
function ke(r, t) {
  return r === null ? m : `${U(r, t, 0)} km`;
}
function Pe(r, t) {
  return r === null ? m : `${U(r, t, 1)} kW`;
}
function tt(r, t, e) {
  return r === null ? m : new Intl.DateTimeFormat(t, {
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(r));
}
function Dt(r, t, e) {
  return r === null ? m : new Intl.DateTimeFormat(t, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(r));
}
function ct(r, t, e) {
  return new Intl.DateTimeFormat(t, { month: e, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, r - 1, 1))
  );
}
function Wt(r, t) {
  return r.vehicle_id === null ? t("unassigned") : r.vehicle_name ?? r.vehicle_id;
}
const Te = [
  "soc_start",
  "soc_end",
  "odometer_km",
  "energy_kwh",
  "energy_grid_kwh",
  "energy_solar_kwh",
  "cost",
  "address"
];
function Me(r) {
  return Te.includes(r);
}
function Ue(r, t) {
  return Me(r) ? t(`field_${r}`) : r;
}
const qt = "__unassigned__", $t = "__none__", et = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: ""
};
function Kt(r, t) {
  const e = new Intl.DateTimeFormat("en-US", {
    timeZone: t,
    year: "numeric",
    month: "numeric"
  }).formatToParts(r), s = (i) => Number(e.find((a) => a.type === i)?.value ?? 0);
  return { year: s("year"), month: s("month") };
}
function Re(r, t) {
  return { view: "overview", ...Kt(r, t), filters: { ...et } };
}
function Oe(r, t, e) {
  const s = r * 12 + (t - 1) + e;
  return { year: Math.floor(s / 12), month: s % 12 + 1 };
}
const Zt = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"]
];
function Ne(r) {
  const t = new URLSearchParams({ year: String(r.year), month: String(r.month) });
  for (const [e, s] of Zt)
    r.filters[e] !== "" && t.set(s, r.filters[e]);
  return `/${r.view}?${t.toString()}`;
}
function He(r, t) {
  const e = {}, s = r.split("/").filter((d) => d !== "")[0];
  (s === "overview" || s === "detail" || s === "recent") && (e.view = s);
  const i = new URLSearchParams(t), a = Number(i.get("year")), n = Number(i.get("month"));
  Number.isInteger(a) && a >= 1e3 && a <= 9999 && Number.isInteger(n) && n >= 1 && n <= 12 && (e.year = a, e.month = n);
  const o = { ...et };
  let l = !1;
  for (const [d, p] of Zt) {
    const u = i.get(p);
    u && (o[d] = u, l = !0);
  }
  return l && (e.filters = o), e;
}
function dt(r) {
  const t = r.reduce((e, s) => e + (s ?? 0), 0);
  return Math.round(t * 1e4) / 1e4;
}
function ze(r) {
  return {
    count: r.length,
    energy_kwh: dt(r.map((t) => t.energy_kwh)),
    energy_is_estimate: r.some((t) => t.energy_is_estimate),
    cost: dt(r.map((t) => t.cost)),
    charge_duration_min: dt(r.map((t) => t.charge_duration_min)),
    open_followups: r.filter(
      (t) => t.status === "followup_open" || t.open_fields.length > 0
    ).length
  };
}
function De(r) {
  let t = null;
  return r.latitude !== null && r.longitude !== null ? t = `${r.latitude},${r.longitude}` : r.address && (t = r.address), t === null ? null : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(t)}`;
}
function Le(r) {
  return Object.values(r).some((t) => t !== "");
}
function Ie(r, t) {
  return r.filter((e) => {
    if (t.vehicle === qt) {
      if (e.vehicle_id !== null) return !1;
    } else if (t.vehicle !== "" && e.vehicle_id !== t.vehicle)
      return !1;
    if (t.location !== "" && e.location !== t.location || t.chargeType !== "" && e.charge_type !== t.chargeType || t.status !== "" && e.status !== t.status) return !1;
    if (t.card === $t) {
      if (e.card_uid !== null) return !1;
    } else if (t.card !== "" && e.card_uid !== t.card)
      return !1;
    return !0;
  });
}
function Fe(r, t) {
  const e = /* @__PURE__ */ new Map();
  for (const s of r)
    e.set(s.id, s.name);
  for (const s of t)
    s.vehicle_id !== null && !e.has(s.vehicle_id) && e.set(s.vehicle_id, s.vehicle_name ?? s.vehicle_id);
  return [...e].map(([s, i]) => ({ value: s, label: i }));
}
function je(r, t, e) {
  const s = new Set(
    t.map((a) => a.card_uid).filter((a) => a !== null)
  ), i = /* @__PURE__ */ new Map();
  for (const a of r) {
    const n = [...s].find((o) => o !== "" && a.uid.endsWith(o));
    i.set(n ?? a.uid, a.label || a.uid);
  }
  for (const a of t)
    a.card_uid !== null && !i.has(a.card_uid) && i.set(a.card_uid, a.card_label || a.card_uid);
  return e !== "" && e !== $t && !i.has(e) && i.set(e, e), [...i].map(([a, n]) => ({ value: a, label: n }));
}
function Ve(r, t, e) {
  return [.../* @__PURE__ */ new Set([...r, t, e])].sort((s, i) => i - s);
}
const Be = "M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z";
function _(r, t) {
  return t === null || t === "" || t === m ? h : c`<dt class="muted">${r}</dt>
    <dd>${t}</dd>`;
}
function We(r, t) {
  const e = De(r);
  return r.address === null && e === null ? null : c`${r.address ?? h}${e === null ? h : c`<a
        class="map"
        href=${e}
        target="_blank"
        rel="noopener noreferrer"
        title=${t("detail_map_link")}
        aria-label=${t("detail_map_link")}
        ><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d=${Be} fill="currentColor"></path></svg
        >${r.address === null ? t("detail_map_link") : h}</a
      >`}`;
}
function qe(r, t, e) {
  if (!r.phases_recorded || r.phases.length === 0)
    return c`<p class="muted">${t("detail_phases_not_recorded")}</p>`;
  const s = e.locale.language, i = e.config.time_zone;
  return c`<table class="phases">
    <caption>
      ${t("detail_phases")}
    </caption>
    <thead>
      <tr>
        <th>${t("phase_start")}</th>
        <th>${t("phase_end")}</th>
        <th class="num">${t("phase_duration")}</th>
        <th class="num">${t("total_energy")}</th>
        <th class="num">${t("total_cost")}</th>
      </tr>
    </thead>
    <tbody>
      ${r.phases.map(
    (a) => c`<tr>
          <td>${Dt(a.start, s, i)}</td>
          <td>${Dt(a.end, s, i)}</td>
          <td class="num">${P(a.duration_min)}</td>
          <td class="num">${k(a.energy_kwh, s)}</td>
          <td class="num">${X(a.cost, s, e.config.currency)}</td>
        </tr>`
  )}
    </tbody>
  </table>`;
}
function Yt(r, t, e) {
  const s = e.locale.language, i = e.config.time_zone, a = t("detail_not_recorded"), n = r.soc_start === null && r.soc_end === null ? null : `${Q(r.soc_start, s)} → ${Q(r.soc_end, s)}`;
  return c`<div class="body">
    <dl>
      ${_(t("detail_plug_start"), tt(r.plug_start, s, i))}
      ${_(t("detail_plug_end"), tt(r.plug_end, s, i))}
      ${_(t("detail_plug_duration"), P(r.plug_duration_min))}
      ${_(t("detail_charge_duration"), P(r.charge_duration_min))}
      ${r.pause_duration_min ? _(t("detail_pause_duration"), P(r.pause_duration_min)) : h}
      ${_(t("detail_soc"), n)}
      ${_(t("detail_odometer"), ke(r.odometer_km, s))}
      ${_(t("detail_power_avg"), Pe(r.power_avg_kw, s))}
      ${r.location === "home" ? c`${_(
    t("detail_energy_grid"),
    r.energy_grid_kwh === null ? a : k(r.energy_grid_kwh, s)
  )}
          ${_(
    t("detail_energy_solar"),
    r.energy_solar_kwh === null ? a : k(r.energy_solar_kwh, s)
  )}` : h}
      ${r.energy_unallocated_kwh > 0 ? _(t("detail_energy_unallocated"), k(r.energy_unallocated_kwh, s)) : h}
      ${_(t("detail_card"), r.card_label ?? r.card_uid)}
      ${_(t("detail_identification"), t(`identification_${r.identification_source}`))}
      ${_(t("detail_address"), We(r, t))}
      ${_(t("detail_provider"), r.provider)}
      ${_(t("detail_note"), r.note)}
      ${r.open_fields.length > 0 ? _(
    t("detail_open_fields"),
    r.open_fields.map((o) => Ue(o, t)).join(", ")
  ) : h}
    </dl>
    ${qe(r, t, e)}
  </div>`;
}
const Gt = A`
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
`, H = A`
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
var Ke = Object.defineProperty, yt = (r, t, e, s) => {
  for (var i = void 0, a = r.length - 1, n; a >= 0; a--)
    (n = r[a]) && (i = n(t, e, i) || i);
  return i && Ke(t, e, i), i;
};
class at extends $ {
  constructor() {
    super(...arguments), this.sessions = [];
  }
  render() {
    const t = this.t;
    return !t || !this.hass ? h : c`<ul>
      ${this.sessions.map((e) => this._renderSession(e, t))}
    </ul>`;
  }
  _renderSession(t, e) {
    const s = this.hass, i = s.locale.language, a = t.soc_start !== null && t.soc_end !== null ? `${Q(t.soc_start, i)} → ${Q(t.soc_end, i)}` : h;
    return c`<li>
      <details>
        <summary>
          <div class="line">
            <span class=${Y({ vehicle: !0, unassigned: t.vehicle_id === null })}
              >${Wt(t, e)}</span
            >
            <span class="muted"
              >${tt(t.plug_start, i, s.config.time_zone)}</span
            >
          </div>
          <div class="line">
            <span>
              ${k(t.energy_kwh, i, t.energy_is_estimate)} ·
              ${X(t.cost, i, s.config.currency)} ·
              ${P(t.charge_duration_min)}
            </span>
            <span class="muted">${a}</span>
          </div>
          <div class="line">
            <span class="chips">
              <span class="chip">${e(`location_${t.location}`)}</span>
              ${t.status === "complete" ? h : c`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
            </span>
          </div>
        </summary>
        ${Yt(t, e, s)}
      </details>
    </li>`;
  }
  static {
    this.styles = [
      H,
      Gt,
      A`
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
yt([
  f({ attribute: !1 })
], at.prototype, "hass");
yt([
  f({ attribute: !1 })
], at.prototype, "t");
yt([
  f({ attribute: !1 })
], at.prototype, "sessions");
const Ze = "component.ev_charging.selector.panel.options.";
function B(r) {
  return (t, e) => {
    const s = r[Ze + t];
    return s === void 0 ? t : e ? s.replace(
      /\{(\w+)\}/g,
      (i, a) => a in e ? String(e[a]) : i
    ) : s;
  };
}
const ht = /* @__PURE__ */ new Map();
function bt(r) {
  const t = r.language;
  let e = ht.get(t);
  return e === void 0 && (e = r.callWS({
    type: "frontend/get_translations",
    language: t,
    category: "selector",
    integration: ["ev_charging"]
  }).then((s) => B(s.resources)), e.catch(() => ht.delete(t)), ht.set(t, e)), e;
}
var Ye = Object.defineProperty, y = (r, t, e, s) => {
  for (var i = void 0, a = r.length - 1, n; a >= 0; a--)
    (n = r[a]) && (i = n(t, e, i) || i);
  return i && Ye(t, e, i), i;
};
const Ge = 600 * 1e3, Je = 5, Xe = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z", Qe = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z", tr = [
  { id: "overview", label: "view_overview" },
  { id: "recent", label: "view_recent" },
  { id: "detail", label: "view_detail" }
], er = ["home", "home_no_wallbox", "external"], rr = ["ac", "dc", "unknown"], sr = ["complete", "followup_open", "flagged"], ir = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" }
];
function Lt(r) {
  return c`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${r} fill="currentColor"></path>
  </svg>`;
}
class v extends $ {
  constructor() {
    super(...arguments), this._vehicles = [], this._failed = !1, this._metric = "energy", this._started = !1, this._recentRequested = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => this._refresh(), Ge);
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
        ...Re(/* @__PURE__ */ new Date(), this.hass.config.time_zone),
        ...e,
        filters: { ...et, ...e?.filters }
      };
    }
    this._sync();
  }
  _sync() {
    const t = this.hass, e = this._state;
    if (!(!t || !e)) {
      if (this._started || (this._started = !0, this._loadShared(t, !1)), e.view !== "recent" && this._statsKey !== e.year && (this._statsKey = e.year, this._stats = void 0, this._loadStats(t, e.year, !1)), e.view === "detail") {
        const s = `${e.year}-${e.month}`;
        this._sessionsKey !== s && (this._sessionsKey = s, this._sessions = void 0, this._loadSessions(t, e.year, e.month, !1));
      }
      e.view === "recent" && !this._recentRequested && (this._recentRequested = !0, this._loadRecent(t, !1));
    }
  }
  _refresh() {
    const t = this.hass, e = this._state;
    !t || !e || !this._started || this._failed || (this._loadShared(t, !0), e.view !== "recent" && this._loadStats(t, e.year, !0), e.view === "detail" && this._loadSessions(t, e.year, e.month, !0), e.view === "recent" && this._loadRecent(t, !0));
  }
  _fail(t, e) {
    console.error("ev_charging: loading data failed", t), e || (this._failed = !0);
  }
  _retry() {
    this._failed = !1, this._started = !1, this._statsKey = void 0, this._sessionsKey = void 0, this._recentRequested = !1, this.requestUpdate();
  }
  async _loadShared(t, e) {
    try {
      this._t = await bt(t);
    } catch (s) {
      this._t = B({}), this._fail(s, e);
      return;
    }
    try {
      this._vehicles = await Ce(t);
    } catch (s) {
      this._fail(s, e);
    }
  }
  async _loadStats(t, e, s) {
    try {
      const i = await Ee(t, e);
      this._statsKey === e && (this._stats = i);
    } catch (i) {
      this._statsKey === e && this._fail(i, s);
    }
  }
  async _loadSessions(t, e, s, i) {
    const a = `${e}-${s}`;
    try {
      const n = await ut(t, { year: e, month: s });
      this._sessionsKey === a && (this._sessions = n);
    } catch (n) {
      this._sessionsKey === a && this._fail(n, i);
    }
  }
  async _loadRecent(t, e) {
    try {
      this._recent = await ut(t, { limit: Je });
    } catch (s) {
      this._fail(s, e);
    }
  }
  _setState(t) {
    this._state && (this._state = { ...this._state, ...t }, this.dispatchEvent(new CustomEvent("ev-state-changed", { detail: this._state })));
  }
  _setFilter(t, e) {
    this._state && this._setState({ filters: { ...this._state.filters, [t]: e } });
  }
  _shift(t) {
    this._state && this._setState(Oe(this._state.year, this._state.month, t));
  }
  render() {
    const t = this._state;
    if (!t || !this.hass)
      return h;
    if (this._failed)
      return this._renderError(this._t ?? B({}));
    const e = this._t;
    return e ? c`
      <div class="view">
        ${this._renderTabs(e, t)}
        ${t.view === "recent" ? h : this._renderPeriod(e, t)}
        ${t.view === "overview" ? this._renderOverview(e, t) : t.view === "detail" ? this._renderDetail(e, t) : this._renderRecent(e)}
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
      ${tr.map(
      (s) => c`<button
          class=${Y({ tab: !0, active: s.id === e.view })}
          aria-current=${s.id === e.view ? "page" : "false"}
          @click=${() => this._setState({ view: s.id })}
        >
          ${t(s.label)}
        </button>`
    )}
    </nav>`;
  }
  _renderPeriod(t, e) {
    const s = this.hass, i = s.locale.language, a = Kt(/* @__PURE__ */ new Date(), s.config.time_zone), n = Ve(this._stats?.years ?? [], a.year, e.year);
    return c`<div class="period">
      <button class="icon" aria-label=${t("period_previous")} @click=${() => this._shift(-1)}>
        ${Lt(Xe)}
      </button>
      <select
        aria-label=${t("period_month")}
        @change=${(o) => this._setState({ month: Number(o.target.value) })}
      >
        ${Array.from({ length: 12 }, (o, l) => l + 1).map(
      (o) => c`<option value=${o} .selected=${o === e.month}>
              ${ct(o, i, "long")}
            </option>`
    )}
      </select>
      <select
        aria-label=${t("period_year")}
        @change=${(o) => this._setState({ year: Number(o.target.value) })}
      >
        ${n.map(
      (o) => c`<option value=${o} .selected=${o === e.year}>${o}</option>`
    )}
      </select>
      <button class="icon" aria-label=${t("period_next")} @click=${() => this._shift(1)}>
        ${Lt(Qe)}
      </button>
    </div>`;
  }
  _renderTiles(t, e) {
    const s = this.hass, i = s.locale.language, a = [
      ["total_energy", k(e.energy_kwh, i, e.energy_is_estimate)],
      ["total_cost", X(e.cost, i, s.config.currency)],
      ["total_duration", P(e.charge_duration_min)],
      ["total_sessions", String(e.count)],
      ["open_followups", String(e.open_followups)]
    ];
    return c`<div class="tiles">
      ${a.map(
      ([n, o]) => c`<div class="tile">
          <span class="tile-label muted">${t(n)}</span>
          <span class="tile-value">${o}</span>
        </div>`
    )}
    </div>`;
  }
  _renderOverview(t, e) {
    const s = this._stats;
    return s ? c`
      ${this._renderTiles(t, s.months[e.month - 1])}
      ${this._renderChart(t, e, s)} ${this._renderYearSummary(t, e, s)}
    ` : c`<div class="spinner" role="progressbar"></div>`;
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
        return Ht(t.cost, s, e.config.currency);
      case "duration":
        return zt(t.charge_duration_min);
      default:
        return Nt(t.energy_kwh, s, t.energy_is_estimate);
    }
  }
  _renderChart(t, e, s) {
    const i = this.hass.locale.language, a = Math.max(...s.months.map((n) => this._metricValue(n)), 0);
    return c`<section class="chart">
      <div class="chart-head">
        <h3>${t("chart_title", { year: e.year })}</h3>
        <label class="metric">
          <span class="muted">${t("chart_metric")}</span>
          <select
            @change=${(n) => {
      this._metric = n.target.value;
    }}
          >
            ${ir.map(
      (n) => c`<option value=${n.id} .selected=${n.id === this._metric}>
                  ${t(n.label)}
                </option>`
    )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${s.months.map((n) => {
      const o = a > 0 ? this._metricValue(n) / a * 100 : 0, l = ct(n.month, i, "long"), d = n.count === 0 ? m : this._formatMetric(n);
      return c`<button
            class=${Y({ bar: !0, selected: n.month === e.month })}
            title=${`${l}: ${d}`}
            aria-label=${`${l}: ${d}`}
            aria-pressed=${n.month === e.month ? "true" : "false"}
            @click=${() => this._setState({ month: n.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${o}%`}></span></span>
            <span class="bar-label muted">${ct(n.month, i, "short")}</span>
            <span class="bar-value">${d}</span>
          </button>`;
    })}
      </div>
    </section>`;
  }
  _renderYearSummary(t, e, s) {
    const i = this.hass, a = i.locale.language, n = s.year_summary, o = [
      ["scope_total", n.all],
      ["scope_internal", n.internal],
      ["scope_external", n.external]
    ], l = [
      ["total_energy", (d) => Nt(d.energy_kwh, a, d.energy_is_estimate)],
      ["total_cost", (d) => Ht(d.cost, a, i.config.currency)],
      ["total_duration", (d) => zt(d.charge_duration_min)],
      ["total_sessions", (d) => String(d.count)]
    ];
    return c`<section class="year-summary">
      <h3>${t("year_summary_title", { year: e.year })}</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            ${o.map(([d]) => c`<th class="num">${t(d)}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${l.map(
      ([d, p]) => c`<tr>
              <th>${t(d)}</th>
              ${o.map(([, u]) => c`<td class="num">${p(u)}</td>`)}
            </tr>`
    )}
        </tbody>
      </table>
    </section>`;
  }
  _renderDetail(t, e) {
    const s = this._sessions;
    if (!s)
      return c`<div class="spinner" role="progressbar"></div>`;
    const i = e.filters, a = Ie(s, i), n = [
      ...Fe(this._vehicles, s),
      { value: qt, label: t("unassigned") }
    ], o = [
      { value: $t, label: t("filter_no_card") },
      ...je(
        this._vehicles.flatMap((l) => l.cards),
        s,
        i.card
      )
    ];
    return c`
      <div class="filters">
        ${this._renderFilter(t("filter_vehicle"), "vehicle", n, t)}
        ${this._renderFilter(
      t("filter_location"),
      "location",
      er.map((l) => ({ value: l, label: t(`location_${l}`) })),
      t
    )}
        ${this._renderFilter(
      t("filter_charge_type"),
      "chargeType",
      rr.map((l) => ({ value: l, label: t(`charge_type_${l}`) })),
      t
    )}
        ${this._renderFilter(t("filter_card"), "card", o, t)}
        ${this._renderFilter(
      t("filter_status"),
      "status",
      sr.map((l) => ({ value: l, label: t(`status_${l}`) })),
      t
    )}
        ${Le(i) ? c`<button
              class="text reset"
              @click=${() => this._setState({ filters: { ...et } })}
            >
              ${t("filter_reset")}
            </button>` : h}
      </div>
      ${this._renderTiles(t, ze(a))}
      <p class="count muted">
        ${t("filter_count", { shown: a.length, total: s.length })}
      </p>
      ${a.length === 0 ? c`<div class="message">
            ${s.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>` : this._renderTable(a, t)}
    `;
  }
  _renderRecent(t) {
    const e = this._recent;
    return e ? e.length === 0 ? c`<div class="message">${t("no_sessions")}</div>` : c`<ev-charging-session-list
          .hass=${this.hass}
          .t=${t}
          .sessions=${e}
        ></ev-charging-session-list>` : c`<div class="spinner" role="progressbar"></div>`;
  }
  _renderFilter(t, e, s, i) {
    const a = this._state.filters[e];
    return c`<label class="filter">
      <span class="muted">${t}</span>
      <select
        @change=${(n) => this._setFilter(e, n.target.value)}
      >
        <option value="" .selected=${a === ""}>${i("filter_all")}</option>
        ${s.map(
      (n) => c`<option value=${n.value} .selected=${n.value === a}>
              ${n.label}
            </option>`
    )}
      </select>
    </label>`;
  }
  _renderTable(t, e) {
    return c`<div class="table" role="table">
      <div class="head" role="row">
        <span>${e("col_date")}</span>
        <span>${e("filter_vehicle")}</span>
        <span>${e("filter_location")}</span>
        <span>${e("filter_charge_type")}</span>
        <span class="num">${e("total_energy")}</span>
        <span class="num">${e("total_cost")}</span>
        <span class="num">${e("total_duration")}</span>
        <span>${e("filter_status")}</span>
      </div>
      ${t.map((s) => this._renderSession(s, e))}
    </div>`;
  }
  _renderSession(t, e) {
    const s = this.hass, i = s.locale.language, a = s.config.time_zone, n = t.vehicle_id === null;
    return c`<details class="session">
      <summary>
        <span class="c-date">${tt(t.plug_start, i, a)}</span>
        <span class=${Y({ "c-vehicle": !0, vehicle: !0, unassigned: n })}
          >${Wt(t, e)}</span
        >
        <span class="c-location"><span class="chip">${e(`location_${t.location}`)}</span></span>
        <span class="c-type"><span class="chip">${e(`charge_type_${t.charge_type}`)}</span></span>
        <span class="c-energy num"
          >${k(t.energy_kwh, i, t.energy_is_estimate)}</span
        >
        <span class="c-cost num">${X(t.cost, i, s.config.currency)}</span>
        <span class="c-duration num">${P(t.charge_duration_min)}</span>
        <span class="c-status">
          ${t.status === "complete" ? h : c`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
          ${t.location_conflict ? c`<span class="chip alert">${e("flag_location_conflict")}</span>` : h}
          ${t.identification_conflict ? c`<span class="chip alert">${e("flag_identification_conflict")}</span>` : h}
          ${t.charge_error ? c`<span class="chip alert">${e("flag_charge_error")}</span>` : h}
          ${t.energy_unallocated_kwh > 0 ? c`<span class="chip warn">${e("flag_unallocated_energy")}</span>` : h}
        </span>
      </summary>
      ${Yt(t, e, s)}
    </details>`;
  }
  static {
    this.styles = [
      H,
      Gt,
      A`
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
y([
  f({ attribute: !1 })
], v.prototype, "hass");
y([
  f({ attribute: !1 })
], v.prototype, "initialState");
y([
  g()
], v.prototype, "_state");
y([
  g()
], v.prototype, "_t");
y([
  g()
], v.prototype, "_stats");
y([
  g()
], v.prototype, "_sessions");
y([
  g()
], v.prototype, "_recent");
y([
  g()
], v.prototype, "_vehicles");
y([
  g()
], v.prototype, "_failed");
y([
  g()
], v.prototype, "_metric");
var ar = Object.defineProperty, nt = (r, t, e, s) => {
  for (var i = void 0, a = r.length - 1, n; a >= 0; a--)
    (n = r[a]) && (i = n(t, e, i) || i);
  return i && ar(t, e, i), i;
};
const nr = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
class q extends $ {
  constructor() {
    super(...arguments), this.narrow = !1;
  }
  willUpdate() {
    this._initialState === void 0 && (this._initialState = He(this.route?.path ?? "", window.location.search));
  }
  _toggleMenu() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: !0, composed: !0 }));
  }
  _onStateChanged(t) {
    const e = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${e}${Ne(t.detail)}`);
  }
  render() {
    return c`
      <header>
        ${this.narrow ? c`<button class="menu" @click=${() => this._toggleMenu()}>
              <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d=${nr} fill="currentColor"></path>
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
      H,
      A`
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
nt([
  f({ attribute: !1 })
], q.prototype, "hass");
nt([
  f({ type: Boolean })
], q.prototype, "narrow");
nt([
  f({ attribute: !1 })
], q.prototype, "route");
nt([
  f({ attribute: !1 })
], q.prototype, "panel");
var or = Object.defineProperty, Jt = (r, t, e, s) => {
  for (var i = void 0, a = r.length - 1, n; a >= 0; a--)
    (n = r[a]) && (i = n(t, e, i) || i);
  return i && or(t, e, i), i;
};
class xt extends $ {
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
      H,
      A`
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
Jt([
  f({ attribute: !1 })
], xt.prototype, "hass");
Jt([
  f({ type: Boolean, reflect: !0, attribute: "is-panel" })
], xt.prototype, "isPanel");
var lr = Object.defineProperty, S = (r, t, e, s) => {
  for (var i = void 0, a = r.length - 1, n; a >= 0; a--)
    (n = r[a]) && (i = n(t, e, i) || i);
  return i && lr(t, e, i), i;
};
const O = 3, wt = 20, cr = 600 * 1e3;
function Xt(r) {
  return Number.isInteger(r) && r >= 1 && r <= wt;
}
class z extends $ {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1;
  }
  setConfig(t) {
    if (!Xt(t.count ?? O))
      throw new Error(`count must be a whole number from 1 to ${wt}`);
    this._config = t, this._started && this.hass && this._load(this.hass, !0);
  }
  getCardSize() {
    return 1 + (this._config.count ?? O) * 2;
  }
  static getStubConfig() {
    return { count: O };
  }
  static getConfigElement() {
    return document.createElement("ev-charging-recent-card-editor");
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => {
      this.hass && this._started && !this._failed && this._load(this.hass, !0);
    }, cr);
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
      this._t = await bt(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = B({}), this._failed = !0;
      return;
    }
    await this._load(t, !1);
  }
  async _load(t, e) {
    try {
      this._sessions = await ut(t, { limit: this._config.count ?? O }), this._failed = !1;
    } catch (s) {
      console.error("ev_charging: loading sessions failed", s), e || (this._failed = !0);
    }
  }
  _retry() {
    this.hass && (this._failed = !1, this._started = !1, this.requestUpdate());
  }
  render() {
    const t = this._t;
    return !t || !this.hass ? c`<div class="spinner" role="progressbar"></div>` : this._failed ? c`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>` : c`
      <h2>${this._config.title ?? t("recent_title")}</h2>
      ${this._sessions === void 0 ? c`<div class="spinner" role="progressbar"></div>` : this._sessions.length === 0 ? c`<div class="message">${t("no_sessions")}</div>` : c`<ev-charging-session-list
              .hass=${this.hass}
              .t=${t}
              .sessions=${this._sessions}
            ></ev-charging-session-list>`}
    `;
  }
  static {
    this.styles = [
      H,
      A`
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
S([
  f({ attribute: !1 })
], z.prototype, "hass");
S([
  g()
], z.prototype, "_config");
S([
  g()
], z.prototype, "_t");
S([
  g()
], z.prototype, "_sessions");
S([
  g()
], z.prototype, "_failed");
class ot extends $ {
  constructor() {
    super(...arguments), this._config = {}, this._started = !1;
  }
  setConfig(t) {
    this._config = t;
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, bt(this.hass).then(
      (e) => this._t = e,
      () => this._t = B({})
    ));
  }
  _changed(t) {
    const e = Number(t.target.value);
    if (!Xt(e)) {
      t.target.value = String(this._config.count ?? O);
      return;
    }
    this._config = { ...this._config, count: e }, this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: !0,
        composed: !0
      })
    );
  }
  render() {
    const t = this._t;
    return t ? c`<label>
      <span>${t("card_count")}</span>
      <input
        type="number"
        min="1"
        max=${wt}
        step="1"
        .value=${String(this._config.count ?? O)}
        @change=${(e) => this._changed(e)}
      />
    </label>` : c``;
  }
  static {
    this.styles = [
      H,
      A`
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
S([
  f({ attribute: !1 })
], ot.prototype, "hass");
S([
  g()
], ot.prototype, "_config");
S([
  g()
], ot.prototype, "_t");
function D(r, t) {
  customElements.get(r) || customElements.define(r, t);
}
D("ev-charging-panel-view", v);
D("ev-charging-session-list", at);
D("ev-charging-panel", q);
D("ev-charging-panel-card", xt);
D("ev-charging-recent-card", z);
D("ev-charging-recent-card-editor", ot);
const rt = window;
rt.customCards = rt.customCards ?? [];
for (const r of ["ev-charging-panel-card", "ev-charging-recent-card"])
  rt.customCards.some((t) => t.type === r) || rt.customCards.push({ type: r, name: r });
