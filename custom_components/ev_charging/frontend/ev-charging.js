/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const it = globalThis, wt = it.ShadowRoot && (it.ShadyCSS === void 0 || it.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, xt = Symbol(), Nt = /* @__PURE__ */ new WeakMap();
let Jt = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== xt) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (wt && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = Nt.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && Nt.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const ue = (r) => new Jt(typeof r == "string" ? r : r + "", void 0, xt), S = (r, ...t) => {
  const e = r.length === 1 ? r[0] : t.reduce((s, i, n) => s + ((a) => {
    if (a._$cssResult$ === !0) return a.cssText;
    if (typeof a == "number") return a;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + a + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + r[n + 1], r[0]);
  return new Jt(e, r, xt);
}, pe = (r, t) => {
  if (wt) r.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), i = it.litNonce;
    i !== void 0 && s.setAttribute("nonce", i), s.textContent = e.cssText, r.appendChild(s);
  }
}, zt = wt ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return ue(e);
})(r) : r;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: _e, defineProperty: fe, getOwnPropertyDescriptor: ge, getOwnPropertyNames: me, getOwnPropertySymbols: ve, getPrototypeOf: $e } = Object, ht = globalThis, Dt = ht.trustedTypes, ye = Dt ? Dt.emptyScript : "", be = ht.reactiveElementPolyfillSupport, Y = (r, t) => r, at = { toAttribute(r, t) {
  switch (t) {
    case Boolean:
      r = r ? ye : null;
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
} }, St = (r, t) => !_e(r, t), Ht = { attribute: !0, type: String, converter: at, reflect: !1, useDefault: !1, hasChanged: St };
Symbol.metadata ??= Symbol("metadata"), ht.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let I = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = Ht) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), i = this.getPropertyDescriptor(t, s, e);
      i !== void 0 && fe(this.prototype, t, i);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: i, set: n } = ge(this.prototype, t) ?? { get() {
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
    return this.elementProperties.get(t) ?? Ht;
  }
  static _$Ei() {
    if (this.hasOwnProperty(Y("elementProperties"))) return;
    const t = $e(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(Y("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(Y("properties"))) {
      const e = this.properties, s = [...me(e), ...ve(e)];
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
      for (const i of s) e.unshift(zt(i));
    } else t !== void 0 && e.push(zt(t));
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
    return pe(t, this.constructor.elementStyles), t;
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
      const n = (s.converter?.toAttribute !== void 0 ? s.converter : at).toAttribute(e, s.type);
      this._$Em = t, n == null ? this.removeAttribute(i) : this.setAttribute(i, n), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, i = s._$Eh.get(t);
    if (i !== void 0 && this._$Em !== i) {
      const n = s.getPropertyOptions(i), a = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : at;
      this._$Em = i;
      const l = a.fromAttribute(e, n.type);
      this[i] = l ?? this._$Ej?.get(i) ?? l, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, i = !1, n) {
    if (t !== void 0) {
      const a = this.constructor;
      if (i === !1 && (n = this[t]), s ??= a.getPropertyOptions(t), !((s.hasChanged ?? St)(n, e) || s.useDefault && s.reflect && n === this._$Ej?.get(t) && !this.hasAttribute(a._$Eu(t, s)))) return;
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
I.elementStyles = [], I.shadowRootOptions = { mode: "open" }, I[Y("elementProperties")] = /* @__PURE__ */ new Map(), I[Y("finalized")] = /* @__PURE__ */ new Map(), be?.({ ReactiveElement: I }), (ht.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const At = globalThis, It = (r) => r, ot = At.trustedTypes, Lt = ot ? ot.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, Xt = "$lit$", E = `lit$${Math.random().toFixed(9).slice(2)}$`, Qt = "?" + E, we = `<${Qt}>`, z = document, Z = () => z.createComment(""), K = (r) => r === null || typeof r != "object" && typeof r != "function", Ct = Array.isArray, xe = (r) => Ct(r) || typeof r?.[Symbol.iterator] == "function", mt = `[ 	
\f\r]`, q = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Ft = /-->/g, jt = />/g, O = RegExp(`>|${mt}(?:([^\\s"'>=/]+)(${mt}*=${mt}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Wt = /'/g, Vt = /"/g, te = /^(?:script|style|textarea|title)$/i, Se = (r) => (t, ...e) => ({ _$litType$: r, strings: t, values: e }), o = Se(1), D = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), Bt = /* @__PURE__ */ new WeakMap(), N = z.createTreeWalker(z, 129);
function ee(r, t) {
  if (!Ct(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Lt !== void 0 ? Lt.createHTML(t) : t;
}
const Ae = (r, t) => {
  const e = r.length - 1, s = [];
  let i, n = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", a = q;
  for (let l = 0; l < e; l++) {
    const c = r[l];
    let u, p, h = -1, y = 0;
    for (; y < c.length && (a.lastIndex = y, p = a.exec(c), p !== null); ) y = a.lastIndex, a === q ? p[1] === "!--" ? a = Ft : p[1] !== void 0 ? a = jt : p[2] !== void 0 ? (te.test(p[2]) && (i = RegExp("</" + p[2], "g")), a = O) : p[3] !== void 0 && (a = O) : a === O ? p[0] === ">" ? (a = i ?? q, h = -1) : p[1] === void 0 ? h = -2 : (h = a.lastIndex - p[2].length, u = p[1], a = p[3] === void 0 ? O : p[3] === '"' ? Vt : Wt) : a === Vt || a === Wt ? a = O : a === Ft || a === jt ? a = q : (a = O, i = void 0);
    const w = a === O && r[l + 1].startsWith("/>") ? " " : "";
    n += a === q ? c + we : h >= 0 ? (s.push(u), c.slice(0, h) + Xt + c.slice(h) + E + w) : c + E + (h === -2 ? l : w);
  }
  return [ee(r, n + (r[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class G {
  constructor({ strings: t, _$litType$: e }, s) {
    let i;
    this.parts = [];
    let n = 0, a = 0;
    const l = t.length - 1, c = this.parts, [u, p] = Ae(t, e);
    if (this.el = G.createElement(u, s), N.currentNode = this.el.content, e === 2 || e === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (i = N.nextNode()) !== null && c.length < l; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const h of i.getAttributeNames()) if (h.endsWith(Xt)) {
          const y = p[a++], w = i.getAttribute(h).split(E), st = /([.?@])?(.*)/.exec(y);
          c.push({ type: 1, index: n, name: st[2], strings: w, ctor: st[1] === "." ? Ee : st[1] === "?" ? ke : st[1] === "@" ? Te : ut }), i.removeAttribute(h);
        } else h.startsWith(E) && (c.push({ type: 6, index: n }), i.removeAttribute(h));
        if (te.test(i.tagName)) {
          const h = i.textContent.split(E), y = h.length - 1;
          if (y > 0) {
            i.textContent = ot ? ot.emptyScript : "";
            for (let w = 0; w < y; w++) i.append(h[w], Z()), N.nextNode(), c.push({ type: 2, index: ++n });
            i.append(h[y], Z());
          }
        }
      } else if (i.nodeType === 8) if (i.data === Qt) c.push({ type: 2, index: n });
      else {
        let h = -1;
        for (; (h = i.data.indexOf(E, h + 1)) !== -1; ) c.push({ type: 7, index: n }), h += E.length - 1;
      }
      n++;
    }
  }
  static createElement(t, e) {
    const s = z.createElement("template");
    return s.innerHTML = t, s;
  }
}
function j(r, t, e = r, s) {
  if (t === D) return t;
  let i = s !== void 0 ? e._$Co?.[s] : e._$Cl;
  const n = K(t) ? void 0 : t._$litDirective$;
  return i?.constructor !== n && (i?._$AO?.(!1), n === void 0 ? i = void 0 : (i = new n(r), i._$AT(r, e, s)), s !== void 0 ? (e._$Co ??= [])[s] = i : e._$Cl = i), i !== void 0 && (t = j(r, i._$AS(r, t.values), i, s)), t;
}
class Ce {
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
    const { el: { content: e }, parts: s } = this._$AD, i = (t?.creationScope ?? z).importNode(e, !0);
    N.currentNode = i;
    let n = N.nextNode(), a = 0, l = 0, c = s[0];
    for (; c !== void 0; ) {
      if (a === c.index) {
        let u;
        c.type === 2 ? u = new Q(n, n.nextSibling, this, t) : c.type === 1 ? u = new c.ctor(n, c.name, c.strings, this, t) : c.type === 6 && (u = new Ue(n, this, t)), this._$AV.push(u), c = s[++l];
      }
      a !== c?.index && (n = N.nextNode(), a++);
    }
    return N.currentNode = z, i;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class Q {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, e, s, i) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = s, this.options = i, this._$Cv = i?.isConnected ?? !0;
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
    t = j(this, t, e), K(t) ? t === d || t == null || t === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : t !== this._$AH && t !== D && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : xe(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== d && K(this._$AH) ? this._$AA.nextSibling.data = t : this.T(z.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: s } = t, i = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = G.createElement(ee(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === i) this._$AH.p(e);
    else {
      const n = new Ce(i, this), a = n.u(this.options);
      n.p(e), this.T(a), this._$AH = n;
    }
  }
  _$AC(t) {
    let e = Bt.get(t.strings);
    return e === void 0 && Bt.set(t.strings, e = new G(t)), e;
  }
  k(t) {
    Ct(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, i = 0;
    for (const n of t) i === e.length ? e.push(s = new Q(this.O(Z()), this.O(Z()), this, this.options)) : s = e[i], s._$AI(n), i++;
    i < e.length && (this._$AR(s && s._$AB.nextSibling, i), e.length = i);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const s = It(t).nextSibling;
      It(t).remove(), t = s;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class ut {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, s, i, n) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = t, this.name = e, this._$AM = i, this.options = n, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = d;
  }
  _$AI(t, e = this, s, i) {
    const n = this.strings;
    let a = !1;
    if (n === void 0) t = j(this, t, e, 0), a = !K(t) || t !== this._$AH && t !== D, a && (this._$AH = t);
    else {
      const l = t;
      let c, u;
      for (t = n[0], c = 0; c < n.length - 1; c++) u = j(this, l[s + c], e, c), u === D && (u = this._$AH[c]), a ||= !K(u) || u !== this._$AH[c], u === d ? t = d : t !== d && (t += (u ?? "") + n[c + 1]), this._$AH[c] = u;
    }
    a && !i && this.j(t);
  }
  j(t) {
    t === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Ee extends ut {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === d ? void 0 : t;
  }
}
class ke extends ut {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== d);
  }
}
class Te extends ut {
  constructor(t, e, s, i, n) {
    super(t, e, s, i, n), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = j(this, t, e, 0) ?? d) === D) return;
    const s = this._$AH, i = t === d && s !== d || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, n = t !== d && (s === d || i);
    i && this.element.removeEventListener(this.name, this, s), n && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Ue {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    j(this, t);
  }
}
const Pe = At.litHtmlPolyfillSupport;
Pe?.(G, Q), (At.litHtmlVersions ??= []).push("3.3.3");
const Me = (r, t, e) => {
  const s = e?.renderBefore ?? t;
  let i = s._$litPart$;
  if (i === void 0) {
    const n = e?.renderBefore ?? null;
    s._$litPart$ = i = new Q(t.insertBefore(Z(), n), n, void 0, e ?? {});
  }
  return i._$AI(r), i;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Et = globalThis;
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Me(e, this.renderRoot, this.renderOptions);
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
v._$litElement$ = !0, v.finalized = !0, Et.litElementHydrateSupport?.({ LitElement: v });
const Re = Et.litElementPolyfillSupport;
Re?.({ LitElement: v });
(Et.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Oe = { attribute: !0, type: String, converter: at, reflect: !1, hasChanged: St }, Ne = (r = Oe, t, e) => {
  const { kind: s, metadata: i } = e;
  let n = globalThis.litPropertyMetadata.get(i);
  if (n === void 0 && globalThis.litPropertyMetadata.set(i, n = /* @__PURE__ */ new Map()), s === "setter" && ((r = Object.create(r)).wrapped = !0), n.set(e.name, r), s === "accessor") {
    const { name: a } = e;
    return { set(l) {
      const c = t.get.call(this);
      t.set.call(this, l), this.requestUpdate(a, c, r, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(a, void 0, r, l), l;
    } };
  }
  if (s === "setter") {
    const { name: a } = e;
    return function(l) {
      const c = this[a];
      t.call(this, l), this.requestUpdate(a, c, r, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function g(r) {
  return (t, e) => typeof e == "object" ? Ne(r, t, e) : ((s, i, n) => {
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
const m = "–";
function T(r, t, e) {
  return new Intl.NumberFormat(t, {
    minimumFractionDigits: e,
    maximumFractionDigits: e
  }).format(r);
}
function $(r, t, e = !1) {
  return r === null ? m : `${e ? "~" : ""}${T(r, t, 3)} kWh`;
}
function qt(r, t, e = !1) {
  return r === null ? m : `${e ? "~" : ""}${T(r, t, 0)} kWh`;
}
function Yt(r, t, e) {
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
    return `${T(r, t, 0)} ${e}`;
  }
}
function Zt(r) {
  if (r === null)
    return m;
  const t = Math.round(r);
  return t < 60 ? `${t} min` : `${Math.round(t / 60)} h`;
}
function W(r, t, e) {
  if (r === null)
    return m;
  try {
    return new Intl.NumberFormat(t, { style: "currency", currency: e }).format(r);
  } catch {
    return `${T(r, t, 2)} ${e}`;
  }
}
function ze(r, t, e) {
  if (r === null)
    return m;
  try {
    return `${new Intl.NumberFormat(t, {
      style: "currency",
      currency: e,
      minimumFractionDigits: 3,
      maximumFractionDigits: 4
    }).format(r)} / kWh`;
  } catch {
    return `${T(r, t, 4)} ${e} / kWh`;
  }
}
function x(r) {
  if (r === null)
    return m;
  const t = Math.round(r);
  if (t < 60)
    return `${t} min`;
  const e = Math.floor(t / 60), s = String(t % 60).padStart(2, "0");
  return `${e}:${s} h`;
}
function k(r, t) {
  return r === null ? m : `${T(r, t, 0)} %`;
}
function kt(r, t) {
  return r === null ? m : `${T(r, t, 0)} km`;
}
function re(r, t) {
  return r === null ? m : `${T(r, t, 1)} kW`;
}
function J(r, t, e) {
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
function lt(r, t, e) {
  return r === null ? m : new Intl.DateTimeFormat(t, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: e
  }).format(new Date(r));
}
function vt(r, t, e) {
  return new Intl.DateTimeFormat(t, { month: e, timeZone: "UTC" }).format(
    new Date(Date.UTC(2026, r - 1, 1))
  );
}
function pt(r, t) {
  const e = () => t();
  return r.connection.addEventListener("ready", e), () => r.connection.removeEventListener("ready", e);
}
const De = "component.ev_charging.selector.panel.options.";
function H(r) {
  return (t, e) => {
    const s = r[De + t];
    return s === void 0 ? t : e ? s.replace(
      /\{(\w+)\}/g,
      (i, n) => n in e ? String(e[n]) : i
    ) : s;
  };
}
const $t = /* @__PURE__ */ new Map();
function tt(r) {
  const t = r.language;
  let e = $t.get(t);
  return e === void 0 && (e = r.callWS({
    type: "frontend/get_translations",
    language: t,
    category: "selector",
    integration: ["ev_charging"]
  }).then((s) => H(s.resources)), e.catch(() => $t.delete(t)), $t.set(t, e)), e;
}
const Tt = 6e4;
function He(r, t, e) {
  if (r.net_duration_min === null)
    return null;
  const s = r.state === "charging";
  return r.net_duration_min + (s ? (e - t) / Tt : 0);
}
function Ie(r, t) {
  return r.session_start === null ? null : Math.max((t - new Date(r.session_start).getTime()) / Tt, 0);
}
function Le(r, t) {
  if (r.charge_end === null)
    return null;
  const e = (new Date(r.charge_end).getTime() - t) / Tt;
  return e > 0 ? e : null;
}
function Fe(r) {
  const t = r.energy_grid_kwh, e = r.energy_solar_kwh;
  return t === null || e === null || t + e <= 0 ? null : e / (t + e) * 100;
}
function je(r) {
  let t = 0, e = 0;
  for (const s of r)
    s.energy_grid_kwh !== null && s.energy_solar_kwh !== null && (t += s.energy_grid_kwh, e += s.energy_solar_kwh);
  return t + e > 0 ? e / (t + e) * 100 : null;
}
function bt(r, t) {
  const e = (s) => new Intl.DateTimeFormat("en-CA", {
    timeZone: t.timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(s);
  return e(new Date(r).getTime()) === e(t.now) ? lt(r, t.locale, t.timeZone) : J(r, t.locale, t.timeZone);
}
function We(r) {
  return r("live_title");
}
function Ve(r, t) {
  if (r.kind === "external")
    return t("live_block_external");
  const e = r.wallbox?.name.trim();
  return e || t("live_title");
}
function Be(r, t, e) {
  if (r.soc_start === null && r.soc === null)
    return null;
  const s = r.soc_start !== null && r.soc !== null ? `${k(r.soc_start, e)} → ${k(r.soc, e)}` : k(r.soc ?? r.soc_start, e);
  return r.soc_target === null ? s : `${s} (${t("live_soc_target", { target: r.soc_target })})`;
}
function qe(r, t, e) {
  const s = [
    r.odometer_km === null ? null : kt(r.odometer_km, e),
    Be(r, t, e)
  ].filter((i) => i !== null);
  return s.length === 0 ? null : s.join(" · ");
}
function Ye(r, t, e) {
  return r.charge_end !== null ? lt(r.charge_end, e.locale, e.timeZone) : r.charge_end_missing === "no_power" ? t("live_charge_end_no_power") : null;
}
const Ze = {
  ac: "charge_type_ac",
  dc: "charge_type_dc"
};
function Ke(r, t) {
  return r.charge_type === null ? null : t(Ze[r.charge_type]);
}
function Ge(r, t) {
  switch (r.plug?.state) {
    case "not_connected":
      return t("live_idle_not_connected");
    case "unavailable":
      return t("live_idle_plug_unavailable");
    default:
      return t("live_idle");
  }
}
function Je(r, t, e) {
  const s = r.state_since === null ? null : bt(r.state_since, e);
  switch (r.state) {
    case "candidate":
      return t("live_status_candidate");
    case "charging":
      return s === null ? t("live_state_charging") : t("live_status_charging", { time: s });
    case "paused":
      return r.waiting_for_power ? t("live_status_waiting_for_power") : s === null ? t("live_status_paused") : t("live_status_paused_since", { time: s });
    case "error":
      return s === null ? t("live_state_error") : t("live_status_error", { time: s });
    case "awaiting_final":
      return t("live_status_awaiting_final");
    default:
      return t("live_idle");
  }
}
function Xe(r, t) {
  return r.phase_count === 0 ? null : r.phase_count === 1 ? t("live_phase_one") : t("live_phase_other", { count: r.phase_count });
}
function Qe(r, t, e) {
  const s = r.plug;
  if (s === null)
    return "";
  switch (s.state) {
    case "connected":
      return t("live_plug_connected");
    case "not_connected":
      return t("live_plug_not_connected");
    default:
      return s.unavailable_since !== null && s.timeout_at !== null ? t("live_plug_unavailable_timeout", {
        since: bt(s.unavailable_since, e),
        timeout: bt(s.timeout_at, e)
      }) : t("live_plug_unavailable");
  }
}
function tr(r, t) {
  return r.vehicle_guest ? t("live_vehicle_guest") : r.vehicle !== null ? r.vehicle.name : r.identification_decided ? t("unassigned") : t("live_assign_detecting");
}
const er = {
  rfid: "identification_rfid",
  emaid: "identification_emaid",
  vehicle_api: "identification_vehicle_api",
  manual: "identification_manual"
};
function se(r, t) {
  const e = r.identification_source;
  if (!r.identification_decided || r.vehicle === null || e === null)
    return null;
  const s = er[e];
  return s === void 0 ? null : t("live_assign_via", { source: t(s) });
}
function rr(r, t) {
  const e = r.identification_read;
  if (e === null || e.state === "read" && se(r, t) !== null)
    return null;
  switch (e.state) {
    case "reading":
      return t("live_read_reading", {
        sequence: e.sequence,
        attempt: e.attempt,
        max: e.max_attempts
      });
    case "waiting":
      return t("live_read_waiting");
    case "read":
      return t("live_read_done");
    default:
      return t("live_read_unreadable");
  }
}
function sr(r, t) {
  if (r.counter === null || r.counter.authoritative === null)
    return null;
  const { authoritative: e, switched: s } = r.counter, i = t(e === "total" ? "live_counter_total" : "live_counter_session");
  return s ? t("live_counter_switched", { counter: i }) : t("live_counter", { counter: i });
}
function ir(r, t, e) {
  const s = r.energy_unallocated_kwh;
  return s === null || s <= 0 ? null : t("live_unallocated", { energy: $(s, e) });
}
function nr(r, t) {
  return r.sources === null ? { split: null, cost: null } : {
    split: r.energy_grid_kwh === null && !r.sources.grid_balance ? t("live_missing_split") : null,
    cost: r.cost === null && !r.sources.grid_price ? t("live_missing_cost") : null
  };
}
const U = S`
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
var ar = Object.defineProperty, P = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && ar(t, e, i), i;
};
const or = "ev_charging/live/subscribe", lr = 1e3;
class C extends v {
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
      this._live?.some((t) => t.active) && (this._now = Date.now());
    }, lr), this.hass && this._started && this._subscribe(this.hass), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._started);
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass), this._watchConnection(this.hass));
  }
  // A load that raced a reconnect leaves the card failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(t) {
    this._connectionUnsub || (this._connectionUnsub = pt(t, () => {
      (this._failed || this._noWallbox) && this.hass && this._subscribe(this.hass);
    }));
  }
  async _start(t) {
    try {
      this._t = await tt(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = H({});
    }
    await this._subscribe(t);
  }
  async _subscribe(t) {
    this._release(), this._failed = !1, this._noWallbox = !1;
    const e = t.connection.subscribeMessage(
      (s) => {
        this._live = s, this._received = Date.now(), this._now = this._received;
      },
      { type: or }
    );
    this._unsubscribe = e;
    try {
      await e;
    } catch (s) {
      this._unsubscribe = void 0, s.code === "not_found" ? this._noWallbox = !0 : (console.error("ev_charging: subscribing to the live values failed", s), this._failed = !0);
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
  // The vehicle with its odometer and state of charge in a muted line below.
  _vehicle(t, e, s) {
    const i = !t.vehicle_guest && t.vehicle === null, n = qe(t, e, s);
    return o`<div class="vehicle ${i ? "unassigned" : ""}">${tr(t, e)}</div>
      ${n === null ? d : o`<div class="vehicle-details">${n}</div>`}`;
  }
  _format(t) {
    return {
      locale: t.locale?.language ?? t.language,
      timeZone: t.config.time_zone,
      now: this._now
    };
  }
  // The state of the session and where it came from: what it is doing, the plug,
  // the assignment and the reading of the identification. The plug only applies
  // to the wallbox block; an external block never carries one.
  _status(t, e, s) {
    const i = Xe(t, e), n = [
      se(t, e),
      t.kind === "wallbox" ? Qe(t, e, s) : null,
      rr(t, e)
    ].filter((a) => a !== null && a !== "");
    return o`<div class="status">
      <div class="state">
        ${Je(t, e, s)}${i === null ? d : o` · ${i}`}
      </div>
      ${n.map((a) => o`<div class="line">${a}</div>`)}
    </div>`;
  }
  // The data situation: which counter carries the energy, and energy that could
  // not be assigned. Wallbox blocks only; an external block has neither.
  _situation(t, e, s) {
    const i = [sr(t, e), ir(t, e, s)].filter(
      (n) => n !== null
    );
    return i.length === 0 ? d : o`<div class="situation">${i.map((n) => o`<div>${n}</div>`)}</div>`;
  }
  _flags(t, e) {
    const s = [];
    return t.charge_error && s.push(o`<span class="chip alert">${e("flag_charge_error")}</span>`), t.location_conflict && s.push(o`<span class="chip warn">${e("flag_location_conflict")}</span>`), t.identification_conflict && s.push(o`<span class="chip warn">${e("flag_identification_conflict")}</span>`), t.flagged && s.push(o`<span class="chip warn">${e("status_flagged")}</span>`), s.length === 0 ? d : o`<div class="flags">${s}</div>`;
  }
  // Wallbox blocks show the grid/solar split, the cost and the price; external
  // blocks never have those and show the address, charge type and range instead.
  _details(t, e, s) {
    const i = s.locale?.language ?? s.language, n = t.currency || s.config.currency, a = Ye(t, e, {
      locale: i,
      timeZone: s.config.time_zone,
      now: this._now
    }), l = a === null ? d : this._row(e("live_charge_end"), a);
    let c = d, u = d;
    if (t.kind === "wallbox") {
      const p = Fe(t), h = nr(t, e), y = t.energy_grid_kwh === null || t.energy_solar_kwh === null ? h.split === null ? d : this._row(`${e("detail_energy_grid")} / ${e("detail_energy_solar")}`, h.split) : this._row(
        `${e("detail_energy_grid")} / ${e("detail_energy_solar")}`,
        `${$(t.energy_grid_kwh, i)} / ${$(
          t.energy_solar_kwh,
          i
        )}${p === null ? "" : ` (${e("live_solar_share", { percent: Math.round(p) })})`}`
      ), w = t.effective_price === null ? d : this._row(e("live_price"), ze(t.effective_price, i, n));
      c = o`${y}
        ${this._row(e("live_cost"), h.cost ?? W(t.cost, i, n))}
        ${w}`;
    } else {
      const p = Ke(t, e), h = Le(t, this._now);
      c = o`
        ${t.address === null ? d : this._row(e("live_address"), t.address)}
        ${p === null ? d : this._row(e("live_charge_type"), p)}
        ${t.range_km === null ? d : this._row(e("live_range"), kt(t.range_km, i))}
      `, u = h === null ? d : this._row(e("live_remaining_time"), x(h));
    }
    return o`<dl>
      ${this._row(e("live_power"), re(t.charge_power_kw, i))}
      ${this._row(e("live_energy"), $(t.energy_kwh, i, t.energy_is_estimate))}
      ${c}
      ${this._row(
      e("live_charge_time"),
      x(He(t, this._received, this._now))
    )}
      ${this._row(e("live_plug_time"), x(Ie(t, this._now)))}
      ${l} ${u}
    </dl>`;
  }
  // One block: the wallbox's own session, or one vehicle's own external session.
  _block(t, e, s) {
    const i = Ve(t, e);
    if (!t.active)
      return o`<div class="block">
        <h3><span>${i}</span></h3>
        <div class="message">${Ge(t, e)}</div>
      </div>`;
    const n = `live_state_${t.state}`;
    return o`<div class="block">
      <h3>
        <span>${i}</span>
        <span class="chip ${t.state === "error" ? "alert" : ""}">${e(n)}</span>
      </h3>
      ${this._vehicle(t, e, s.locale?.language ?? s.language)}
      ${this._status(t, e, this._format(s))}
      ${this._details(t, e, s)}
      ${this._situation(t, e, s.locale?.language ?? s.language)}
      ${this._flags(t, e)}
    </div>`;
  }
  render() {
    const t = this._t, e = this.hass;
    if (!t || !e)
      return o`<div class="spinner" role="progressbar"></div>`;
    const s = this._config.title ?? We(t);
    if (this._noWallbox)
      return o`<h2>${s}</h2>
        <div class="message">${t("live_no_wallbox")}</div>`;
    if (this._failed)
      return o`<h2>${s}</h2>
        <div class="message">
          <span>${t("load_error")}</span>
          <button class="text" @click=${() => this._retry()}>${t("retry")}</button>
        </div>`;
    const i = this._live;
    return i === void 0 ? o`<h2>${s}</h2>
        <div class="spinner" role="progressbar"></div>` : o`<h2>${s}</h2>
      ${i.map((n) => this._block(n, t, e))}`;
  }
  static {
    this.styles = [
      U,
      S`
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
P([
  g({ attribute: !1 })
], C.prototype, "hass");
P([
  _()
], C.prototype, "_config");
P([
  _()
], C.prototype, "_t");
P([
  _()
], C.prototype, "_live");
P([
  _()
], C.prototype, "_received");
P([
  _()
], C.prototype, "_now");
P([
  _()
], C.prototype, "_failed");
P([
  _()
], C.prototype, "_noWallbox");
async function Ut(r, t) {
  return (await r.callWS({
    type: "ev_charging/sessions/list",
    ...t
  })).sessions;
}
function cr(r, t) {
  return r.callWS({ type: "ev_charging/sessions/list", year: t });
}
async function dr(r) {
  return (await r.callWS({
    type: "ev_charging/vehicles/list"
  })).vehicles;
}
const ie = "__unassigned__", Pt = "__none__", ct = {
  vehicle: "",
  location: "",
  chargeType: "",
  card: "",
  status: ""
};
function X(r, t) {
  const e = new Intl.DateTimeFormat("en-US", {
    timeZone: t,
    year: "numeric",
    month: "numeric"
  }).formatToParts(r), s = (i) => Number(e.find((n) => n.type === i)?.value ?? 0);
  return { year: s("year"), month: s("month") };
}
function hr(r, t) {
  return { view: "overview", ...X(r, t), filters: { ...ct } };
}
function ur(r, t, e) {
  const s = r * 12 + (t - 1) + e;
  return { year: Math.floor(s / 12), month: s % 12 + 1 };
}
const ne = [
  ["vehicle", "vehicle"],
  ["location", "location"],
  ["chargeType", "charge_type"],
  ["status", "status"]
];
function pr(r) {
  const t = new URLSearchParams({ year: String(r.year), month: String(r.month) });
  for (const [e, s] of ne)
    r.filters[e] !== "" && t.set(s, r.filters[e]);
  return `/${r.view}?${t.toString()}`;
}
function _r(r, t) {
  const e = {}, s = r.split("/").filter((u) => u !== "")[0];
  (s === "overview" || s === "detail" || s === "recent") && (e.view = s);
  const i = new URLSearchParams(t), n = Number(i.get("year")), a = Number(i.get("month"));
  Number.isInteger(n) && n >= 1e3 && n <= 9999 && Number.isInteger(a) && a >= 1 && a <= 12 && (e.year = n, e.month = a);
  const l = { ...ct };
  let c = !1;
  for (const [u, p] of ne) {
    const h = i.get(p);
    h && (l[u] = h, c = !0);
  }
  return c && (e.filters = l), e;
}
function yt(r) {
  const t = r.reduce((e, s) => e + (s ?? 0), 0);
  return Math.round(t * 1e4) / 1e4;
}
function F(r) {
  return {
    count: r.length,
    energy_kwh: yt(r.map((t) => t.energy_kwh)),
    energy_is_estimate: r.some((t) => t.energy_is_estimate),
    cost: yt(r.map((t) => t.cost)),
    charge_duration_min: yt(r.map((t) => t.charge_duration_min)),
    open_followups: r.filter(
      (t) => t.status === "followup_open" || t.open_fields.length > 0
    ).length
  };
}
function fr(r, t) {
  return X(new Date(r.plug_start), t).month;
}
function ae(r, t, e) {
  return r.filter((s) => fr(s, e) === t);
}
function gr(r, t) {
  return Array.from({ length: 12 }, (e, s) => ({
    month: s + 1,
    ...F(ae(r, s + 1, t))
  }));
}
function mr(r) {
  const t = r.filter((s) => s.location === "external"), e = r.filter((s) => s.location !== "external");
  return {
    all: F(r),
    internal: F(e),
    external: F(t)
  };
}
function vr(r) {
  let t = null;
  return r.latitude !== null && r.longitude !== null ? t = `${r.latitude},${r.longitude}` : r.address && (t = r.address), t === null ? null : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(t)}`;
}
function $r(r) {
  return Object.values(r).some((t) => t !== "");
}
function Kt(r, t) {
  return r.filter((e) => {
    if (t.vehicle === ie) {
      if (e.vehicle_id !== null) return !1;
    } else if (t.vehicle !== "" && e.vehicle_id !== t.vehicle)
      return !1;
    if (t.location !== "" && e.location !== t.location || t.chargeType !== "" && e.charge_type !== t.chargeType || t.status !== "" && e.status !== t.status) return !1;
    if (t.card === Pt) {
      if (e.card_uid !== null) return !1;
    } else if (t.card !== "" && e.card_uid !== t.card)
      return !1;
    return !0;
  });
}
function yr(r, t) {
  const e = /* @__PURE__ */ new Map();
  for (const s of r)
    e.set(s.id, s.name);
  for (const s of t)
    s.vehicle_id !== null && !e.has(s.vehicle_id) && e.set(s.vehicle_id, s.vehicle_name ?? s.vehicle_id);
  return [...e].map(([s, i]) => ({ value: s, label: i }));
}
function br(r, t, e) {
  const s = new Set(
    t.map((n) => n.card_uid).filter((n) => n !== null)
  ), i = /* @__PURE__ */ new Map();
  for (const n of r) {
    const a = [...s].find(
      (l) => l !== "" && (n.uid.startsWith(l) || n.uid.endsWith(l))
    );
    i.set(a ?? n.uid, n.label || n.uid);
  }
  for (const n of t)
    n.card_uid !== null && !i.has(n.card_uid) && i.set(n.card_uid, n.card_label || n.card_uid);
  return e !== "" && e !== Pt && !i.has(e) && i.set(e, e), [...i].map(([n, a]) => ({ value: n, label: a }));
}
function wr(r, t, e) {
  return [.../* @__PURE__ */ new Set([...r, t, e])].sort((s, i) => i - s);
}
function xr(r) {
  return r.phases_recorded ? r.phases.length === 0 ? "detail_no_phases" : null : "detail_phases_not_recorded";
}
var Sr = Object.defineProperty, et = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && Sr(t, e, i), i;
};
const Ar = 600 * 1e3, Cr = "ev_charging/live/subscribe";
class V extends v {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1, this._activeCount = 0;
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
    }, Ar), this.hass && this._started && this._watchSessions(this.hass), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._release(), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one starts the card.
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._started);
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass), this._watchConnection(this.hass));
  }
  // A load that raced a reconnect leaves the card failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(t) {
    this._connectionUnsub || (this._connectionUnsub = pt(t, () => {
      this._failed && this._retry();
    }));
  }
  async _start(t) {
    try {
      this._t = await tt(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = H({}), this._failed = !0;
      return;
    }
    this._watchSessions(t), await this._load(t, !1);
  }
  // Any running session ending changes the month, so it is worth a reload.
  _watchSessions(t) {
    this._release(), this._unsubscribe = t.connection.subscribeMessage(
      (e) => {
        const s = e.filter((i) => i.active).length;
        s < this._activeCount && this.hass && this._load(this.hass, !0), this._activeCount = s;
      },
      { type: Cr }
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
    const { year: s, month: i } = X(/* @__PURE__ */ new Date(), t.config.time_zone);
    try {
      this._sessions = await Ut(t, { year: s, month: i }), this._failed = !1;
    } catch (n) {
      console.error("ev_charging: loading sessions failed", n), e || (this._failed = !0);
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
    const s = e.locale?.language ?? e.language, { year: i, month: n } = X(/* @__PURE__ */ new Date(), e.config.time_zone), a = this._config.title ?? new Intl.DateTimeFormat(s, { month: "long", year: "numeric", timeZone: "UTC" }).format(
      new Date(Date.UTC(i, n - 1, 1))
    );
    if (this._sessions === void 0)
      return o`<h2>${a}</h2>
        <div class="spinner" role="progressbar"></div>`;
    const l = F(this._sessions), c = je(this._sessions);
    return o`
      <h2>${a}</h2>
      <dl>
        ${this._row(t("total_energy"), $(l.energy_kwh, s, l.energy_is_estimate))}
        ${this._row(t("total_cost"), W(l.cost, s, e.config.currency))}
        ${this._row(t("month_solar_share"), k(c, s))}
      </dl>
    `;
  }
  static {
    this.styles = [
      U,
      S`
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
et([
  g({ attribute: !1 })
], V.prototype, "hass");
et([
  _()
], V.prototype, "_config");
et([
  _()
], V.prototype, "_t");
et([
  _()
], V.prototype, "_sessions");
et([
  _()
], V.prototype, "_failed");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Er = { ATTRIBUTE: 1 }, kr = (r) => (...t) => ({ _$litDirective$: r, values: t });
class Tr {
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
const nt = kr(class extends Tr {
  constructor(r) {
    if (super(r), r.type !== Er.ATTRIBUTE || r.name !== "class" || r.strings?.length > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
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
    return D;
  }
});
function oe(r, t) {
  return r.vehicle_id === null ? t("unassigned") : r.vehicle_name ?? r.vehicle_id;
}
const Ur = [
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
function Pr(r) {
  return Ur.includes(r);
}
function Mr(r, t) {
  return Pr(r) ? t(`field_${r}`) : r;
}
const Rr = "M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z";
function f(r, t) {
  return t === null || t === "" || t === m ? d : o`<dt class="muted">${r}</dt>
    <dd>${t}</dd>`;
}
function Or(r, t) {
  const e = vr(r);
  return r.address === null && e === null ? null : o`${r.address ?? d}${e === null ? d : o`<a
        class="map"
        href=${e}
        target="_blank"
        rel="noopener noreferrer"
        title=${t("detail_map_link")}
        aria-label=${t("detail_map_link")}
        ><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d=${Rr} fill="currentColor"></path></svg
        >${r.address === null ? t("detail_map_link") : d}</a
      >`}`;
}
function Nr(r, t, e) {
  const s = xr(r);
  if (s !== null)
    return o`<p class="muted">${t(s)}</p>`;
  const i = e.locale.language, n = e.config.time_zone;
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
      ${r.phases.map(
    (a) => o`<tr>
          <td>${lt(a.start, i, n)}</td>
          <td>${lt(a.end, i, n)}</td>
          <td class="num">${x(a.duration_min)}</td>
          <td class="num">${$(a.energy_kwh, i)}</td>
          <td class="num">${W(a.cost, i, e.config.currency)}</td>
        </tr>`
  )}
    </tbody>
  </table>`;
}
function le(r, t, e) {
  const s = e.locale.language, i = e.config.time_zone, n = t("detail_not_recorded"), a = r.soc_start === null && r.soc_end === null ? null : `${k(r.soc_start, s)} → ${k(r.soc_end, s)}`;
  return o`<div class="body">
    <dl>
      ${f(t("detail_plug_start"), J(r.plug_start, s, i))}
      ${f(t("detail_plug_end"), J(r.plug_end, s, i))}
      ${f(t("detail_plug_duration"), x(r.plug_duration_min))}
      ${f(t("detail_charge_duration"), x(r.charge_duration_min))}
      ${r.pause_duration_min ? f(t("detail_pause_duration"), x(r.pause_duration_min)) : d}
      ${f(t("detail_soc"), a)}
      ${f(t("detail_odometer"), kt(r.odometer_km, s))}
      ${f(t("detail_power_avg"), re(r.power_avg_kw, s))}
      ${r.location === "home" ? o`${f(
    t("detail_energy_grid"),
    r.energy_grid_kwh === null ? n : $(r.energy_grid_kwh, s)
  )}
          ${f(
    t("detail_energy_solar"),
    r.energy_solar_kwh === null ? n : $(r.energy_solar_kwh, s)
  )}` : d}
      ${r.energy_unallocated_kwh > 0 ? f(t("detail_energy_unallocated"), $(r.energy_unallocated_kwh, s)) : d}
      ${f(t("detail_card"), r.card_label ?? r.card_uid)}
      ${f(t("detail_identification"), t(`identification_${r.identification_source}`))}
      ${f(t("detail_address"), Or(r, t))}
      ${f(t("detail_provider"), r.provider)}
      ${f(t("detail_note"), r.note)}
      ${r.open_fields.length > 0 ? f(
    t("detail_open_fields"),
    r.open_fields.map((l) => Mr(l, t)).join(", ")
  ) : d}
    </dl>
    ${Nr(r, t, e)}
  </div>`;
}
const ce = S`
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
var zr = Object.defineProperty, Mt = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && zr(t, e, i), i;
};
class _t extends v {
  constructor() {
    super(...arguments), this.sessions = [];
  }
  render() {
    const t = this.t;
    return !t || !this.hass ? d : o`<ul>
      ${this.sessions.map((e) => this._renderSession(e, t))}
    </ul>`;
  }
  _renderSession(t, e) {
    const s = this.hass, i = s.locale.language, n = t.soc_start !== null && t.soc_end !== null ? `${k(t.soc_start, i)} → ${k(t.soc_end, i)}` : d;
    return o`<li>
      <details>
        <summary>
          <div class="line">
            <span class=${nt({ vehicle: !0, unassigned: t.vehicle_id === null })}
              >${oe(t, e)}</span
            >
            <span class="muted"
              >${J(t.plug_start, i, s.config.time_zone)}</span
            >
          </div>
          <div class="line">
            <span>
              ${$(t.energy_kwh, i, t.energy_is_estimate)} ·
              ${W(t.cost, i, s.config.currency)} ·
              ${x(t.charge_duration_min)}
            </span>
            <span class="muted">${n}</span>
          </div>
          <div class="line">
            <span class="chips">
              <span class="chip">${e(`location_${t.location}`)}</span>
              ${t.status === "complete" ? d : o`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
            </span>
          </div>
        </summary>
        ${le(t, e, s)}
      </details>
    </li>`;
  }
  static {
    this.styles = [
      U,
      ce,
      S`
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
Mt([
  g({ attribute: !1 })
], _t.prototype, "hass");
Mt([
  g({ attribute: !1 })
], _t.prototype, "t");
Mt([
  g({ attribute: !1 })
], _t.prototype, "sessions");
var Dr = Object.defineProperty, A = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && Dr(t, e, i), i;
};
const Hr = 600 * 1e3, Ir = 5, Lr = "M15.41,16.58L10.83,12L15.41,7.42L14,6L8,12L14,18L15.41,16.58Z", Fr = "M8.59,16.58L13.17,12L8.59,7.42L10,6L16,12L10,18L8.59,16.58Z", jr = [
  { id: "overview", label: "view_overview" },
  { id: "recent", label: "view_recent" },
  { id: "detail", label: "view_detail" }
], Wr = ["home", "home_no_wallbox", "external"], Vr = ["ac", "dc", "unknown"], Br = ["complete", "followup_open", "flagged"], qr = [
  { id: "energy", label: "total_energy" },
  { id: "cost", label: "total_cost" },
  { id: "duration", label: "total_duration" }
];
function Gt(r) {
  return o`<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d=${r} fill="currentColor"></path>
  </svg>`;
}
class b extends v {
  constructor() {
    super(...arguments), this._years = [], this._vehicles = [], this._failed = !1, this._metric = "energy", this._started = !1, this._recentRequested = !1;
  }
  connectedCallback() {
    super.connectedCallback(), this._timer = window.setInterval(() => this._refresh(), Hr), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._state !== void 0);
  }
  willUpdate(t) {
    if (t.has("hass") && this.hass && this._state === void 0) {
      const e = this.initialState;
      this._state = {
        ...hr(/* @__PURE__ */ new Date(), this.hass.config.time_zone),
        ...e,
        filters: { ...ct, ...e?.filters }
      };
    }
    this._sync();
  }
  _sync() {
    const t = this.hass, e = this._state;
    !t || !e || (this._watchConnection(t), this._started || (this._started = !0, this._loadShared(t, !1)), e.view !== "recent" && this._yearKey !== e.year && (this._yearKey = e.year, this._yearSessions = void 0, this._loadYear(t, e.year, !1)), e.view === "recent" && !this._recentRequested && (this._recentRequested = !0, this._loadRecent(t, !1)));
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
  // A load that raced a reconnect leaves the view failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(t) {
    this._connectionUnsub || (this._connectionUnsub = pt(t, () => {
      this._failed && this._retry();
    }));
  }
  async _loadShared(t, e) {
    try {
      this._t = await tt(t);
    } catch (s) {
      this._t = H({}), this._fail(s, e);
      return;
    }
    try {
      this._vehicles = await dr(t);
    } catch (s) {
      this._fail(s, e);
    }
  }
  async _loadYear(t, e, s) {
    try {
      const i = await cr(t, e);
      this._yearKey === e && (this._yearSessions = i.sessions, this._years = i.years);
    } catch (i) {
      this._yearKey === e && this._fail(i, s);
    }
  }
  async _loadRecent(t, e) {
    try {
      this._recent = await Ut(t, { limit: Ir });
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
    this._state && this._setState(ur(this._state.year, this._state.month, t));
  }
  render() {
    const t = this._state;
    if (!t || !this.hass)
      return d;
    if (this._failed)
      return this._renderError(this._t ?? H({}));
    const e = this._t;
    return e ? o`
      <div class="view">
        ${this._renderTabs(e, t)}
        ${t.view === "recent" ? d : this._renderFilters(e, t)}
        ${t.view === "recent" ? d : this._renderPeriod(e, t)}
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
      ${jr.map(
      (s) => o`<button
          class=${nt({ tab: !0, active: s.id === e.view })}
          aria-current=${s.id === e.view ? "page" : "false"}
          @click=${() => this._setState({ view: s.id })}
        >
          ${t(s.label)}
        </button>`
    )}
    </nav>`;
  }
  _renderPeriod(t, e) {
    const s = this.hass, i = s.locale.language, n = X(/* @__PURE__ */ new Date(), s.config.time_zone), a = wr(this._years, n.year, e.year);
    return o`<div class="period">
      <button class="icon" aria-label=${t("period_previous")} @click=${() => this._shift(-1)}>
        ${Gt(Lr)}
      </button>
      <select
        aria-label=${t("period_month")}
        @change=${(l) => this._setState({ month: Number(l.target.value) })}
      >
        ${Array.from({ length: 12 }, (l, c) => c + 1).map(
      (l) => o`<option value=${l} .selected=${l === e.month}>
              ${vt(l, i, "long")}
            </option>`
    )}
      </select>
      <select
        aria-label=${t("period_year")}
        @change=${(l) => this._setState({ year: Number(l.target.value) })}
      >
        ${a.map(
      (l) => o`<option value=${l} .selected=${l === e.year}>${l}</option>`
    )}
      </select>
      <button class="icon" aria-label=${t("period_next")} @click=${() => this._shift(1)}>
        ${Gt(Fr)}
      </button>
    </div>`;
  }
  _renderTiles(t, e) {
    const s = this.hass, i = s.locale.language, n = [
      ["total_energy", $(e.energy_kwh, i, e.energy_is_estimate)],
      ["total_cost", W(e.cost, i, s.config.currency)],
      ["total_duration", x(e.charge_duration_min)],
      ["total_sessions", String(e.count)],
      ["open_followups", String(e.open_followups)]
    ];
    return o`<div class="tiles">
      ${n.map(
      ([a, l]) => o`<div class="tile">
          <span class="tile-label muted">${t(a)}</span>
          <span class="tile-value">${l}</span>
        </div>`
    )}
    </div>`;
  }
  // Sessions of the selected year that pass the filters.
  _filteredYear(t) {
    return Kt(this._yearSessions ?? [], t.filters);
  }
  _renderOverview(t, e) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const s = this._filteredYear(e), i = this.hass.config.time_zone, n = gr(s, i);
    return o`
      ${this._renderTiles(t, n[e.month - 1])}
      ${this._renderChart(t, e, n)}
      ${this._renderYearSummary(t, e, mr(s))}
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
        return Yt(t.cost, s, e.config.currency);
      case "duration":
        return Zt(t.charge_duration_min);
      default:
        return qt(t.energy_kwh, s, t.energy_is_estimate);
    }
  }
  _renderChart(t, e, s) {
    const i = this.hass.locale.language, n = Math.max(...s.map((a) => this._metricValue(a)), 0);
    return o`<section class="chart">
      <div class="chart-head">
        <h3>${t("chart_title", { year: e.year })}</h3>
        <label class="metric">
          <span class="muted">${t("chart_metric")}</span>
          <select
            @change=${(a) => {
      this._metric = a.target.value;
    }}
          >
            ${qr.map(
      (a) => o`<option value=${a.id} .selected=${a.id === this._metric}>
                  ${t(a.label)}
                </option>`
    )}
          </select>
        </label>
      </div>
      <div class="plot">
        ${s.map((a) => {
      const l = n > 0 ? this._metricValue(a) / n * 100 : 0, c = vt(a.month, i, "long"), u = a.count === 0 ? m : this._formatMetric(a);
      return o`<button
            class=${nt({ bar: !0, selected: a.month === e.month })}
            title=${`${c}: ${u}`}
            aria-label=${`${c}: ${u}`}
            aria-pressed=${a.month === e.month ? "true" : "false"}
            @click=${() => this._setState({ month: a.month })}
          >
            <span class="fill-area"><span class="fill" style=${`height:${l}%`}></span></span>
            <span class="bar-label muted">${vt(a.month, i, "short")}</span>
            <span class="bar-value">${u}</span>
          </button>`;
    })}
      </div>
    </section>`;
  }
  _renderYearSummary(t, e, s) {
    const i = this.hass, n = i.locale.language, a = [
      ["scope_total", s.all],
      ["scope_internal", s.internal],
      ["scope_external", s.external]
    ], l = [
      ["total_energy", (c) => qt(c.energy_kwh, n, c.energy_is_estimate)],
      ["total_cost", (c) => Yt(c.cost, n, i.config.currency)],
      ["total_duration", (c) => Zt(c.charge_duration_min)],
      ["total_sessions", (c) => String(c.count)]
    ];
    return o`<section class="year-summary">
      <h3>${t("year_summary_title", { year: e.year })}</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            ${a.map(([c]) => o`<th class="num">${t(c)}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${l.map(
      ([c, u]) => o`<tr>
              <th>${t(c)}</th>
              ${a.map(([, p]) => o`<td class="num">${u(p)}</td>`)}
            </tr>`
    )}
        </tbody>
      </table>
    </section>`;
  }
  _renderFilters(t, e) {
    const s = this._yearSessions ?? [], i = e.filters, n = [
      ...yr(this._vehicles, s),
      { value: ie, label: t("unassigned") }
    ], a = [
      { value: Pt, label: t("filter_no_card") },
      ...br(
        this._vehicles.flatMap((l) => l.cards),
        s,
        i.card
      )
    ];
    return o`<div class="filters">
      ${this._renderFilter(t("filter_vehicle"), "vehicle", n, t)}
      ${this._renderFilter(
      t("filter_location"),
      "location",
      Wr.map((l) => ({ value: l, label: t(`location_${l}`) })),
      t
    )}
      ${this._renderFilter(
      t("filter_charge_type"),
      "chargeType",
      Vr.map((l) => ({ value: l, label: t(`charge_type_${l}`) })),
      t
    )}
      ${this._renderFilter(t("filter_card"), "card", a, t)}
      ${this._renderFilter(
      t("filter_status"),
      "status",
      Br.map((l) => ({ value: l, label: t(`status_${l}`) })),
      t
    )}
      ${$r(i) ? o`<button
            class="text reset"
            @click=${() => this._setState({ filters: { ...ct } })}
          >
            ${t("filter_reset")}
          </button>` : d}
    </div>`;
  }
  _renderDetail(t, e) {
    if (!this._yearSessions)
      return o`<div class="spinner" role="progressbar"></div>`;
    const s = this.hass.config.time_zone, i = ae(this._yearSessions, e.month, s), n = Kt(i, e.filters);
    return o`
      ${this._renderTiles(t, F(n))}
      <p class="count muted">
        ${t("filter_count", { shown: n.length, total: i.length })}
      </p>
      ${n.length === 0 ? o`<div class="message">
            ${i.length === 0 ? t("no_sessions") : t("no_sessions_filtered")}
          </div>` : this._renderTable(n, t)}
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
  _renderFilter(t, e, s, i) {
    const n = this._state.filters[e];
    return o`<label class="filter">
      <span class="muted">${t}</span>
      <select
        @change=${(a) => this._setFilter(e, a.target.value)}
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
      ${t.map((s) => this._renderSession(s, e))}
    </div>`;
  }
  _renderSession(t, e) {
    const s = this.hass, i = s.locale.language, n = s.config.time_zone, a = t.vehicle_id === null;
    return o`<details class="session">
      <summary>
        <span class="c-date">${J(t.plug_start, i, n)}</span>
        <span class=${nt({ "c-vehicle": !0, vehicle: !0, unassigned: a })}
          >${oe(t, e)}</span
        >
        <span class="c-location"><span class="chip">${e(`location_${t.location}`)}</span></span>
        <span class="c-type"><span class="chip">${e(`charge_type_${t.charge_type}`)}</span></span>
        <span class="c-energy num"
          >${$(t.energy_kwh, i, t.energy_is_estimate)}</span
        >
        <span class="c-cost num">${W(t.cost, i, s.config.currency)}</span>
        <span class="c-duration num">${x(t.charge_duration_min)}</span>
        <span class="c-status">
          ${t.status === "complete" ? d : o`<span class="chip warn">${e(`status_${t.status}`)}</span>`}
          ${t.location_conflict ? o`<span class="chip alert">${e("flag_location_conflict")}</span>` : d}
          ${t.identification_conflict ? o`<span class="chip alert">${e("flag_identification_conflict")}</span>` : d}
          ${t.charge_error ? o`<span class="chip alert">${e("flag_charge_error")}</span>` : d}
          ${t.energy_unallocated_kwh > 0 ? o`<span class="chip warn">${e("flag_unallocated_energy")}</span>` : d}
        </span>
      </summary>
      ${le(t, e, s)}
    </details>`;
  }
  static {
    this.styles = [
      U,
      ce,
      S`
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
A([
  g({ attribute: !1 })
], b.prototype, "hass");
A([
  g({ attribute: !1 })
], b.prototype, "initialState");
A([
  _()
], b.prototype, "_state");
A([
  _()
], b.prototype, "_t");
A([
  _()
], b.prototype, "_yearSessions");
A([
  _()
], b.prototype, "_years");
A([
  _()
], b.prototype, "_recent");
A([
  _()
], b.prototype, "_vehicles");
A([
  _()
], b.prototype, "_failed");
A([
  _()
], b.prototype, "_metric");
var Yr = Object.defineProperty, ft = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && Yr(t, e, i), i;
};
const Zr = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";
class rt extends v {
  constructor() {
    super(...arguments), this.narrow = !1;
  }
  willUpdate() {
    this._initialState === void 0 && (this._initialState = _r(this.route?.path ?? "", window.location.search));
  }
  _toggleMenu() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: !0, composed: !0 }));
  }
  _onStateChanged(t) {
    const e = this.route?.prefix ?? `/${this.panel?.url_path ?? ""}`;
    window.history.replaceState(window.history.state, "", `${e}${pr(t.detail)}`);
  }
  render() {
    return o`
      <header>
        ${this.narrow ? o`<button class="menu" @click=${() => this._toggleMenu()}>
              <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d=${Zr} fill="currentColor"></path>
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
      U,
      S`
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
ft([
  g({ attribute: !1 })
], rt.prototype, "hass");
ft([
  g({ type: Boolean })
], rt.prototype, "narrow");
ft([
  g({ attribute: !1 })
], rt.prototype, "route");
ft([
  g({ attribute: !1 })
], rt.prototype, "panel");
var Kr = Object.defineProperty, de = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && Kr(t, e, i), i;
};
class Rt extends v {
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
      U,
      S`
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
de([
  g({ attribute: !1 })
], Rt.prototype, "hass");
de([
  g({ type: Boolean, reflect: !0, attribute: "is-panel" })
], Rt.prototype, "isPanel");
var Gr = Object.defineProperty, M = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, a; n >= 0; n--)
    (a = r[n]) && (i = a(t, e, i) || i);
  return i && Gr(t, e, i), i;
};
const L = 3, Ot = 20, Jr = 600 * 1e3;
function he(r) {
  return Number.isInteger(r) && r >= 1 && r <= Ot;
}
class B extends v {
  constructor() {
    super(...arguments), this._config = {}, this._failed = !1, this._started = !1;
  }
  setConfig(t) {
    if (!he(t.count ?? L))
      throw new Error(`count must be a whole number from 1 to ${Ot}`);
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
    }, Jr), this.hass && this._watchConnection(this.hass);
  }
  disconnectedCallback() {
    window.clearInterval(this._timer), this._connectionUnsub?.(), this._connectionUnsub = void 0, super.disconnectedCallback();
  }
  // Home Assistant sets hass on every state change; only the first one loads.
  shouldUpdate(t) {
    return !(t.size === 1 && t.has("hass") && this._started);
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, this._start(this.hass), this._watchConnection(this.hass));
  }
  // A load that raced a reconnect leaves the card failed; retry once the
  // connection is back instead of waiting only for a manual click.
  _watchConnection(t) {
    this._connectionUnsub || (this._connectionUnsub = pt(t, () => {
      this._failed && this._retry();
    }));
  }
  async _start(t) {
    try {
      this._t = await tt(t);
    } catch (e) {
      console.error("ev_charging: loading translations failed", e), this._t = H({}), this._failed = !0;
      return;
    }
    await this._load(t, !1);
  }
  async _load(t, e) {
    try {
      this._sessions = await Ut(t, { limit: this._config.count ?? L }), this._failed = !1;
    } catch (s) {
      console.error("ev_charging: loading sessions failed", s), e || (this._failed = !0);
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
      U,
      S`
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
M([
  g({ attribute: !1 })
], B.prototype, "hass");
M([
  _()
], B.prototype, "_config");
M([
  _()
], B.prototype, "_t");
M([
  _()
], B.prototype, "_sessions");
M([
  _()
], B.prototype, "_failed");
class gt extends v {
  constructor() {
    super(...arguments), this._config = {}, this._started = !1;
  }
  setConfig(t) {
    this._config = t;
  }
  willUpdate(t) {
    t.has("hass") && this.hass && !this._started && (this._started = !0, tt(this.hass).then(
      (e) => this._t = e,
      () => this._t = H({})
    ));
  }
  _changed(t) {
    const e = Number(t.target.value);
    if (!he(e)) {
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
        max=${Ot}
        step="1"
        .value=${String(this._config.count ?? L)}
        @change=${(e) => this._changed(e)}
      />
    </label>` : o``;
  }
  static {
    this.styles = [
      U,
      S`
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
M([
  g({ attribute: !1 })
], gt.prototype, "hass");
M([
  _()
], gt.prototype, "_config");
M([
  _()
], gt.prototype, "_t");
function R(r, t) {
  customElements.get(r) || customElements.define(r, t);
}
R("ev-charging-panel-view", b);
R("ev-charging-session-list", _t);
R("ev-charging-panel", rt);
R("ev-charging-panel-card", Rt);
R("ev-charging-recent-card", B);
R("ev-charging-recent-card-editor", gt);
R("ev-charging-live-card", C);
R("ev-charging-month-card", V);
const dt = window;
dt.customCards = dt.customCards ?? [];
for (const r of [
  "ev-charging-panel-card",
  "ev-charging-recent-card",
  "ev-charging-live-card",
  "ev-charging-month-card"
])
  dt.customCards.some((t) => t.type === r) || dt.customCards.push({ type: r, name: r });
