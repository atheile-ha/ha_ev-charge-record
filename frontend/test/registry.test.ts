import { afterEach, describe, expect, it, vi } from "vitest";
import { type ElementRegistry, ensureDefined, keepDefined } from "../src/registry";

class FakeRegistry implements ElementRegistry {
  readonly defined = new Map<string, CustomElementConstructor>();
  constructor(private readonly refuse: ReadonlySet<string> = new Set()) {}
  get(name: string): CustomElementConstructor | undefined {
    return this.defined.get(name);
  }
  define(name: string, constructor: CustomElementConstructor): void {
    if (this.refuse.has(name) || this.defined.has(name)) {
      throw new Error(`refused ${name}`);
    }
    this.defined.set(name, constructor);
  }
}

const A = class {} as unknown as CustomElementConstructor;
const B = class {} as unknown as CustomElementConstructor;
const ELEMENTS = [
  ["ev-a", A],
  ["ev-b", B],
] as const;

afterEach(() => {
  vi.useRealTimers();
});

describe("ensureDefined", () => {
  it("defines every unknown element and reports completeness", () => {
    const registry = new FakeRegistry();
    expect(ensureDefined(registry, ELEMENTS)).toBe(true);
    expect(registry.get("ev-a")).toBe(A);
    expect(registry.get("ev-b")).toBe(B);
  });

  it("leaves a name the registry already knows untouched", () => {
    const registry = new FakeRegistry();
    const other = class {} as unknown as CustomElementConstructor;
    registry.defined.set("ev-a", other);
    expect(ensureDefined(registry, ELEMENTS)).toBe(true);
    expect(registry.get("ev-a")).toBe(other);
  });

  it("reports a refused name without throwing and still defines the others", () => {
    const registry = new FakeRegistry(new Set(["ev-a"]));
    expect(ensureDefined(registry, ELEMENTS)).toBe(false);
    expect(registry.get("ev-b")).toBe(B);
  });
});

describe("keepDefined", () => {
  it("defines the elements again in a registry that replaced the first one later", () => {
    vi.useFakeTimers();
    let current = new FakeRegistry();
    const stop = keepDefined(ELEMENTS, { registry: () => current, intervalMs: 1000 });
    expect(current.get("ev-a")).toBe(A);

    current = new FakeRegistry();
    expect(current.get("ev-a")).toBeUndefined();
    vi.advanceTimersByTime(1000);
    expect(current.get("ev-a")).toBe(A);
    expect(current.get("ev-b")).toBe(B);
    stop();
  });

  it("reports a refusing registry only once", () => {
    vi.useFakeTimers();
    const onIncomplete = vi.fn();
    const stop = keepDefined(ELEMENTS, {
      registry: () => new FakeRegistry(new Set(["ev-b"])),
      intervalMs: 1000,
      onIncomplete,
    });
    vi.advanceTimersByTime(5000);
    expect(onIncomplete).toHaveBeenCalledTimes(1);
    stop();
  });
});
