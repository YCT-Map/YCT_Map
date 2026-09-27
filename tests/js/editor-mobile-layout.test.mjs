import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../../static/yct_map/css/editor.css", import.meta.url), "utf8");
const base = readFileSync(new URL("../../templates/editor/base.html", import.meta.url), "utf8");

test("mobile editor replaces the desktop navigation stack with an accessible menu", () => {
  assert.match(base, /<details class="editor-mobile-menu">/);
  assert.match(base, /aria-label="Mobile editor navigation"/);
  assert.match(css, /\.editor-desktop-nav\s*\{\s*display:\s*none/);
  assert.match(css, /\.editor-mobile-menu\s*\{\s*display:\s*block/);
  assert.match(css, /min-height:\s*2\.75rem/);
});

test("mobile editor content and field maps stay within the viewport", () => {
  assert.match(css, /overflow-x:\s*hidden/);
  assert.match(css, /\.editor-table-wrap\s*\{[^}]*overflow-scrolling:\s*touch/s);
  assert.match(css, /\.survey-field-map\s*\{[^}]*height:\s*46dvh/s);
  assert.match(css, /#survey-actions\s*\{[^}]*grid-template-columns:/s);
});
