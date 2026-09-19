/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const W = globalThis, ct = W.ShadowRoot && (W.ShadyCSS === void 0 || W.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, dt = Symbol(), mt = /* @__PURE__ */ new WeakMap();
let Ut = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== dt) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (ct && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = mt.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && mt.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const Ft = (i) => new Ut(typeof i == "string" ? i : i + "", void 0, dt), L = (i, ...t) => {
  const e = i.length === 1 ? i[0] : t.reduce((s, r, a) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[a + 1], i[0]);
  return new Ut(e, i, dt);
}, Vt = (i, t) => {
  if (ct) i.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), r = W.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = e.cssText, i.appendChild(s);
  }
}, vt = ct ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return Ft(e);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Bt, defineProperty: Wt, getOwnPropertyDescriptor: qt, getOwnPropertyNames: Kt, getOwnPropertySymbols: Zt, getPrototypeOf: Yt } = Object, tt = globalThis, $t = tt.trustedTypes, Gt = $t ? $t.emptyScript : "", Jt = tt.reactiveElementPolyfillSupport, R = (i, t) => i, Z = { toAttribute(i, t) {
  switch (t) {
    case Boolean:
      i = i ? Gt : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, t) {
  let e = i;
  switch (t) {
    case Boolean:
      e = i !== null;
      break;
    case Number:
      e = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(i);
      } catch {
        e = null;
      }
  }
  return e;
} }, ht = (i, t) => !Bt(i, t), yt = { attribute: !0, type: String, converter: Z, reflect: !1, useDefault: !1, hasChanged: ht };
Symbol.metadata ??= Symbol("metadata"), tt.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let T = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = yt) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(t, s, e);
      r !== void 0 && Wt(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: r, set: a } = qt(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: r, set(n) {
      const o = r?.call(this);
      a?.call(this, n), this.requestUpdate(t, o, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? yt;
  }
  static _$Ei() {
    if (this.hasOwnProperty(R("elementProperties"))) return;
    const t = Yt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(R("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(R("properties"))) {
      const e = this.properties, s = [...Kt(e), ...Zt(e)];
      for (const r of s) this.createProperty(r, e[r]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [s, r] of e) this.elementProperties.set(s, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, s] of this.elementProperties) {
      const r = this._$Eu(e, s);
      r !== void 0 && this._$Eh.set(r, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const s = new Set(t.flat(1 / 0).reverse());
      for (const r of s) e.unshift(vt(r));
    } else t !== void 0 && e.push(vt(t));
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
    const s = this.constructor.elementProperties.get(t), r = this.constructor._$Eu(t, s);
    if (r !== void 0 && s.reflect === !0) {
      const a = (s.converter?.toAttribute !== void 0 ? s.converter : Z).toAttribute(e, s.type);
      this._$Em = t, a == null ? this.removeAttribute(r) : this.setAttribute(r, a), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, r = s._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const a = s.getPropertyOptions(r), n = typeof a.converter == "function" ? { fromAttribute: a.converter } : a.converter?.fromAttribute !== void 0 ? a.converter : Z;
      this._$Em = r;
      const o = n.fromAttribute(e, a.type);
      this[r] = o ?? this._$Ej?.get(r) ?? o, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, r = !1, a) {
    if (t !== void 0) {
      const n = this.constructor;
      if (r === !1 && (a = this[t]), s ??= n.getPropertyOptions(t), !((s.hasChanged ?? ht)(a, e) || s.useDefault && s.reflect && a === this._$Ej?.get(t) && !this.hasAttribute(n._$Eu(t, s)))) return;
      this.C(t, e, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: s, reflect: r, wrapped: a }, n) {
    s && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, n ?? e ?? this[t]), a !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || s || (e = void 0), this._$AL.set(t, e)), r === !0 && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
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
        for (const [r, a] of this._$Ep) this[r] = a;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [r, a] of s) {
        const { wrapped: n } = a, o = this[r];
        n !== !0 || this._$AL.has(r) || o === void 0 || this.C(r, void 0, a, o);
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
T.elementStyles = [], T.shadowRootOptions = { mode: "open" }, T[R("elementProperties")] = /* @__PURE__ */ new Map(), T[R("finalized")] = /* @__PURE__ */ new Map(), Jt?.({ ReactiveElement: T }), (tt.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const pt = globalThis, bt = (i) => i, Y = pt.trustedTypes, wt = Y ? Y.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, Mt = "$lit$", x = `lit$${Math.random().toFixed(9).slice(2)}$`, Ot = "?" + x, Xt = `<${Ot}>`, C = document, N = () => C.createComment(""), H = (i) => i === null || typeof i != "object" && typeof i != "function", ut = Array.isArray, Qt = (i) => ut(i) || typeof i?.[Symbol.iterator] == "function", at = `[ 	
\f\r]`, O = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, xt = /-->/g, St = />/g, A = RegExp(`>|${at}(?:([^\\s"'>=/]+)(${at}*=${at}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), At = /'/g, Et = /"/g, Rt = /^(?:script|style|textarea|title)$/i, te = (i) => (t, ...e) => ({ _$litType$: i, strings: t, values: e }), l = te(1), k = Symbol.for("lit-noChange"), h = Symbol.for("lit-nothing"), Ct = /* @__PURE__ */ new WeakMap(), E = C.createTreeWalker(C, 129);
function Nt(i, t) {
  if (!ut(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return wt !== void 0 ? wt.createHTML(t) : t;
}
const ee = (i, t) => {
  const e = i.length - 1, s = [];
  let r, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = O;
  for (let o = 0; o < e; o++) {
    const c = i[o];
    let d, u, p = -1, $ = 0;
    for (; $ < c.length && (n.lastIndex = $, u = n.exec(c), u !== null); ) $ = n.lastIndex, n === O ? u[1] === "!--" ? n = xt : u[1] !== void 0 ? n = St : u[2] !== void 0 ? (Rt.test(u[2]) && (r = RegExp("</" + u[2], "g")), n = A) : u[3] !== void 0 && (n = A) : n === A ? u[0] === ">" ? (n = r ?? O, p = -1) : u[1] === void 0 ? p = -2 : (p = n.lastIndex - u[2].length, d = u[1], n = u[3] === void 0 ? A : u[3] === '"' ? Et : At) : n === Et || n === At ? n = A : n === xt || n === St ? n = O : (n = A, r = void 0);
    const w = n === A && i[o + 1].startsWith("/>") ? " " : "";
    a += n === O ? c + Xt : p >= 0 ? (s.push(d), c.slice(0, p) + Mt + c.slice(p) + x + w) : c + x + (p === -2 ? o : w);
  }
  return [Nt(i, a + (i[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class z {
  constructor({ strings: t, _$litType$: e }, s) {
    let r;
    this.parts = [];
    let a = 0, n = 0;
    const o = t.length - 1, c = this.parts, [d, u] = ee(t, e);
    if (this.el = z.createElement(d, s), E.currentNode = this.el.content, e === 2 || e === 3) {
      const p = this.el.content.firstChild;
      p.replaceWith(...p.childNodes);
    }
    for (; (r = E.nextNode()) !== null && c.length < o; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const p of r.getAttributeNames()) if (p.endsWith(Mt)) {
          const $ = u[n++], w = r.getAttribute(p).split(x), V = /([.?@])?(.*)/.exec($);
          c.push({ type: 1, index: a, name: V[2], strings: w, ctor: V[1] === "." ? re : V[1] === "?" ? ie : V[1] === "@" ? ae : et }), r.removeAttribute(p);
        } else p.startsWith(x) && (c.push({ type: 6, index: a }), r.removeAttribute(p));
        if (Rt.test(r.tagName)) {
          const p = r.textContent.split(x), $ = p.length - 1;
          if ($ > 0) {
            r.textContent = Y ? Y.emptyScript : "";
            for (let w = 0; w < $; w++) r.append(p[w], N()), E.nextNode(), c.push({ type: 2, index: ++a });
            r.append(p[$], N());
          }
        }
      } else if (r.nodeType === 8) if (r.data === Ot) c.push({ type: 2, index: a });
      else {
        let p = -1;
        for (; (p = r.data.indexOf(x, p + 1)) !== -1; ) c.push({ type: 7, index: a }), p += x.length - 1;
      }
      a++;
    }
  }
  static createElement(t, e) {
    const s = C.createElement("template");
    return s.innerHTML = t, s;
  }
}
function U(i, t, e = i, s) {
  if (t === k) return t;
  let r = s !== void 0 ? e._$Co?.[s] : e._$Cl;
  const a = H(t) ? void 0 : t._$litDirective$;
  return r?.constructor !== a && (r?._$AO?.(!1), a === void 0 ? r = void 0 : (r = new a(i), r._$AT(i, e, s)), s !== void 0 ? (e._$Co ??= [])[s] = r : e._$Cl = r), r !== void 0 && (t = U(i, r._$AS(i, t.values), r, s)), t;
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
    const { el: { content: e }, parts: s } = this._$AD, r = (t?.creationScope ?? C).importNode(e, !0);
    E.currentNode = r;
    let a = E.nextNode(), n = 0, o = 0, c = s[0];
    for (; c !== void 0; ) {
      if (n === c.index) {
        let d;
        c.type === 2 ? d = new D(a, a.nextSibling, this, t) : c.type === 1 ? d = new c.ctor(a, c.name, c.strings, this, t) : c.type === 6 && (d = new ne(a, this, t)), this._$AV.push(d), c = s[++o];
      }
      n !== c?.index && (a = E.nextNode(), n++);
    }
    return E.currentNode = C, r;
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
  constructor(t, e, s, r) {
    this.type = 2, this._$AH = h, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = s, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
    t = U(this, t, e), H(t) ? t === h || t == null || t === "" ? (this._$AH !== h && this._$AR(), this._$AH = h) : t !== this._$AH && t !== k && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Qt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== h && H(this._$AH) ? this._$AA.nextSibling.data = t : this.T(C.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: s } = t, r = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = z.createElement(Nt(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === r) this._$AH.p(e);
    else {
      const a = new se(r, this), n = a.u(this.options);
      a.p(e), this.T(n), this._$AH = a;
    }
  }
  _$AC(t) {
    let e = Ct.get(t.strings);
    return e === void 0 && Ct.set(t.strings, e = new z(t)), e;
  }
  k(t) {
    ut(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, r = 0;
    for (const a of t) r === e.length ? e.push(s = new D(this.O(N()), this.O(N()), this, this.options)) : s = e[r], s._$AI(a), r++;
    r < e.length && (this._$AR(s && s._$AB.nextSibling, r), e.length = r);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const s = bt(t).nextSibling;
      bt(t).remove(), t = s;
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
  constructor(t, e, s, r, a) {
    this.type = 1, this._$AH = h, this._$AN = void 0, this.element = t, this.name = e, this._$AM = r, this.options = a, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = h;
  }
  _$AI(t, e = this, s, r) {
    const a = this.strings;
    let n = !1;
    if (a === void 0) t = U(this, t, e, 0), n = !H(t) || t !== this._$AH && t !== k, n && (this._$AH = t);
    else {
      const o = t;
      let c, d;
      for (t = a[0], c = 0; c < a.length - 1; c++) d = U(this, o[s + c], e, c), d === k && (d = this._$AH[c]), n ||= !H(d) || d !== this._$AH[c], d === h ? t = h : t !== h && (t += (d ?? "") + a[c + 1]), this._$AH[c] = d;
    }
    n && !r && this.j(t);
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
  constructor(t, e, s, r, a) {
    super(t, e, s, r, a), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = U(this, t, e, 0) ?? h) === k) return;
    const s = this._$AH, r = t === h && s !== h || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, a = t !== h && (s === h || r);
    r && this.element.removeEventListener(this.name, this, s), a && this.element.addEventListener(this.name, this, t), this._$AH = t;
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
    U(this, t);
  }
}
const oe = pt.litHtmlPolyfillSupport;
oe?.(z, D), (pt.litHtmlVersions ??= []).push("3.3.3");
const le = (i, t, e) => {
  const s = e?.renderBefore ?? t;
  let r = s._$litPart$;
  if (r === void 0) {
    const a = e?.renderBefore ?? null;
    s._$litPart$ = r = new D(t.insertBefore(N(), a), a, void 0, e ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const _t = globalThis;
let S = class extends T {
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
S._$litElement$ = !0, S.finalized = !0, _t.litElementHydrateSupport?.({ LitElement: S });
const ce = _t.litElementPolyfillSupport;
ce?.({ LitElement: S });
(_t.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const de = { attribute: !0, type: String, converter: Z, reflect: !1, hasChanged: ht }, he = (i = de, t, e) => {
  const { kind: s, metadata: r } = e;
  let a = globalThis.litPropertyMetadata.get(r);
  if (a === void 0 && globalThis.litPropertyMetadata.set(r, a = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), a.set(e.name, i), s === "accessor") {
    const { name: n } = e;
    return { set(o) {
      const c = t.get.call(this);
      t.set.call(this, o), this.requestUpdate(n, c, i, !0, o);
    }, init(o) {
      return o !== void 0 && this.C(n, void 0, i, o), o;
    } };
  }
  if (s === "setter") {
    const { name: n } = e;
    return function(o) {
      const c = this[n];
      t.call(this, o), this.requestUpdate(n, c, i, !0, o);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function m(i) {
  return (t, e) => typeof e == "object" ? he(i, t, e) : ((s, r, a) => {
    const n = r.hasOwnProperty(a);
    return r.constructor.createProperty(a, s), n ? Object.getOwnPropertyDescriptor(r, a) : void 0;
  })(i, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function _(i) {
  return m({ ...i, state: !0, attribute: !1 });
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const pe = { ATTRIBUTE: 1 }, ue = (i) => (...t) => ({ _$litDirective$: i, values: t });
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
const q = ue(class extends _e {
  constructor(i) {
    if (super(i), i.type !== pe.ATTRIBUTE || i.name !== "class" || i.strings?.length > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
  }
  render(i) {
    return " " + Object.keys(i).filter((t) => i[t]).join(" ") + " ";
  }
  update(i, [t]) {
    if (this.st === void 0) {
      this.st = /* @__PURE__ */ new Set(), i.strings !== void 0 && (this.nt = new Set(i.strings.join(" ").split(/\s/).filter((s) => s !== "")));
      for (const s in t) t[s] && !this.nt?.has(s) && this.st.add(s);
      return this.render(t);
    }
    const e = i.element.classList;
    for (const s of this.st) s in t || (e.remove(s), this.st.delete(s));
    for (const s in t) {
      const r = !!t[s];
      r === this.st.has(s) || this.nt?.has(s) || (r ? (e.add(s), this.st.add(s)) : (e.remove(s), this.st.delete(s)));
    }
    return k;
  }
});
async function lt(i, t) {
  return (await i.callWS({
    type: "ev_charging/sessions/list",
    ...t
  })).sessions;
}
function fe(i, t) {
  return i.callWS({ type: "ev_charging/sessions/stats", year: t });
}
async function ge(i) {
  return (await i.callWS({
    type: "ev_charging/vehicles/list"
  })).vehicles;
}
const g = "–";
function I(i, t, e) {
  return new Intl.NumberFormat(t, {
    minimumFractionDigits: e,
    maximumFractionDigits: e
  }).format(i);
}
function y(i, t, e = !1) {
  return i === null ? g : `${e ? "~" : ""}${I(i, t, 3)} kWh`;
}
function P(i, t, e) {
  if (i === null)
    return g;
  try {
    return new Intl.NumberFormat(t, { style: "currency", currency: e }).format(i);
  } catch {
    return `${I(i, t, 2)} ${e}`;
  }
}
function b(i) {
  if (i === null)
    return g;
  const t = Math.round(i);
  if (t < 60)
    return `${t} min`;
  const e = Math.floor(t / 60), s = String(t % 60).padStart(2, "0");
  return `${e}:${s} h`;
}
function G(i, t) {
  return i === null ? g : `${I(i, t, 0)} %`;
}
function me(i, t) {
  return i === null ? g : `${I(i, t, 0)} km`;
}
function ve(i, t) {
  return i === null ? g : `${I(i, t, 1)} kW`;
}
function K(i, t, e) {
  return i === null ? g : new Intl.DateTimeFormat(t, {
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(i));
}
function kt(i, t, e) {
  return i === null ? g : new Intl.DateTimeFormat(t, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(i));
}
function nt(i, t, e) {
  return new Intl.DateTimeFormat(t, { month: e, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, i - 1, 1))
  );
}
const $e = "component.ev_charging.selector.panel.options.";
function J(i) {
  return (t, e) => {
    const s = i[$e + t];
    return s === void 0 ? t : e ? s.replace(
      /\{(\w+)\}/g,
      (r, a) => a in e ? String(e[a]) : r
    ) : s;
  };
}
const ot = /* @__PURE__ */ new Map();
function Ht(i) {
  const t = i.language;
  let e = ot.get(t);
  return e === void 0 && (e = i.callWS({
    type: "frontend/get_translations",
    language: t,
    category: "selector",
    integration: ["ev_charging"]
  }).then((s) => J(s.resources)), e.catch(() => ot.delete(t)), ot.set(t, e)), e;
}
function zt(i, t) {
  return i.vehicle_id === null ? t("unassigned") : i.vehicle_name ?? i.vehicle_id;
}
const ye = [
  "soc_start",
  "soc_end",
  "odometer_km",
  "energy_kwh",
  "energy_grid_kwh",
  "energy_solar_kwh",
  "cost",
  "address"
];
function be(i) {
  return ye.includes(i);
}
function we(i, t) {
  return be(i) ? t(`field_${i}`) : i;
}
const Lt = "__unassigned__", ft = "__none__", X = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: ""
};
function Dt(i, t) {
  const e = new Intl.DateTimeFormat("en-US", {
    timeZone: t,
    year: "numeric",
    month: "numeric"
  }).formatToParts(i), s = (r) => Number(e.find((a) => a.type === r)?.value ?? 0);
  return { year: s("year"), month: s("month") };
}
function xe(i, t) {
  return { view: "overview", ...Dt(i, t), filters: { ...X } };
}
function Se(i, t, e) {
  const s = i * 12 + (t - 1) + e;
  return { year: Math.floor(s / 12), month: s % 12 + 1 };
}
const It = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"]
];
function Ae(i) {
  const t = new URLSearchParams({ year: String(i.year), month: String(i.month) });
  for (const [e, s] of It)
    i.filters[e] !== "" && t.set(s, i.filters[e]);
  return `/${i.view}?${t.toString()}`;
}
function Ee(i, t) {
  const e = {}, s = i.split("/").filter((d) => d !== "")[0];
  (s === "overview" || s === "detail" || s === "recent") && (e.view = s);
  const r = new URLSearchParams(t), a = Number(r.get("year")), n = Number(r.get("month"));
  Number.isInteger(a) && a >= 1e3 && a <= 9999 && Number.isInteger(n) && n >= 1 && n <= 12 && (e.year = a, e.month = n);
  const o = { ...X };
  let c = !1;
  for (const [d, u] of It) {
    const p = r.get(u);
    p && (o[d] = p, c = !0);
  }
  return c && (e.filters = o), e;
}
function Ce(i) {
  return Object.values(i).some((t) => t !== "");
}
function ke(i, t) {
  return i.filter((e) => {
    if (t.vehicle === Lt) {
      if (e.vehicle_id !== null) return !1;
    } else if (t.vehicle !== "" && e.vehicle_id !== t.vehicle)
      return !1;
    if (t.location !== "" && e.location !== t.location || t.chargeType !== "" && e.charge_type !== t.chargeType || t.status !== "" && e.status !== t.status) return !1;
    if (t.card === ft) {
      if (e.card_uid !== null) return !1;
    } else if (t.card !== "" && e.card_uid !== t.card)
      return !1;
    return !0;
  });
}
function Te(i, t) {
  const e = /* @__PURE__ */ new Map();
  for (const s of i)
    e.set(s.id, s.name);
  for (const s of t)
    s.vehicle_id !== null && !e.has(s.vehicle_id) && e.set(s.vehicle_id, s.vehicle_name ?? s.vehicle_id);
  return [...e].map(([s, r]) => ({ value: s, label: r }));
}
function Pe(i, t, e) {
  const s = new Set(
    t.map((a) => a.card_uid).filter((a) => a !== null)
  ), r = /* @__PURE__ */ new Map();
  for (const a of i) {
    const n = [...s].find((o) => o !== "" && a.uid.endsWith(o));
    r.set(n ?? a.uid, a.label || a.uid);
  }
  for (const a of t)
    a.card_uid !== null && !r.has(a.card_uid) && r.set(a.card_uid, a.card_label || a.card_uid);
  return e !== "" && e !== ft && !r.has(e) && r.set(e, e), [...r].map(([a, n]) => ({ value: a, label: n }));
}
function Ue(i, t, e) {
  return [.../* @__PURE__ */ new Set([...i, t, e])].sort((s, r) => r - s);
}
const st = L`
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
var Me = Object.defineProperty, v = (i, t, e, s) => {
  for (var r = void 0, a = i.length - 1, n; a >= 0; a--)
    (n = i[a]) && (r = n(t, e, r) || r);
  return r && Me(t, e, r), r;
};
const Oe = 600 * 1e3, Re = 5, Ne = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z", He = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z", ze = [
  { id: "overview", label: "view_overview" },
  { id: "detail", label: "view_detail" },
  { id: "recent", label: "view_recent" }
], Le = ["home", "home_no_wallbox", "external"], De = ["ac", "dc", "unknown"], Ie = ["complete", "followup_open", "flagged"], je = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" }
];
function Tt(i) {
  return l`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${i} fill="currentColor"></path>
  </svg>`;
}
class f extends S {
  constructor() {
    super(...arguments), this._vehicles = [], this._failed = !1, this._metric = "energy", this._started = !1, this._recentRequested = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => this._refresh(), Oe);
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
        ...xe(/* @__PURE__ */ new Date(), this.hass.config.time_zone),
        ...e,
        filters: { ...X, ...e?.filters }
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
      this._t = await Ht(t);
    } catch (s) {
      this._t = J({}), this._fail(s, e);
      return;
    }
    try {
      this._vehicles = await ge(t);
    } catch (s) {
      this._fail(s, e);
    }
  }
  async _loadStats(t, e, s) {
    try {
      const r = await fe(t, e);
      this._statsKey === e && (this._stats = r);
    } catch (r) {
      this._statsKey === e && this._fail(r, s);
    }
  }
  async _loadSessions(t, e, s, r) {
    const a = `${e}-${s}`;
    try {
      const n = await lt(t, { year: e, month: s });
      this._sessionsKey === a && (this._sessions = n);
    } catch (n) {
      this._sessionsKey === a && this._fail(n, r);
    }
  }
  async _loadRecent(t, e) {
    try {
      this._recent = await lt(t, { limit: Re });
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
    this._state && this._setState(Se(this._state.year, this._state.month, t));
  }
  render() {
    const t = this._state;
    if (!t || !this.hass)
      return h;
    if (this._failed)
      return this._renderError(this._t ?? J({}));
    const e = this._t;
    return e ? l`
      <div class="view">
        ${this._renderTabs(e, t)}
        ${t.view === "recent" ? h : this._renderPeriod(e, t)}
        ${t.view === "overview" ? this._renderOverview(e, t) : t.view === "detail" ? this._renderDetail(e, t) : this._renderRecent(e)}
        <p class="hint muted">${e("multi_day_hint")} ${e("estimate_hint")}</p>
      </div>
    ` : l`<div class="spinner" role="progressbar"></div>`;
  }
  _renderError(t) {
    return l`<div class="message">
      <span>${t("load_error")}</span>
      <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
    </div>`;
  }
  _renderTabs(t, e) {
    return l`<nav class="tabs">
      ${ze.map(
      (s) => l`<button
          class=${q({ tab: !0, active: s.id === e.view })}
          aria-current=${s.id === e.view ? "page" : "false"}
          @click=${() => this._setState({ view: s.id })}
        >
          ${t(s.label)}
        </button>`
    )}
    </nav>`;
  }
  _renderPeriod(t, e) {
    const s = this.hass, r = s.locale.language, a = Dt(/* @__PURE__ */ new Date(), s.config.time_zone), n = Ue(this._stats?.years ?? [], a.year, e.year);
    return l`<div class="period">
      <button class="icon" aria-label=${t("period_previous")} @click=${() => this._shift(-1)}>
        ${Tt(Ne)}
      </button>
      <select
        aria-label=${t("period_month")}
        @change=${(o) => this._setState({ month: Number(o.target.value) })}
      >
        ${Array.from({ length: 12 }, (o, c) => c + 1).map(
      (o) => l`<option value=${o} .selected=${o === e.month}>
              ${nt(o, r, "long")}
            </option>`
    )}
      </select>
      <select
        aria-label=${t("period_year")}
        @change=${(o) => this._setState({ year: Number(o.target.value) })}
      >
        ${n.map(
      (o) => l`<option value=${o} .selected=${o === e.year}>${o}</option>`
    )}
      </select>
      <button class="icon" aria-label=${t("period_next")} @click=${() => this._shift(1)}>
        ${Tt(He)}
      </button>
    </div>`;
  }
  _renderTiles(t, e) {
    const s = this.hass, r = s.locale.language, a = [
      ["total_energy", y(e.energy_kwh, r, e.energy_is_estimate)],
      ["total_cost", P(e.cost, r, s.config.currency)],
      ["total_duration", b(e.charge_duration_min)],
      ["total_sessions", String(e.count)],
      ["open_followups", String(e.open_followups)]
    ];
    return l`<div class="tiles">
      ${a.map(
      ([n, o]) => l`<div class="tile">
          <span class="tile-label muted">${t(n)}</span>
          <span class="tile-value">${o}</span>
        </div>`
    )}
    </div>`;
  }
  _renderOverview(t, e) {
    const s = this._stats;
    return s ? l`
      ${this._renderTiles(t, s.months[e.month - 1])}
      ${this._renderChart(t, e, s)} ${this._renderYearSummary(t, e, s)}
    ` : l`<div class="spinner" role="progressbar"></div>`;
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
        return P(t.cost, s, e.config.currency);
      case "duration":
        return b(t.charge_duration_min);
      default:
        return y(t.energy_kwh, s, t.energy_is_estimate);
    }
  }
  _renderChart(t, e, s) {
    const r = this.hass.locale.language, a = Math.max(...s.months.map((n) => this._metricValue(n)), 0);
    return l`<section class="chart">
      <div class="chart-head">
        <h3>${t("chart_title", { year: e.year })}</h3>
        <label class="metric">
          <span class="muted">${t("chart_metric")}</span>
          <select
            @change=${(n) => {
      this._metric = n.target.value;
    }}
          >
            ${je.map(
      (n) => l`<option value=${n.id} .selected=${n.id === this._metric}>
                  ${t(n.label)}
                </option>`
    )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${s.months.map((n) => {
      const o = a > 0 ? this._metricValue(n) / a * 100 : 0, c = nt(n.month, r, "long"), d = n.count === 0 ? g : this._formatMetric(n);
      return l`<button
            class=${q({ bar: !0, selected: n.month === e.month })}
            title=${`${c}: ${d}`}
            aria-label=${`${c}: ${d}`}
            aria-pressed=${n.month === e.month ? "true" : "false"}
            @click=${() => this._setState({ month: n.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${o}%`}></span></span>
            <span class="bar-label muted">${nt(n.month, r, "short")}</span>
            <span class="bar-value">${d}</span>
          </button>`;
    })}
      </div>
    </section>`;
  }
  _renderYearSummary(t, e, s) {
    const r = this.hass, a = r.locale.language, n = s.year_summary, o = [
      ["scope_total", n.all],
      ["scope_internal", n.internal],
      ["scope_external", n.external]
    ], c = [
      ["total_energy", (d) => y(d.energy_kwh, a, d.energy_is_estimate)],
      ["total_cost", (d) => P(d.cost, a, r.config.currency)],
      ["total_duration", (d) => b(d.charge_duration_min)],
      ["total_sessions", (d) => String(d.count)]
    ];
    return l`<section class="year-summary">
      <h3>${t("year_summary_title", { year: e.year })}</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            ${o.map(([d]) => l`<th class="num">${t(d)}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${c.map(
      ([d, u]) => l`<tr>
              <th>${t(d)}</th>
              ${o.map(([, p]) => l`<td class="num">${u(p)}</td>`)}
            </tr>`
    )}
        </tbody>
      </table>
    </section>`;
  }
  _renderDetail(t, e) {
    const s = this._sessions, r = this._stats;
    if (!s || !r)
      return l`<div class="spinner" role="progressbar"></div>`;
    const a = e.filters, n = ke(s, a), o = [
      ...Te(this._vehicles, s),
      { value: Lt, label: t("unassigned") }
    ], c = [
      { value: ft, label: t("filter_no_card") },
      ...Pe(
        this._vehicles.flatMap((d) => d.cards),
        s,
        a.card
      )
    ];
    return l`
      ${this._renderTiles(t, r.months[e.month - 1])}
      <div class="filters">
        ${this._renderFilter(t("filter_vehicle"), "vehicle", o, t)}
        ${this._renderFilter(
      t("filter_location"),
      "location",
      Le.map((d) => ({ value: d, label: t(`location_${d}`) })),
      t
    )}
        ${this._renderFilter(
      t("filter_charge_type"),
      "chargeType",
      De.map((d) => ({ value: d, label: t(`charge_type_${d}`) })),
      t
    )}
        ${this._renderFilter(t("filter_card"), "card", c, t)}
        ${this._renderFilter(
      t("filter_status"),
      "status",
      Ie.map((d) => ({ value: d, label: t(`status_${d}`) })),
      t
    )}
        ${Ce(a) ? l`<button
              class="text reset"
              @click=${() => this._setState({ filters: { ...X } })}
            >
              ${t("filter_reset")}
            </button>` : h}
      </div>
      <p class="count muted">
        ${t("filter_count", { shown: n.length, total: s.length })}
      </p>
      ${n.length === 0 ? l`<div class="message">
            ${s.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>` : this._renderTable(n, t, !1)}
    `;
  }
  _renderRecent(t) {
    const e = this._recent;
    return e ? e.length === 0 ? l`<div class="message">${t("no_sessions")}</div>` : this._renderTable(e, t, !0) : l`<div class="spinner" role="progressbar"></div>`;
  }
  _renderFilter(t, e, s, r) {
    const a = this._state.filters[e];
    return l`<label class="filter">
      <span class="muted">${t}</span>
      <select
        @change=${(n) => this._setFilter(e, n.target.value)}
      >
        <option value="" .selected=${a === ""}>${r("filter_all")}</option>
        ${s.map(
      (n) => l`<option value=${n.value} .selected=${n.value === a}>
              ${n.label}
            </option>`
    )}
      </select>
    </label>`;
  }
  _renderTable(t, e, s) {
    return l`<div class="table" role="table">
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
      ${t.map((r) => this._renderSession(r, e, s))}
    </div>`;
  }
  _renderSession(t, e, s) {
    const r = this.hass, a = r.locale.language, n = r.config.time_zone, o = t.vehicle_id === null;
    return l`<details class="session" ?open=${s}>
      <summary>
        <span class="c-date">${K(t.plug_start, a, n)}</span>
        <span class=${q({ "c-vehicle": !0, vehicle: !0, unassigned: o })}
          >${zt(t, e)}</span
        >
        <span class="c-location"><span class="chip">${e(`location_${t.location}`)}</span></span>
        <span class="c-type"><span class="chip">${e(`charge_type_${t.charge_type}`)}</span></span>
        <span class="c-energy num"
          >${y(t.energy_kwh, a, t.energy_is_estimate)}</span
        >
        <span class="c-cost num">${P(t.cost, a, r.config.currency)}</span>
        <span class="c-duration num">${b(t.charge_duration_min)}</span>
        <span class="c-status">
          ${t.status === "complete" ? h : l`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
          ${t.location_conflict ? l`<span class="chip alert">${e("flag_location_conflict")}</span>` : h}
          ${t.identification_conflict ? l`<span class="chip alert">${e("flag_identification_conflict")}</span>` : h}
          ${t.charge_error ? l`<span class="chip alert">${e("flag_charge_error")}</span>` : h}
          ${t.energy_unallocated_kwh > 0 ? l`<span class="chip warn">${e("flag_unallocated_energy")}</span>` : h}
        </span>
      </summary>
      ${this._renderSessionBody(t, e)}
    </details>`;
  }
  _row(t, e) {
    return e === null || e === "" || e === g ? h : l`<dt class="muted">${t}</dt>
      <dd>${e}</dd>`;
  }
  _renderSessionBody(t, e) {
    const s = this.hass, r = s.locale.language, a = s.config.time_zone, n = t.location === "home", o = e("detail_not_recorded"), c = t.soc_start === null && t.soc_end === null ? null : `${G(t.soc_start, r)} → ${G(t.soc_end, r)}`, d = t.address ?? (t.latitude !== null && t.longitude !== null ? l`<a
            href=${`https://www.openstreetmap.org/?mlat=${t.latitude}&mlon=${t.longitude}#map=17/${t.latitude}/${t.longitude}`}
            target="_blank"
            rel="noopener noreferrer"
            >${e("detail_map_link")}</a
          >` : null);
    return l`<div class="body">
      <dl>
        ${this._row(e("detail_plug_start"), K(t.plug_start, r, a))}
        ${this._row(e("detail_plug_end"), K(t.plug_end, r, a))}
        ${this._row(e("detail_plug_duration"), b(t.plug_duration_min))}
        ${this._row(e("detail_charge_duration"), b(t.charge_duration_min))}
        ${t.pause_duration_min ? this._row(e("detail_pause_duration"), b(t.pause_duration_min)) : h}
        ${this._row(e("detail_soc"), c)}
        ${this._row(e("detail_odometer"), me(t.odometer_km, r))}
        ${this._row(e("detail_power_avg"), ve(t.power_avg_kw, r))}
        ${n ? l`${this._row(
      e("detail_energy_grid"),
      t.energy_grid_kwh === null ? o : y(t.energy_grid_kwh, r)
    )}
            ${this._row(
      e("detail_energy_solar"),
      t.energy_solar_kwh === null ? o : y(t.energy_solar_kwh, r)
    )}` : h}
        ${t.energy_unallocated_kwh > 0 ? this._row(
      e("detail_energy_unallocated"),
      y(t.energy_unallocated_kwh, r)
    ) : h}
        ${this._row(e("detail_card"), t.card_label ?? t.card_uid)}
        ${this._row(
      e("detail_identification"),
      e(`identification_${t.identification_source}`)
    )}
        ${this._row(e("detail_address"), d)}
        ${this._row(e("detail_provider"), t.provider)}
        ${this._row(e("detail_note"), t.note)}
        ${t.open_fields.length > 0 ? this._row(
      e("detail_open_fields"),
      t.open_fields.map((u) => we(u, e)).join(", ")
    ) : h}
      </dl>
      ${this._renderPhases(t, e)}
    </div>`;
  }
  _renderPhases(t, e) {
    if (!t.phases_recorded || t.phases.length === 0)
      return l`<p class="muted">${e("detail_phases_not_recorded")}</p>`;
    const s = this.hass, r = s.locale.language, a = s.config.time_zone;
    return l`<table class="phases">
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
        ${t.phases.map(
      (n) => l`<tr>
            <td>${kt(n.start, r, a)}</td>
            <td>${kt(n.end, r, a)}</td>
            <td class="num">${b(n.duration_min)}</td>
            <td class="num">${y(n.energy_kwh, r)}</td>
            <td class="num">${P(n.cost, r, s.config.currency)}</td>
          </tr>`
    )}
      </tbody>
    </table>`;
  }
  static {
    this.styles = [
      st,
      L`
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
        gap: 8px;
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
v([
  m({ attribute: !1 })
], f.prototype, "hass");
v([
  m({ attribute: !1 })
], f.prototype, "initialState");
v([
  _()
], f.prototype, "_state");
v([
  _()
], f.prototype, "_t");
v([
  _()
], f.prototype, "_stats");
v([
  _()
], f.prototype, "_sessions");
v([
  _()
], f.prototype, "_recent");
v([
  _()
], f.prototype, "_vehicles");
v([
  _()
], f.prototype, "_failed");
v([
  _()
], f.prototype, "_metric");
var Fe = Object.defineProperty, rt = (i, t, e, s) => {
  for (var r = void 0, a = i.length - 1, n; a >= 0; a--)
    (n = i[a]) && (r = n(t, e, r) || r);
  return r && Fe(t, e, r), r;
};
const Ve = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
class j extends S {
  constructor() {
    super(...arguments), this.narrow = !1;
  }
  willUpdate() {
    this._initialState === void 0 && (this._initialState = Ee(this.route?.path ?? "", window.location.search));
  }
  _toggleMenu() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: !0, composed: !0 }));
  }
  _onStateChanged(t) {
    const e = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${e}${Ae(t.detail)}`);
  }
  render() {
    return l`
      <header>
        ${this.narrow ? l`<button class="menu" @click=${() => this._toggleMenu()}>
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
      L`
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
  m({ attribute: !1 })
], j.prototype, "hass");
rt([
  m({ type: Boolean })
], j.prototype, "narrow");
rt([
  m({ attribute: !1 })
], j.prototype, "route");
rt([
  m({ attribute: !1 })
], j.prototype, "panel");
var Be = Object.defineProperty, jt = (i, t, e, s) => {
  for (var r = void 0, a = i.length - 1, n; a >= 0; a--)
    (n = i[a]) && (r = n(t, e, r) || r);
  return r && Be(t, e, r), r;
};
class gt extends S {
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
    return l`<div class="card">
      <ev-charging-panel-view .hass=${this.hass}></ev-charging-panel-view>
    </div>`;
  }
  static {
    this.styles = [
      st,
      L`
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
jt([
  m({ attribute: !1 })
], gt.prototype, "hass");
jt([
  m({ type: Boolean, reflect: !0, attribute: "is-panel" })
], gt.prototype, "isPanel");
var We = Object.defineProperty, F = (i, t, e, s) => {
  for (var r = void 0, a = i.length - 1, n; a >= 0; a--)
    (n = i[a]) && (r = n(t, e, r) || r);
  return r && We(t, e, r), r;
};
const B = 3, Pt = 20, qe = 600 * 1e3;
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
    }, qe);
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
      this._t = await Ht(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = J({}), this._failed = !0;
      return;
    }
    await this._load(t, !1);
  }
  async _load(t, e) {
    try {
      this._sessions = await lt(t, { limit: this._config.count ?? B }), this._failed = !1;
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
      return l`<div class="spinner" role="progressbar"></div>`;
    const e = this._config.title ?? t("recent_title");
    return this._failed ? l`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>` : l`
      <h2>${e}</h2>
      ${this._sessions === void 0 ? l`<div class="spinner" role="progressbar"></div>` : this._sessions.length === 0 ? l`<div class="message">${t("no_sessions")}</div>` : l`<ul>
              ${this._sessions.map((s) => this._renderSession(s, t))}
            </ul>`}
    `;
  }
  _renderSession(t, e) {
    const s = this.hass, r = s.locale.language, a = t.soc_start !== null && t.soc_end !== null ? `${G(t.soc_start, r)} → ${G(t.soc_end, r)}` : h;
    return l`<li>
      <div class="line">
        <span class=${q({ vehicle: !0, unassigned: t.vehicle_id === null })}
          >${zt(t, e)}</span
        >
        <span class="muted">${K(t.plug_start, r, s.config.time_zone)}</span>
      </div>
      <div class="line">
        <span>
          ${y(t.energy_kwh, r, t.energy_is_estimate)} ·
          ${P(t.cost, r, s.config.currency)} ·
          ${b(t.charge_duration_min)}
        </span>
        <span class="muted">${a}</span>
      </div>
      <div class="line">
        <span class="chip">${e(`location_${t.location}`)}</span>
        ${t.status === "complete" ? h : l`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
      </div>
    </li>`;
  }
  static {
    this.styles = [
      st,
      L`
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
F([
  m({ attribute: !1 })
], M.prototype, "hass");
F([
  _()
], M.prototype, "_config");
F([
  _()
], M.prototype, "_t");
F([
  _()
], M.prototype, "_sessions");
F([
  _()
], M.prototype, "_failed");
function it(i, t) {
  customElements.get(i) || customElements.define(i, t);
}
it("ev-charging-panel-view", f);
it("ev-charging-panel", j);
it("ev-charging-panel-card", gt);
it("ev-charging-recent-card", M);
const Q = window;
Q.customCards = Q.customCards ?? [];
for (const i of ["ev-charging-panel-card", "ev-charging-recent-card"])
  Q.customCards.some((t) => t.type === i) || Q.customCards.push({ type: i, name: i });
