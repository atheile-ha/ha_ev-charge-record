// Keeps the custom elements of this bundle known to the element registry of
// the page. The Home Assistant frontend may replace window.customElements with
// a polyfill registry after this bundle ran; that registry does not know
// elements defined before it, so the dashboard reports the cards as missing.
// The elements are therefore defined again in whichever registry the page
// currently exposes, until it knows all of them.

export interface ElementRegistry {
  get(name: string): CustomElementConstructor | undefined;
  define(name: string, constructor: CustomElementConstructor): void;
}

export type ElementDefinitions = ReadonlyArray<readonly [string, CustomElementConstructor]>;

/** Define every element the registry does not know yet; return whether it knows all afterwards. */
export function ensureDefined(registry: ElementRegistry, elements: ElementDefinitions): boolean {
  let complete = true;
  for (const [name, constructor] of elements) {
    if (registry.get(name)) {
      continue;
    }
    try {
      registry.define(name, constructor);
    } catch {
      // A registry that refuses the name leaves the element undefined there.
    }
    if (!registry.get(name)) {
      complete = false;
    }
  }
  return complete;
}

export interface KeepDefinedOptions {
  registry?: () => ElementRegistry;
  intervalMs?: number;
  onIncomplete?: () => void;
}

/**
 * Define the elements now and check again at the interval, so a registry that
 * replaces the current one later learns them too. Returns a function that
 * stops the checks. onIncomplete is called once, the first time a registry
 * refuses an element.
 */
export function keepDefined(
  elements: ElementDefinitions,
  options: KeepDefinedOptions = {},
): () => void {
  const registry = options.registry ?? (() => window.customElements);
  let reported = false;
  const check = (): void => {
    if (!ensureDefined(registry(), elements) && !reported) {
      reported = true;
      options.onIncomplete?.();
    }
  };
  check();
  const timer = setInterval(check, options.intervalMs ?? 2000);
  return () => clearInterval(timer);
}
