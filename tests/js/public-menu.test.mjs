import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import { createDisclosureMenu } from "../../static/yct_map/js/disclosure-menu.js";

const css = readFileSync(new URL("../../static/yct_map/css/app.css", import.meta.url), "utf8");
const template = readFileSync(new URL("../../templates/map/index.html", import.meta.url), "utf8");

function harness() {
  const listeners = new Map();
  const documentObject = { addEventListener(type, fn) { listeners.set(type, fn); }, removeEventListener() {} };
  const summary = { focused: false, focus() { this.focused = true; } };
  const element = {
    open: true, listeners: new Map(),
    querySelector() { return summary; },
    hasAttribute(name) { return name === "open" && this.open; },
    removeAttribute(name) { if (name === "open") this.open = false; },
    contains(target) { return target.inside === true; },
    addEventListener(type, fn) { this.listeners.set(type, fn); }, removeEventListener() {},
  };
  return { element, summary, listeners, documentObject };
}

test("open public menu owns an intentional layer above ordinary HUD contexts", () => {
  assert.match(css, /\.app-header:has\(\.team-menu\[open\]\)\s*\{[^}]*z-index:\s*20/s);
  assert.match(css, /\.team-menu-panel\s*\{[^}]*z-index:\s*2/s);
  assert.match(css, /\.team-menu-backdrop\s*\{[^}]*position:\s*fixed[^}]*inset:\s*0/s);
  assert.match(template, /data-menu-dismiss/);
  assert.match(template, /Data status/);
  assert.match(template, /Published campus information is reviewed before release\./);
  assert.doesNotMatch(template, /dataset-badge/);
});

test("outside pointer and Escape close the menu without reaching controls underneath", () => {
  const state = harness();
  createDisclosureMenu(state);
  let prevented = false; let stopped = false;
  state.listeners.get("pointerdown")({ target: { inside: false, closest: () => null },
    preventDefault() { prevented = true; }, stopPropagation() { stopped = true; } });
  assert.equal(state.element.open, false); assert.equal(prevented, true); assert.equal(stopped, true);
  state.element.open = true;
  state.listeners.get("keydown")({ key: "Escape", preventDefault() {} });
  assert.equal(state.element.open, false); assert.equal(state.summary.focused, true);
});

test("selecting a menu action closes the disclosure", () => {
  const state = harness();
  createDisclosureMenu(state);
  state.element.listeners.get("click")({ target: { closest: (selector) => selector.includes("team-menu-panel") } });
  assert.equal(state.element.open, false);
});
