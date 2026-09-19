/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const st = globalThis, yt = st.ShadowRoot && (st.ShadyCSS === void 0 || st.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, bt = Symbol(), Tt = /* @__PURE__ */ new WeakMap();
let Kt = class {
  constructor(t, e, r) {
    if (this._$cssResult$ = !0, r !== bt) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (yt && t === void 0) {
      const r = e !== void 0 && e.length === 1;
      r && (t = Tt.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), r && Tt.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const le = (s) => new Kt(typeof s == "string" ? s : s + "", void 0, bt), b = (s, ...t) => {
  const e = s.length === 1 ? s[0] : t.reduce((r, i, a) => r + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + s[a + 1], s[0]);
  return new Kt(e, s, bt);
}, ce = (s, t) => {
  if (yt) s.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const r = document.createElement("style"), i = st.litNonce;
    i !== void 0 && r.setAttribute("nonce", i), r.textContent = e.cssText, s.appendChild(r);
  }
}, Ut = yt ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const r of t.cssRules) e += r.cssText;
  return le(e);
})(s) : s;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: he, defineProperty: de, getOwnPropertyDescriptor: ue, getOwnPropertyNames: pe, getOwnPropertySymbols: _e, getPrototypeOf: fe } = Object, ht = globalThis, Rt = ht.trustedTypes, ge = Rt ? Rt.emptyScript : "", me = ht.reactiveElementPolyfillSupport, K = (s, t) => s, at = { toAttribute(s, t) {
  switch (t) {
    case Boolean:
      s = s ? ge : null;
      break;
    case Object:
    case Array:
      s = s == null ? s : JSON.stringify(s);
  }
  return s;
}, fromAttribute(s, t) {
  let e = s;
  switch (t) {
    case Boolean:
      e = s !== null;
      break;
    case Number:
      e = s === null ? null : Number(s);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(s);
      } catch {
        e = null;
      }
  }
  return e;
} }, wt = (s, t) => !he(s, t), Ot = { attribute: !0, type: String, converter: at, reflect: !1, useDefault: !1, hasChanged: wt };
Symbol.metadata ??= Symbol("metadata"), ht.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let I = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = Ot) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const r = Symbol(), i = this.getPropertyDescriptor(t, r, e);
      i !== void 0 && de(this.prototype, t, i);
    }
  }
  static getPropertyDescriptor(t, e, r) {
    const { get: i, set: a } = ue(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: i, set(n) {
      const l = i?.call(this);
      a?.call(this, n), this.requestUpdate(t, l, r);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? Ot;
  }
  static _$Ei() {
    if (this.hasOwnProperty(K("elementProperties"))) return;
    const t = fe(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(K("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(K("properties"))) {
      const e = this.properties, r = [...pe(e), ..._e(e)];
      for (const i of r) this.createProperty(i, e[i]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [r, i] of e) this.elementProperties.set(r, i);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, r] of this.elementProperties) {
      const i = this._$Eu(e, r);
      i !== void 0 && this._$Eh.set(i, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const r = new Set(t.flat(1 / 0).reverse());
      for (const i of r) e.unshift(Ut(i));
    } else t !== void 0 && e.push(Ut(t));
    return e;
  }
  static _$Eu(t, e) {
    const r = e.attribute;
    return r === !1 ? void 0 : typeof r == "string" ? r : typeof t == "string" ? t.toLowerCase() : void 0;
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
    for (const r of e.keys()) this.hasOwnProperty(r) && (t.set(r, this[r]), delete this[r]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return ce(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((t) => t.hostConnected?.());
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t) => t.hostDisconnected?.());
  }
  attributeChangedCallback(t, e, r) {
    this._$AK(t, r);
  }
  _$ET(t, e) {
    const r = this.constructor.elementProperties.get(t), i = this.constructor._$Eu(t, r);
    if (i !== void 0 && r.reflect === !0) {
      const a = (r.converter?.toAttribute !== void 0 ? r.converter : at).toAttribute(e, r.type);
      this._$Em = t, a == null ? this.removeAttribute(i) : this.setAttribute(i, a), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const r = this.constructor, i = r._$Eh.get(t);
    if (i !== void 0 && this._$Em !== i) {
      const a = r.getPropertyOptions(i), n = typeof a.converter == "function" ? { fromAttribute: a.converter } : a.converter?.fromAttribute !== void 0 ? a.converter : at;
      this._$Em = i;
      const l = n.fromAttribute(e, a.type);
      this[i] = l ?? this._$Ej?.get(i) ?? l, this._$Em = null;
    }
  }
  requestUpdate(t, e, r, i = !1, a) {
    if (t !== void 0) {
      const n = this.constructor;
      if (i === !1 && (a = this[t]), r ??= n.getPropertyOptions(t), !((r.hasChanged ?? wt)(a, e) || r.useDefault && r.reflect && a === this._$Ej?.get(t) && !this.hasAttribute(n._$Eu(t, r)))) return;
      this.C(t, e, r);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: r, reflect: i, wrapped: a }, n) {
    r && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, n ?? e ?? this[t]), a !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || r || (e = void 0), this._$AL.set(t, e)), i === !0 && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
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
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [i, a] of r) {
        const { wrapped: n } = a, l = this[i];
        n !== !0 || this._$AL.has(i) || l === void 0 || this.C(i, void 0, a, l);
      }
    }
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), this._$EO?.forEach((r) => r.hostUpdate?.()), this.update(e)) : this._$EM();
    } catch (r) {
      throw t = !1, this._$EM(), r;
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
I.elementStyles = [], I.shadowRootOptions = { mode: "open" }, I[K("elementProperties")] = /* @__PURE__ */ new Map(), I[K("finalized")] = /* @__PURE__ */ new Map(), me?.({ ReactiveElement: I }), (ht.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const xt = globalThis, Nt = (s) => s, nt = xt.trustedTypes, zt = nt ? nt.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, Yt = "$lit$", C = `lit$${Math.random().toFixed(9).slice(2)}$`, Zt = "?" + C, ve = `<${Zt}>`, z = document, Y = () => z.createComment(""), Z = (s) => s === null || typeof s != "object" && typeof s != "function", St = Array.isArray, $e = (s) => St(s) || typeof s?.[Symbol.iterator] == "function", ft = `[ 	
\f\r]`, q = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Dt = /-->/g, Ht = />/g, O = RegExp(`>|${ft}(?:([^\\s"'>=/]+)(${ft}*=${ft}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), It = /'/g, Lt = /"/g, Gt = /^(?:script|style|textarea|title)$/i, ye = (s) => (t, ...e) => ({ _$litType$: s, strings: t, values: e }), o = ye(1), D = Symbol.for("lit-noChange"), h = Symbol.for("lit-nothing"), Ft = /* @__PURE__ */ new WeakMap(), N = z.createTreeWalker(z, 129);
function Jt(s, t) {
  if (!St(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return zt !== void 0 ? zt.createHTML(t) : t;
}
const be = (s, t) => {
  const e = s.length - 1, r = [];
  let i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = q;
  for (let l = 0; l < e; l++) {
    const c = s[l];
    let d, _, u = -1, x = 0;
    for (; x < c.length && (n.lastIndex = x, _ = n.exec(c), _ !== null); ) x = n.lastIndex, n === q ? _[1] === "!--" ? n = Dt : _[1] !== void 0 ? n = Ht : _[2] !== void 0 ? (Gt.test(_[2]) && (i = RegExp("</" + _[2], "g")), n = O) : _[3] !== void 0 && (n = O) : n === O ? _[0] === ">" ? (n = i ?? q, u = -1) : _[1] === void 0 ? u = -2 : (u = n.lastIndex - _[2].length, d = _[1], n = _[3] === void 0 ? O : _[3] === '"' ? Lt : It) : n === Lt || n === It ? n = O : n === Dt || n === Ht ? n = q : (n = O, i = void 0);
    const E = n === O && s[l + 1].startsWith("/>") ? " " : "";
    a += n === q ? c + ve : u >= 0 ? (r.push(d), c.slice(0, u) + Yt + c.slice(u) + C + E) : c + C + (u === -2 ? l : E);
  }
  return [Jt(s, a + (s[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
};
class G {
  constructor({ strings: t, _$litType$: e }, r) {
    let i;
    this.parts = [];
    let a = 0, n = 0;
    const l = t.length - 1, c = this.parts, [d, _] = be(t, e);
    if (this.el = G.createElement(d, r), N.currentNode = this.el.content, e === 2 || e === 3) {
      const u = this.el.content.firstChild;
      u.replaceWith(...u.childNodes);
    }
    for (; (i = N.nextNode()) !== null && c.length < l; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const u of i.getAttributeNames()) if (u.endsWith(Yt)) {
          const x = _[n++], E = i.getAttribute(u).split(C), rt = /([.?@])?(.*)/.exec(x);
          c.push({ type: 1, index: a, name: rt[2], strings: E, ctor: rt[1] === "." ? xe : rt[1] === "?" ? Se : rt[1] === "@" ? Ae : dt }), i.removeAttribute(u);
        } else u.startsWith(C) && (c.push({ type: 6, index: a }), i.removeAttribute(u));
        if (Gt.test(i.tagName)) {
          const u = i.textContent.split(C), x = u.length - 1;
          if (x > 0) {
            i.textContent = nt ? nt.emptyScript : "";
            for (let E = 0; E < x; E++) i.append(u[E], Y()), N.nextNode(), c.push({ type: 2, index: ++a });
            i.append(u[x], Y());
          }
        }
      } else if (i.nodeType === 8) if (i.data === Zt) c.push({ type: 2, index: a });
      else {
        let u = -1;
        for (; (u = i.data.indexOf(C, u + 1)) !== -1; ) c.push({ type: 7, index: a }), u += C.length - 1;
      }
      a++;
    }
  }
  static createElement(t, e) {
    const r = z.createElement("template");
    return r.innerHTML = t, r;
  }
}
function j(s, t, e = s, r) {
  if (t === D) return t;
  let i = r !== void 0 ? e._$Co?.[r] : e._$Cl;
  const a = Z(t) ? void 0 : t._$litDirective$;
  return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(s), i._$AT(s, e, r)), r !== void 0 ? (e._$Co ??= [])[r] = i : e._$Cl = i), i !== void 0 && (t = j(s, i._$AS(s, t.values), i, r)), t;
}
class we {
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
    const { el: { content: e }, parts: r } = this._$AD, i = (t?.creationScope ?? z).importNode(e, !0);
    N.currentNode = i;
    let a = N.nextNode(), n = 0, l = 0, c = r[0];
    for (; c !== void 0; ) {
      if (n === c.index) {
        let d;
        c.type === 2 ? d = new X(a, a.nextSibling, this, t) : c.type === 1 ? d = new c.ctor(a, c.name, c.strings, this, t) : c.type === 6 && (d = new Ee(a, this, t)), this._$AV.push(d), c = r[++l];
      }
      n !== c?.index && (a = N.nextNode(), n++);
    }
    return N.currentNode = z, i;
  }
  p(t) {
    let e = 0;
    for (const r of this._$AV) r !== void 0 && (r.strings !== void 0 ? (r._$AI(t, r, e), e += r.strings.length - 2) : r._$AI(t[e])), e++;
  }
}
class X {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, e, r, i) {
    this.type = 2, this._$AH = h, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = r, this.options = i, this._$Cv = i?.isConnected ?? !0;
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
    t = j(this, t, e), Z(t) ? t === h || t == null || t === "" ? (this._$AH !== h && this._$AR(), this._$AH = h) : t !== this._$AH && t !== D && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : $e(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== h && Z(this._$AH) ? this._$AA.nextSibling.data = t : this.T(z.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: r } = t, i = typeof r == "number" ? this._$AC(t) : (r.el === void 0 && (r.el = G.createElement(Jt(r.h, r.h[0]), this.options)), r);
    if (this._$AH?._$AD === i) this._$AH.p(e);
    else {
      const a = new we(i, this), n = a.u(this.options);
      a.p(e), this.T(n), this._$AH = a;
    }
  }
  _$AC(t) {
    let e = Ft.get(t.strings);
    return e === void 0 && Ft.set(t.strings, e = new G(t)), e;
  }
  k(t) {
    St(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let r, i = 0;
    for (const a of t) i === e.length ? e.push(r = new X(this.O(Y()), this.O(Y()), this, this.options)) : r = e[i], r._$AI(a), i++;
    i < e.length && (this._$AR(r && r._$AB.nextSibling, i), e.length = i);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const r = Nt(t).nextSibling;
      Nt(t).remove(), t = r;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class dt {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, r, i, a) {
    this.type = 1, this._$AH = h, this._$AN = void 0, this.element = t, this.name = e, this._$AM = i, this.options = a, r.length > 2 || r[0] !== "" || r[1] !== "" ? (this._$AH = Array(r.length - 1).fill(new String()), this.strings = r) : this._$AH = h;
  }
  _$AI(t, e = this, r, i) {
    const a = this.strings;
    let n = !1;
    if (a === void 0) t = j(this, t, e, 0), n = !Z(t) || t !== this._$AH && t !== D, n && (this._$AH = t);
    else {
      const l = t;
      let c, d;
      for (t = a[0], c = 0; c < a.length - 1; c++) d = j(this, l[r + c], e, c), d === D && (d = this._$AH[c]), n ||= !Z(d) || d !== this._$AH[c], d === h ? t = h : t !== h && (t += (d ?? "") + a[c + 1]), this._$AH[c] = d;
    }
    n && !i && this.j(t);
  }
  j(t) {
    t === h ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class xe extends dt {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === h ? void 0 : t;
  }
}
class Se extends dt {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== h);
  }
}
class Ae extends dt {
  constructor(t, e, r, i, a) {
    super(t, e, r, i, a), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = j(this, t, e, 0) ?? h) === D) return;
    const r = this._$AH, i = t === h && r !== h || t.capture !== r.capture || t.once !== r.once || t.passive !== r.passive, a = t !== h && (r === h || i);
    i && this.element.removeEventListener(this.name, this, r), a && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Ee {
  constructor(t, e, r) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = r;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    j(this, t);
  }
}
const Ce = xt.litHtmlPolyfillSupport;
Ce?.(G, X), (xt.litHtmlVersions ??= []).push("3.3.3");
const ke = (s, t, e) => {
  const r = e?.renderBefore ?? t;
  let i = r._$litPart$;
  if (i === void 0) {
    const a = e?.renderBefore ?? null;
    r._$litPart$ = i = new X(t.insertBefore(Y(), a), a, void 0, e ?? {});
  }
  return i._$AI(s), i;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const At = globalThis;
let v = class extends I {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t.firstChild, t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = ke(e, this.renderRoot, this.renderOptions);
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
v._$litElement$ = !0, v.finalized = !0, At.litElementHydrateSupport?.({ LitElement: v });
const Pe = At.litElementPolyfillSupport;
Pe?.({ LitElement: v });
(At.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Me = { attribute: !0, type: String, converter: at, reflect: !1, hasChanged: wt }, Te = (s = Me, t, e) => {
  const { kind: r, metadata: i } = e;
  let a = globalThis.litPropertyMetadata.get(i);
  if (a === void 0 && globalThis.litPropertyMetadata.set(i, a = /* @__PURE__ */ new Map()), r === "setter" && ((s = Object.create(s)).wrapped = !0), a.set(e.name, s), r === "accessor") {
    const { name: n } = e;
    return { set(l) {
      const c = t.get.call(this);
      t.set.call(this, l), this.requestUpdate(n, c, s, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(n, void 0, s, l), l;
    } };
  }
  if (r === "setter") {
    const { name: n } = e;
    return function(l) {
      const c = this[n];
      t.call(this, l), this.requestUpdate(n, c, s, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + r);
};
function g(s) {
  return (t, e) => typeof e == "object" ? Te(s, t, e) : ((r, i, a) => {
    const n = i.hasOwnProperty(a);
    return i.constructor.createProperty(a, r), n ? Object.getOwnPropertyDescriptor(i, a) : void 0;
  })(s, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function p(s) {
  return g({ ...s, state: !0, attribute: !1 });
}
const m = "–";
function P(s, t, e) {
  return new Intl.NumberFormat(t, {
    minimumFractionDigits: e,
    maximumFractionDigits: e
  }).format(s);
}
function $(s, t, e = !1) {
  return s === null ? m : `${e ? "~" : ""}${P(s, t, 3)} kWh`;
}
function jt(s, t, e = !1) {
  return s === null ? m : `${e ? "~" : ""}${P(s, t, 0)} kWh`;
}
function Vt(s, t, e) {
  if (s === null)
    return m;
  try {
    return new Intl.NumberFormat(t, {
      style: "currency",
      currency: e,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(s);
  } catch {
    return `${P(s, t, 0)} ${e}`;
  }
}
function Wt(s) {
  if (s === null)
    return m;
  const t = Math.round(s);
  return t < 60 ? `${t} min` : `${Math.round(t / 60)} h`;
}
function V(s, t, e) {
  if (s === null)
    return m;
  try {
    return new Intl.NumberFormat(t, { style: "currency", currency: e }).format(s);
  } catch {
    return `${P(s, t, 2)} ${e}`;
  }
}
function Ue(s, t, e) {
  if (s === null)
    return m;
  try {
    return `${new Intl.NumberFormat(t, {
      style: "currency",
      currency: e,
      minimumFractionDigits: 3,
      maximumFractionDigits: 4
    }).format(s)} / kWh`;
  } catch {
    return `${P(s, t, 4)} ${e} / kWh`;
  }
}
function S(s) {
  if (s === null)
    return m;
  const t = Math.round(s);
  if (t < 60)
    return `${t} min`;
  const e = Math.floor(t / 60), r = String(t % 60).padStart(2, "0");
  return `${e}:${r} h`;
}
function k(s, t) {
  return s === null ? m : `${P(s, t, 0)} %`;
}
function Re(s, t) {
  return s === null ? m : `${P(s, t, 0)} km`;
}
function Xt(s, t) {
  return s === null ? m : `${P(s, t, 1)} kW`;
}
function ot(s, t, e) {
  return s === null ? m : new Intl.DateTimeFormat(t, {
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(s));
}
function $t(s, t, e) {
  return s === null ? m : new Intl.DateTimeFormat(t, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(s));
}
function gt(s, t, e) {
  return new Intl.DateTimeFormat(t, { month: e, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, s - 1, 1))
  );
}
const Oe = "component.ev_charging.selector.panel.options.";
function H(s) {
  return (t, e) => {
    const r = s[Oe + t];
    return r === void 0 ? t : e ? r.replace(
      /\{(\w+)\}/g,
      (i, a) => a in e ? String(e[a]) : i
    ) : r;
  };
}
const mt = /* @__PURE__ */ new Map();
function Q(s) {
  const t = s.language;
  let e = mt.get(t);
  return e === void 0 && (e = s.callWS({
    type: "frontend/get_translations",
    language: t,
    category: "selector",
    integration: ["ev_charging"]
  }).then((r) => H(r.resources)), e.catch(() => mt.delete(t)), mt.set(t, e)), e;
}
const Qt = 6e4;
function Ne(s, t, e) {
  if (s.net_duration_min === null)
    return null;
  const r = s.state === "candidate" || s.state === "charging";
  return s.net_duration_min + (r ? (e - t) / Qt : 0);
}
function ze(s, t) {
  return s.session_start === null ? null : Math.max((t - new Date(s.session_start).getTime()) / Qt, 0);
}
function De(s) {
  const t = s.energy_grid_kwh, e = s.energy_solar_kwh;
  return t === null || e === null || t + e <= 0 ? null : e / (t + e) * 100;
}
function He(s) {
  let t = 0, e = 0;
  for (const r of s)
    r.energy_grid_kwh !== null && r.energy_solar_kwh !== null && (t += r.energy_grid_kwh, e += r.energy_solar_kwh);
  return t + e > 0 ? e / (t + e) * 100 : null;
}
const M = b`
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
var Ie = Object.defineProperty, T = (s, t, e, r) => {
  for (var i = void 0, a = s.length - 1, n; a >= 0; a--)
    (n = s[a]) && (i = n(t, e, i) || i);
  return i && Ie(t, e, i), i;
};
const Le = "ev_charging/live/subscribe", Fe = 1e3;
class A extends v {
  constructor() {
    super(...arguments), this._config = {}, this._received = 0, this._now = Date.now(), this._failed = !1, this._noWallbox = !1, this._started = !1;
  }
  setConfig(t) {
    this._config = t;
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
    }, Fe), this.hass && this._started && this._subscribe(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._started);
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass));
  }
  async _start(t) {
    try {
      this._t = await Q(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = H({});
    }
    await this._subscribe(t);
  }
  async _subscribe(t) {
    this._release(), this._failed = !1, this._noWallbox = !1;
    const e = t.connection.subscribeMessage(
      (r) => {
        this._live = r, this._received = Date.now(), this._now = this._received;
      },
      { type: Le }
    );
    this._unsubscribe = e;
    try {
      await e;
    } catch (r) {
      this._unsubscribe = void 0, r.code === "not_found" ? this._noWallbox = !0 : (console.error("ev_charging: subscribing to the live values failed", r), this._failed = !0);
    }
  }
  _release() {
    const t = this._unsubscribe;
    this._unsubscribe = void 0, t?.then(
      (e) => e(),
      () => {
      }
    );
  }
  _retry() {
    this.hass && this._subscribe(this.hass);
  }
  _row(t, e) {
    return o`<div class="row">
      <dt>${t}</dt>
      <dd>${e}</dd>
    </div>`;
  }
  _vehicle(t, e) {
    return t.vehicle_guest ? o`<div class="vehicle">${e("live_vehicle_guest")}</div>` : t.vehicle === null ? o`<div class="vehicle unassigned">${e("unassigned")}</div>` : o`<div class="vehicle">${t.vehicle.name}</div>`;
  }
  _soc(t, e, r) {
    if (t.soc_start === null && t.soc === null)
      return h;
    const i = t.soc_start !== null && t.soc !== null ? `${k(t.soc_start, r)} → ${k(t.soc, r)}` : k(t.soc ?? t.soc_start, r), a = t.soc_target === null ? "" : ` (${e("live_soc_target", { target: t.soc_target })})`;
    return this._row(e("live_soc"), `${i}${a}`);
  }
  _flags(t, e) {
    const r = [];
    return t.charge_error && r.push(o`<span class="chip alert">${e("flag_charge_error")}</span>`), t.location_conflict && r.push(o`<span class="chip warn">${e("flag_location_conflict")}</span>`), t.flagged && r.push(o`<span class="chip warn">${e("status_flagged")}</span>`), r.length === 0 ? h : o`<div class="flags">${r}</div>`;
  }
  _details(t, e, r) {
    const i = r.locale?.language ?? r.language, a = t.currency || r.config.currency, n = De(t), l = t.energy_grid_kwh === null || t.energy_solar_kwh === null ? h : this._row(
      `${e("detail_energy_grid")} / ${e("detail_energy_solar")}`,
      `${$(t.energy_grid_kwh, i)} / ${$(
        t.energy_solar_kwh,
        i
      )}${n === null ? "" : ` (${e("live_solar_share", { percent: Math.round(n) })})`}`
    ), c = t.effective_price === null ? h : this._row(
      e("live_price"),
      Ue(t.effective_price, i, a)
    ), d = t.charge_end === null ? h : this._row(e("live_charge_end"), $t(t.charge_end, i, r.config.time_zone));
    return o`<dl>
      ${this._soc(t, e, i)}
      ${this._row(e("live_power"), Xt(t.charge_power_kw, i))}
      ${this._row(e("live_energy"), $(t.energy_kwh, i))} ${l}
      ${this._row(e("live_cost"), V(t.cost, i, a))} ${c}
      ${this._row(
      e("live_charge_time"),
      S(Ne(t, this._received, this._now))
    )}
      ${this._row(e("live_plug_time"), S(ze(t, this._now)))}
      ${d}
    </dl>`;
  }
  render() {
    const t = this._t, e = this.hass;
    if (!t || !e)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = this._config.title ?? t("live_title");
    if (this._noWallbox)
      return o`<h2>${r}</h2>
        <div class="message">${t("live_no_wallbox")}</div>`;
    if (this._failed)
      return o`<h2>${r}</h2>
        <div class="message">
          <span>${t("load_error")}</span>
          <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
        </div>`;
    const i = this._live;
    if (i === void 0)
      return o`<h2>${r}</h2>
        <div class="spinner" role="progressbar"></div>`;
    if (!i.active)
      return o`<h2>${r}</h2>
        <div class="message">${t("live_idle")}</div>`;
    const a = `live_state_${i.state}`;
    return o`
      <h2>
        <span>${r}</span>
        <span class="chip ${i.state === "error" ? "alert" : ""}"
          >${t(a)}</span
        >
      </h2>
      ${this._vehicle(i, t)} ${this._details(i, t, e)} ${this._flags(i, t)}
    `;
  }
  static {
    this.styles = [
      M,
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
T([
  g({ attribute: !1 })
], A.prototype, "hass");
T([
  p()
], A.prototype, "_config");
T([
  p()
], A.prototype, "_t");
T([
  p()
], A.prototype, "_live");
T([
  p()
], A.prototype, "_received");
T([
  p()
], A.prototype, "_now");
T([
  p()
], A.prototype, "_failed");
T([
  p()
], A.prototype, "_noWallbox");
async function Et(s, t) {
  return (await s.callWS({
    type: "ev_charging/sessions/list",
    ...t
  })).sessions;
}
function je(s, t) {
  return s.callWS({ type: "ev_charging/sessions/list", year: t });
}
async function Ve(s) {
  return (await s.callWS({
    type: "ev_charging/vehicles/list"
  })).vehicles;
}
const te = "__unassigned__", Ct = "__none__", lt = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: ""
};
function J(s, t) {
  const e = new Intl.DateTimeFormat("en-US", {
    timeZone: t,
    year: "numeric",
    month: "numeric"
  }).formatToParts(s), r = (i) => Number(e.find((a) => a.type === i)?.value ?? 0);
  return { year: r("year"), month: r("month") };
}
function We(s, t) {
  return { view: "overview", ...J(s, t), filters: { ...lt } };
}
function Be(s, t, e) {
  const r = s * 12 + (t - 1) + e;
  return { year: Math.floor(r / 12), month: r % 12 + 1 };
}
const ee = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"]
];
function qe(s) {
  const t = new URLSearchParams({ year: String(s.year), month: String(s.month) });
  for (const [e, r] of ee)
    s.filters[e] !== "" && t.set(r, s.filters[e]);
  return `/${s.view}?${t.toString()}`;
}
function Ke(s, t) {
  const e = {}, r = s.split("/").filter((d) => d !== "")[0];
  (r === "overview" || r === "detail" || r === "recent") && (e.view = r);
  const i = new URLSearchParams(t), a = Number(i.get("year")), n = Number(i.get("month"));
  Number.isInteger(a) && a >= 1e3 && a <= 9999 && Number.isInteger(n) && n >= 1 && n <= 12 && (e.year = a, e.month = n);
  const l = { ...lt };
  let c = !1;
  for (const [d, _] of ee) {
    const u = i.get(_);
    u && (l[d] = u, c = !0);
  }
  return c && (e.filters = l), e;
}
function vt(s) {
  const t = s.reduce((e, r) => e + (r ?? 0), 0);
  return Math.round(t * 1e4) / 1e4;
}
function F(s) {
  return {
    count: s.length,
    energy_kwh: vt(s.map((t) => t.energy_kwh)),
    energy_is_estimate: s.some((t) => t.energy_is_estimate),
    cost: vt(s.map((t) => t.cost)),
    charge_duration_min: vt(s.map((t) => t.charge_duration_min)),
    open_followups: s.filter(
      (t) => t.status === "followup_open" || t.open_fields.length > 0
    ).length
  };
}
function Ye(s, t) {
  return J(new Date(s.plug_start), t).month;
}
function re(s, t, e) {
  return s.filter((r) => Ye(r, e) === t);
}
function Ze(s, t) {
  return Array.from({ length: 12 }, (e, r) => ({
    month: r + 1,
    ...F(re(s, r + 1, t))
  }));
}
function Ge(s) {
  const t = s.filter((r) => r.location === "external"), e = s.filter((r) => r.location !== "external");
  return {
    all: F(s),
    internal: F(e),
    external: F(t)
  };
}
function Je(s) {
  let t = null;
  return s.latitude !== null && s.longitude !== null ? t = `${s.latitude},${s.longitude}` : s.address && (t = s.address), t === null ? null : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(t)}`;
}
function Xe(s) {
  return Object.values(s).some((t) => t !== "");
}
function Bt(s, t) {
  return s.filter((e) => {
    if (t.vehicle === te) {
      if (e.vehicle_id !== null) return !1;
    } else if (t.vehicle !== "" && e.vehicle_id !== t.vehicle)
      return !1;
    if (t.location !== "" && e.location !== t.location || t.chargeType !== "" && e.charge_type !== t.chargeType || t.status !== "" && e.status !== t.status) return !1;
    if (t.card === Ct) {
      if (e.card_uid !== null) return !1;
    } else if (t.card !== "" && e.card_uid !== t.card)
      return !1;
    return !0;
  });
}
function Qe(s, t) {
  const e = /* @__PURE__ */ new Map();
  for (const r of s)
    e.set(r.id, r.name);
  for (const r of t)
    r.vehicle_id !== null && !e.has(r.vehicle_id) && e.set(r.vehicle_id, r.vehicle_name ?? r.vehicle_id);
  return [...e].map(([r, i]) => ({ value: r, label: i }));
}
function tr(s, t, e) {
  const r = new Set(
    t.map((a) => a.card_uid).filter((a) => a !== null)
  ), i = /* @__PURE__ */ new Map();
  for (const a of s) {
    const n = [...r].find((l) => l !== "" && a.uid.endsWith(l));
    i.set(n ?? a.uid, a.label || a.uid);
  }
  for (const a of t)
    a.card_uid !== null && !i.has(a.card_uid) && i.set(a.card_uid, a.card_label || a.card_uid);
  return e !== "" && e !== Ct && !i.has(e) && i.set(e, e), [...i].map(([a, n]) => ({ value: a, label: n }));
}
function er(s, t, e) {
  return [.../* @__PURE__ */ new Set([...s, t, e])].sort((r, i) => i - r);
}
var rr = Object.defineProperty, tt = (s, t, e, r) => {
  for (var i = void 0, a = s.length - 1, n; a >= 0; a--)
    (n = s[a]) && (i = n(t, e, i) || i);
  return i && rr(t, e, i), i;
};
const sr = 600 * 1e3, ir = "ev_charging/live/subscribe";
class W extends v {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1, this._wasActive = !1;
  }
  setConfig(t) {
    this._config = t;
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
    }, sr), this.hass && this._started && this._watchSessions(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._started);
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass));
  }
  async _start(t) {
    try {
      this._t = await Q(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = H({}), this._failed = !0;
      return;
    }
    this._watchSessions(t), await this._load(t, !1);
  }
  // A running session ending changes the month, so it is worth a reload.
  _watchSessions(t) {
    this._release(), this._unsubscribe = t.connection.subscribeMessage(
      (e) => {
        this._wasActive && !e.active && this.hass && this._load(this.hass, !0), this._wasActive = e.active;
      },
      { type: ir }
    ), this._unsubscribe.catch(() => {
      this._unsubscribe = void 0;
    });
  }
  _release() {
    const t = this._unsubscribe;
    this._unsubscribe = void 0, t?.then(
      (e) => e(),
      () => {
      }
    );
  }
  async _load(t, e) {
    const { year: r, month: i } = J(/* @__PURE__ */ new Date(), t.config.time_zone);
    try {
      this._sessions = await Et(t, { year: r, month: i }), this._failed = !1;
    } catch (a) {
      console.error("ev_charging: loading sessions failed", a), e || (this._failed = !0);
    }
  }
  _retry() {
    this.hass && (this._failed = !1, this._started = !1, this.requestUpdate());
  }
  _row(t, e) {
    return o`<div class="row">
      <dt>${t}</dt>
      <dd>${e}</dd>
    </div>`;
  }
  render() {
    const t = this._t, e = this.hass;
    if (!t || !e)
      return o`<div class="spinner" role="progressbar"></div>`;
    if (this._failed)
      return o`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>`;
    const r = e.locale?.language ?? e.language, { year: i, month: a } = J(/* @__PURE__ */ new Date(), e.config.time_zone), n = this._config.title ?? new Intl.DateTimeFormat(r, { month: "long", year: "numeric", timeZone: "UTC" }).format(
      new Date(Date.UTC(i, a - 1, 1))
    );
    if (this._sessions === void 0)
      return o`<h2>${n}</h2>
        <div class="spinner" role="progressbar"></div>`;
    const l = F(this._sessions), c = He(this._sessions);
    return o`
      <h2>${n}</h2>
      <dl>
        ${this._row(t("total_energy"), $(l.energy_kwh, r, l.energy_is_estimate))}
        ${this._row(t("total_cost"), V(l.cost, r, e.config.currency))}
        ${this._row(t("month_solar_share"), k(c, r))}
      </dl>
    `;
  }
  static {
    this.styles = [
      M,
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
tt([
  g({ attribute: !1 })
], W.prototype, "hass");
tt([
  p()
], W.prototype, "_config");
tt([
  p()
], W.prototype, "_t");
tt([
  p()
], W.prototype, "_sessions");
tt([
  p()
], W.prototype, "_failed");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ar = { ATTRIBUTE: 1 }, nr = (s) => (...t) => ({ _$litDirective$: s, values: t });
class or {
  constructor(t) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(t, e, r) {
    this._$Ct = t, this._$AM = e, this._$Ci = r;
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
const it = nr(class extends or {
  constructor(s) {
    if (super(s), s.type !== ar.ATTRIBUTE || s.name !== "class" || s.strings?.length > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
  }
  render(s) {
    return " " + Object.keys(s).filter((t) => s[t]).join(" ") + " ";
  }
  update(s, [t]) {
    if (this.st === void 0) {
      this.st = /* @__PURE__ */ new Set(), s.strings !== void 0 && (this.nt = new Set(s.strings.join(" ").split(/\s/).filter((r) => r !== "")));
      for (const r in t) t[r] && !this.nt?.has(r) && this.st.add(r);
      return this.render(t);
    }
    const e = s.element.classList;
    for (const r of this.st) r in t || (e.remove(r), this.st.delete(r));
    for (const r in t) {
      const i = !!t[r];
      i === this.st.has(r) || this.nt?.has(r) || (i ? (e.add(r), this.st.add(r)) : (e.remove(r), this.st.delete(r)));
    }
    return D;
  }
});
function se(s, t) {
  return s.vehicle_id === null ? t("unassigned") : s.vehicle_name ?? s.vehicle_id;
}
const lr = [
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
function cr(s) {
  return lr.includes(s);
}
function hr(s, t) {
  return cr(s) ? t(`field_${s}`) : s;
}
const dr = "M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z";
function f(s, t) {
  return t === null || t === "" || t === m ? h : o`<dt class="muted">${s}</dt>
    <dd>${t}</dd>`;
}
function ur(s, t) {
  const e = Je(s);
  return s.address === null && e === null ? null : o`${s.address ?? h}${e === null ? h : o`<a
        class="map"
        href=${e}
        target="_blank"
        rel="noopener noreferrer"
        title=${t("detail_map_link")}
        aria-label=${t("detail_map_link")}
        ><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d=${dr} fill="currentColor"></path></svg
        >${s.address === null ? t("detail_map_link") : h}</a
      >`}`;
}
function pr(s, t, e) {
  if (!s.phases_recorded || s.phases.length === 0)
    return o`<p class="muted">${t("detail_phases_not_recorded")}</p>`;
  const r = e.locale.language, i = e.config.time_zone;
  return o`<table class="phases">
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
      ${s.phases.map(
    (a) => o`<tr>
          <td>${$t(a.start, r, i)}</td>
          <td>${$t(a.end, r, i)}</td>
          <td class="num">${S(a.duration_min)}</td>
          <td class="num">${$(a.energy_kwh, r)}</td>
          <td class="num">${V(a.cost, r, e.config.currency)}</td>
        </tr>`
  )}
    </tbody>
  </table>`;
}
function ie(s, t, e) {
  const r = e.locale.language, i = e.config.time_zone, a = t("detail_not_recorded"), n = s.soc_start === null && s.soc_end === null ? null : `${k(s.soc_start, r)} → ${k(s.soc_end, r)}`;
  return o`<div class="body">
    <dl>
      ${f(t("detail_plug_start"), ot(s.plug_start, r, i))}
      ${f(t("detail_plug_end"), ot(s.plug_end, r, i))}
      ${f(t("detail_plug_duration"), S(s.plug_duration_min))}
      ${f(t("detail_charge_duration"), S(s.charge_duration_min))}
      ${s.pause_duration_min ? f(t("detail_pause_duration"), S(s.pause_duration_min)) : h}
      ${f(t("detail_soc"), n)}
      ${f(t("detail_odometer"), Re(s.odometer_km, r))}
      ${f(t("detail_power_avg"), Xt(s.power_avg_kw, r))}
      ${s.location === "home" ? o`${f(
    t("detail_energy_grid"),
    s.energy_grid_kwh === null ? a : $(s.energy_grid_kwh, r)
  )}
          ${f(
    t("detail_energy_solar"),
    s.energy_solar_kwh === null ? a : $(s.energy_solar_kwh, r)
  )}` : h}
      ${s.energy_unallocated_kwh > 0 ? f(t("detail_energy_unallocated"), $(s.energy_unallocated_kwh, r)) : h}
      ${f(t("detail_card"), s.card_label ?? s.card_uid)}
      ${f(t("detail_identification"), t(`identification_${s.identification_source}`))}
      ${f(t("detail_address"), ur(s, t))}
      ${f(t("detail_provider"), s.provider)}
      ${f(t("detail_note"), s.note)}
      ${s.open_fields.length > 0 ? f(
    t("detail_open_fields"),
    s.open_fields.map((l) => hr(l, t)).join(", ")
  ) : h}
    </dl>
    ${pr(s, t, e)}
  </div>`;
}
const ae = b`
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
var _r = Object.defineProperty, kt = (s, t, e, r) => {
  for (var i = void 0, a = s.length - 1, n; a >= 0; a--)
    (n = s[a]) && (i = n(t, e, i) || i);
  return i && _r(t, e, i), i;
};
class ut extends v {
  constructor() {
    super(...arguments), this.sessions = [];
  }
  render() {
    const t = this.t;
    return !t || !this.hass ? h : o`<ul>
      ${this.sessions.map((e) => this._renderSession(e, t))}
    </ul>`;
  }
  _renderSession(t, e) {
    const r = this.hass, i = r.locale.language, a = t.soc_start !== null && t.soc_end !== null ? `${k(t.soc_start, i)} → ${k(t.soc_end, i)}` : h;
    return o`<li>
      <details>
        <summary>
          <div class="line">
            <span class=${it({ vehicle: !0, unassigned: t.vehicle_id === null })}
              >${se(t, e)}</span
            >
            <span class="muted"
              >${ot(t.plug_start, i, r.config.time_zone)}</span
            >
          </div>
          <div class="line">
            <span>
              ${$(t.energy_kwh, i, t.energy_is_estimate)} ·
              ${V(t.cost, i, r.config.currency)} ·
              ${S(t.charge_duration_min)}
            </span>
            <span class="muted">${a}</span>
          </div>
          <div class="line">
            <span class="chips">
              <span class="chip">${e(`location_${t.location}`)}</span>
              ${t.status === "complete" ? h : o`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
            </span>
          </div>
        </summary>
        ${ie(t, e, r)}
      </details>
    </li>`;
  }
  static {
    this.styles = [
      M,
      ae,
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
kt([
  g({ attribute: !1 })
], ut.prototype, "hass");
kt([
  g({ attribute: !1 })
], ut.prototype, "t");
kt([
  g({ attribute: !1 })
], ut.prototype, "sessions");
var fr = Object.defineProperty, w = (s, t, e, r) => {
  for (var i = void 0, a = s.length - 1, n; a >= 0; a--)
    (n = s[a]) && (i = n(t, e, i) || i);
  return i && fr(t, e, i), i;
};
const gr = 600 * 1e3, mr = 5, vr = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z", $r = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z", yr = [
  { id: "overview", label: "view_overview" },
  { id: "recent", label: "view_recent" },
  { id: "detail", label: "view_detail" }
], br = ["home", "home_no_wallbox", "external"], wr = ["ac", "dc", "unknown"], xr = ["complete", "followup_open", "flagged"], Sr = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" }
];
function qt(s) {
  return o`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${s} fill="currentColor"></path>
  </svg>`;
}
class y extends v {
  constructor() {
    super(...arguments), this._years = [], this._vehicles = [], this._failed = !1, this._metric = "energy", this._started = !1, this._recentRequested = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => this._refresh(), gr);
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
        ...We(/* @__PURE__ */ new Date(), this.hass.config.time_zone),
        ...e,
        filters: { ...lt, ...e?.filters }
      };
    }
    this._sync();
  }
  _sync() {
    const t = this.hass, e = this._state;
    !t || !e || (this._started || (this._started = !0, this._loadShared(t, !1)), e.view !== "recent" && this._yearKey !== e.year && (this._yearKey = e.year, this._yearSessions = void 0, this._loadYear(t, e.year, !1)), e.view === "recent" && !this._recentRequested && (this._recentRequested = !0, this._loadRecent(t, !1)));
  }
  _refresh() {
    const t = this.hass, e = this._state;
    !t || !e || !this._started || this._failed || (this._loadShared(t, !0), e.view !== "recent" && this._loadYear(t, e.year, !0), e.view === "recent" && this._loadRecent(t, !0));
  }
  _fail(t, e) {
    console.error("ev_charging: loading data failed", t), e || (this._failed = !0);
  }
  _retry() {
    this._failed = !1, this._started = !1, this._yearKey = void 0, this._recentRequested = !1, this.requestUpdate();
  }
  async _loadShared(t, e) {
    try {
      this._t = await Q(t);
    } catch (r) {
      this._t = H({}), this._fail(r, e);
      return;
    }
    try {
      this._vehicles = await Ve(t);
    } catch (r) {
      this._fail(r, e);
    }
  }
  async _loadYear(t, e, r) {
    try {
      const i = await je(t, e);
      this._yearKey === e && (this._yearSessions = i.sessions, this._years = i.years);
    } catch (i) {
      this._yearKey === e && this._fail(i, r);
    }
  }
  async _loadRecent(t, e) {
    try {
      this._recent = await Et(t, { limit: mr });
    } catch (r) {
      this._fail(r, e);
    }
  }
  _setState(t) {
    this._state && (this._state = { ...this._state, ...t }, this.dispatchEvent(new CustomEvent("ev-state-changed", { detail: this._state })));
  }
  _setFilter(t, e) {
    this._state && this._setState({ filters: { ...this._state.filters, [t]: e } });
  }
  _shift(t) {
    this._state && this._setState(Be(this._state.year, this._state.month, t));
  }
  render() {
    const t = this._state;
    if (!t || !this.hass)
      return h;
    if (this._failed)
      return this._renderError(this._t ?? H({}));
    const e = this._t;
    return e ? o`
      <div class="view">
        ${this._renderTabs(e, t)}
        ${t.view === "recent" ? h : this._renderFilters(e, t)}
        ${t.view === "recent" ? h : this._renderPeriod(e, t)}
        ${t.view === "overview" ? this._renderOverview(e, t) : t.view === "detail" ? this._renderDetail(e, t) : this._renderRecent(e)}
        <p class="hint muted">${e("multi_day_hint")} ${e("estimate_hint")}</p>
      </div>
    ` : o`<div class="spinner" role="progressbar"></div>`;
  }
  _renderError(t) {
    return o`<div class="message">
      <span>${t("load_error")}</span>
      <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
    </div>`;
  }
  _renderTabs(t, e) {
    return o`<nav class="tabs">
      ${yr.map(
      (r) => o`<button
          class=${it({ tab: !0, active: r.id === e.view })}
          aria-current=${r.id === e.view ? "page" : "false"}
          @click=${() => this._setState({ view: r.id })}
        >
          ${t(r.label)}
        </button>`
    )}
    </nav>`;
  }
  _renderPeriod(t, e) {
    const r = this.hass, i = r.locale.language, a = J(/* @__PURE__ */ new Date(), r.config.time_zone), n = er(this._years, a.year, e.year);
    return o`<div class="period">
      <button class="icon" aria-label=${t("period_previous")} @click=${() => this._shift(-1)}>
        ${qt(vr)}
      </button>
      <select
        aria-label=${t("period_month")}
        @change=${(l) => this._setState({ month: Number(l.target.value) })}
      >
        ${Array.from({ length: 12 }, (l, c) => c + 1).map(
      (l) => o`<option value=${l} .selected=${l === e.month}>
              ${gt(l, i, "long")}
            </option>`
    )}
      </select>
      <select
        aria-label=${t("period_year")}
        @change=${(l) => this._setState({ year: Number(l.target.value) })}
      >
        ${n.map(
      (l) => o`<option value=${l} .selected=${l === e.year}>${l}</option>`
    )}
      </select>
      <button class="icon" aria-label=${t("period_next")} @click=${() => this._shift(1)}>
        ${qt($r)}
      </button>
    </div>`;
  }
  _renderTiles(t, e) {
    const r = this.hass, i = r.locale.language, a = [
      ["total_energy", $(e.energy_kwh, i, e.energy_is_estimate)],
      ["total_cost", V(e.cost, i, r.config.currency)],
      ["total_duration", S(e.charge_duration_min)],
      ["total_sessions", String(e.count)],
      ["open_followups", String(e.open_followups)]
    ];
    return o`<div class="tiles">
      ${a.map(
      ([n, l]) => o`<div class="tile">
          <span class="tile-label muted">${t(n)}</span>
          <span class="tile-value">${l}</span>
        </div>`
    )}
    </div>`;
  }
  // Sessions of the selected year that pass the filters.
  _filteredYear(t) {
    return Bt(this._yearSessions ?? [], t.filters);
  }
  _renderOverview(t, e) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = this._filteredYear(e), i = this.hass.config.time_zone, a = Ze(r, i);
    return o`
      ${this._renderTiles(t, a[e.month - 1])}
      ${this._renderChart(t, e, a)}
      ${this._renderYearSummary(t, e, Ge(r))}
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
    const e = this.hass, r = e.locale.language;
    switch (this._metric) {
      case "cost":
        return Vt(t.cost, r, e.config.currency);
      case "duration":
        return Wt(t.charge_duration_min);
      default:
        return jt(t.energy_kwh, r, t.energy_is_estimate);
    }
  }
  _renderChart(t, e, r) {
    const i = this.hass.locale.language, a = Math.max(...r.map((n) => this._metricValue(n)), 0);
    return o`<section class="chart">
      <div class="chart-head">
        <h3>${t("chart_title", { year: e.year })}</h3>
        <label class="metric">
          <span class="muted">${t("chart_metric")}</span>
          <select
            @change=${(n) => {
      this._metric = n.target.value;
    }}
          >
            ${Sr.map(
      (n) => o`<option value=${n.id} .selected=${n.id === this._metric}>
                  ${t(n.label)}
                </option>`
    )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${r.map((n) => {
      const l = a > 0 ? this._metricValue(n) / a * 100 : 0, c = gt(n.month, i, "long"), d = n.count === 0 ? m : this._formatMetric(n);
      return o`<button
            class=${it({ bar: !0, selected: n.month === e.month })}
            title=${`${c}: ${d}`}
            aria-label=${`${c}: ${d}`}
            aria-pressed=${n.month === e.month ? "true" : "false"}
            @click=${() => this._setState({ month: n.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${l}%`}></span></span>
            <span class="bar-label muted">${gt(n.month, i, "short")}</span>
            <span class="bar-value">${d}</span>
          </button>`;
    })}
      </div>
    </section>`;
  }
  _renderYearSummary(t, e, r) {
    const i = this.hass, a = i.locale.language, n = [
      ["scope_total", r.all],
      ["scope_internal", r.internal],
      ["scope_external", r.external]
    ], l = [
      ["total_energy", (c) => jt(c.energy_kwh, a, c.energy_is_estimate)],
      ["total_cost", (c) => Vt(c.cost, a, i.config.currency)],
      ["total_duration", (c) => Wt(c.charge_duration_min)],
      ["total_sessions", (c) => String(c.count)]
    ];
    return o`<section class="year-summary">
      <h3>${t("year_summary_title", { year: e.year })}</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            ${n.map(([c]) => o`<th class="num">${t(c)}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${l.map(
      ([c, d]) => o`<tr>
              <th>${t(c)}</th>
              ${n.map(([, _]) => o`<td class="num">${d(_)}</td>`)}
            </tr>`
    )}
        </tbody>
      </table>
    </section>`;
  }
  _renderFilters(t, e) {
    const r = this._yearSessions ?? [], i = e.filters, a = [
      ...Qe(this._vehicles, r),
      { value: te, label: t("unassigned") }
    ], n = [
      { value: Ct, label: t("filter_no_card") },
      ...tr(
        this._vehicles.flatMap((l) => l.cards),
        r,
        i.card
      )
    ];
    return o`<div class="filters">
      ${this._renderFilter(t("filter_vehicle"), "vehicle", a, t)}
      ${this._renderFilter(
      t("filter_location"),
      "location",
      br.map((l) => ({ value: l, label: t(`location_${l}`) })),
      t
    )}
      ${this._renderFilter(
      t("filter_charge_type"),
      "chargeType",
      wr.map((l) => ({ value: l, label: t(`charge_type_${l}`) })),
      t
    )}
      ${this._renderFilter(t("filter_card"), "card", n, t)}
      ${this._renderFilter(
      t("filter_status"),
      "status",
      xr.map((l) => ({ value: l, label: t(`status_${l}`) })),
      t
    )}
      ${Xe(i) ? o`<button
            class="text reset"
            @click=${() => this._setState({ filters: { ...lt } })}
          >
            ${t("filter_reset")}
          </button>` : h}
    </div>`;
  }
  _renderDetail(t, e) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const r = this.hass.config.time_zone, i = re(this._yearSessions, e.month, r), a = Bt(i, e.filters);
    return o`
      ${this._renderTiles(t, F(a))}
      <p class="count muted">
        ${t("filter_count", { shown: a.length, total: i.length })}
      </p>
      ${a.length === 0 ? o`<div class="message">
            ${i.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>` : this._renderTable(a, t)}
    `;
  }
  _renderRecent(t) {
    const e = this._recent;
    return e ? e.length === 0 ? o`<div class="message">${t("no_sessions")}</div>` : o`<ev-charging-session-list
          .hass=${this.hass}
          .t=${t}
          .sessions=${e}
        ></ev-charging-session-list>` : o`<div class="spinner" role="progressbar"></div>`;
  }
  _renderFilter(t, e, r, i) {
    const a = this._state.filters[e];
    return o`<label class="filter">
      <span class="muted">${t}</span>
      <select
        @change=${(n) => this._setFilter(e, n.target.value)}
      >
        <option value="" .selected=${a === ""}>${i("filter_all")}</option>
        ${r.map(
      (n) => o`<option value=${n.value} .selected=${n.value === a}>
              ${n.label}
            </option>`
    )}
      </select>
    </label>`;
  }
  _renderTable(t, e) {
    return o`<div class="table" role="table">
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
      ${t.map((r) => this._renderSession(r, e))}
    </div>`;
  }
  _renderSession(t, e) {
    const r = this.hass, i = r.locale.language, a = r.config.time_zone, n = t.vehicle_id === null;
    return o`<details class="session">
      <summary>
        <span class="c-date">${ot(t.plug_start, i, a)}</span>
        <span class=${it({ "c-vehicle": !0, vehicle: !0, unassigned: n })}
          >${se(t, e)}</span
        >
        <span class="c-location"><span class="chip">${e(`location_${t.location}`)}</span></span>
        <span class="c-type"><span class="chip">${e(`charge_type_${t.charge_type}`)}</span></span>
        <span class="c-energy num"
          >${$(t.energy_kwh, i, t.energy_is_estimate)}</span
        >
        <span class="c-cost num">${V(t.cost, i, r.config.currency)}</span>
        <span class="c-duration num">${S(t.charge_duration_min)}</span>
        <span class="c-status">
          ${t.status === "complete" ? h : o`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
          ${t.location_conflict ? o`<span class="chip alert">${e("flag_location_conflict")}</span>` : h}
          ${t.identification_conflict ? o`<span class="chip alert">${e("flag_identification_conflict")}</span>` : h}
          ${t.charge_error ? o`<span class="chip alert">${e("flag_charge_error")}</span>` : h}
          ${t.energy_unallocated_kwh > 0 ? o`<span class="chip warn">${e("flag_unallocated_energy")}</span>` : h}
        </span>
      </summary>
      ${ie(t, e, r)}
    </details>`;
  }
  static {
    this.styles = [
      M,
      ae,
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
var Ar = Object.defineProperty, pt = (s, t, e, r) => {
  for (var i = void 0, a = s.length - 1, n; a >= 0; a--)
    (n = s[a]) && (i = n(t, e, i) || i);
  return i && Ar(t, e, i), i;
};
const Er = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
class et extends v {
  constructor() {
    super(...arguments), this.narrow = !1;
  }
  willUpdate() {
    this._initialState === void 0 && (this._initialState = Ke(this.route?.path ?? "", window.location.search));
  }
  _toggleMenu() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: !0, composed: !0 }));
  }
  _onStateChanged(t) {
    const e = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${e}${qe(t.detail)}`);
  }
  render() {
    return o`
      <header>
        ${this.narrow ? o`<button class="menu" @click=${() => this._toggleMenu()}>
              <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d=${Er} fill="currentColor"></path>
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
      M,
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
pt([
  g({ attribute: !1 })
], et.prototype, "hass");
pt([
  g({ type: Boolean })
], et.prototype, "narrow");
pt([
  g({ attribute: !1 })
], et.prototype, "route");
pt([
  g({ attribute: !1 })
], et.prototype, "panel");
var Cr = Object.defineProperty, ne = (s, t, e, r) => {
  for (var i = void 0, a = s.length - 1, n; a >= 0; a--)
    (n = s[a]) && (i = n(t, e, i) || i);
  return i && Cr(t, e, i), i;
};
class Pt extends v {
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
    return o`<div class="card">
      <ev-charging-panel-view .hass=${this.hass}></ev-charging-panel-view>
    </div>`;
  }
  static {
    this.styles = [
      M,
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
ne([
  g({ attribute: !1 })
], Pt.prototype, "hass");
ne([
  g({ type: Boolean, reflect: !0, attribute: "is-panel" })
], Pt.prototype, "isPanel");
var kr = Object.defineProperty, U = (s, t, e, r) => {
  for (var i = void 0, a = s.length - 1, n; a >= 0; a--)
    (n = s[a]) && (i = n(t, e, i) || i);
  return i && kr(t, e, i), i;
};
const L = 3, Mt = 20, Pr = 600 * 1e3;
function oe(s) {
  return Number.isInteger(s) && s >= 1 && s <= Mt;
}
class B extends v {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1;
  }
  setConfig(t) {
    if (!oe(t.count ?? L))
      throw new Error(`count must be a whole number from 1 to ${Mt}`);
    this._config = t, this._started && this.hass && this._load(this.hass, !0);
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
    }, Pr);
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
      this._t = await Q(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = H({}), this._failed = !0;
      return;
    }
    await this._load(t, !1);
  }
  async _load(t, e) {
    try {
      this._sessions = await Et(t, { limit: this._config.count ?? L }), this._failed = !1;
    } catch (r) {
      console.error("ev_charging: loading sessions failed", r), e || (this._failed = !0);
    }
  }
  _retry() {
    this.hass && (this._failed = !1, this._started = !1, this.requestUpdate());
  }
  render() {
    const t = this._t;
    return !t || !this.hass ? o`<div class="spinner" role="progressbar"></div>` : this._failed ? o`<div class="message">
        <span>${t("load_error")}</span>
        <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
      </div>` : o`
      <h2>${this._config.title ?? t("recent_title")}</h2>
      ${this._sessions === void 0 ? o`<div class="spinner" role="progressbar"></div>` : this._sessions.length === 0 ? o`<div class="message">${t("no_sessions")}</div>` : o`<ev-charging-session-list
              .hass=${this.hass}
              .t=${t}
              .sessions=${this._sessions}
            ></ev-charging-session-list>`}
    `;
  }
  static {
    this.styles = [
      M,
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
class _t extends v {
  constructor() {
    super(...arguments), this._config = {}, this._started = !1;
  }
  setConfig(t) {
    this._config = t;
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, Q(this.hass).then(
      (e) => this._t = e,
      () => this._t = H({})
    ));
  }
  _changed(t) {
    const e = Number(t.target.value);
    if (!oe(e)) {
      t.target.value = String(this._config.count ?? L);
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
    return t ? o`<label>
      <span>${t("card_count")}</span>
      <input
        type="number"
        min="1"
        max=${Mt}
        step="1"
        .value=${String(this._config.count ?? L)}
        @change=${(e) => this._changed(e)}
      />
    </label>` : o``;
  }
  static {
    this.styles = [
      M,
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
], _t.prototype, "hass");
U([
  p()
], _t.prototype, "_config");
U([
  p()
], _t.prototype, "_t");
function R(s, t) {
  customElements.get(s) || customElements.define(s, t);
}
R("ev-charging-panel-view", y);
R("ev-charging-session-list", ut);
R("ev-charging-panel", et);
R("ev-charging-panel-card", Pt);
R("ev-charging-recent-card", B);
R("ev-charging-recent-card-editor", _t);
R("ev-charging-live-card", A);
R("ev-charging-month-card", W);
const ct = window;
ct.customCards = ct.customCards ?? [];
for (const s of [
  "ev-charging-panel-card",
  "ev-charging-recent-card",
  "ev-charging-live-card",
  "ev-charging-month-card"
])
  ct.customCards.some((t) => t.type === s) || ct.customCards.push({ type: s, name: s });
