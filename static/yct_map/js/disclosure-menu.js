export function createDisclosureMenu({ element, documentObject = globalThis.document } = {}) {
  if (!element) return { destroy() {} };
  const summary = element.querySelector("summary");

  function close({ restoreFocus = false } = {}) {
    element.removeAttribute("open");
    if (restoreFocus) summary?.focus?.();
  }

  function pointerDown(event) {
    if (!element.hasAttribute("open")) return;
    const backdrop = event.target?.closest?.("[data-menu-dismiss]");
    if (!backdrop && element.contains(event.target)) return;
    event.preventDefault?.();
    event.stopPropagation?.();
    close();
  }

  function keyDown(event) {
    if (event.key !== "Escape" || !element.hasAttribute("open")) return;
    event.preventDefault?.();
    close({ restoreFocus: true });
  }

  function selected(event) {
    if (event.target?.closest?.(".team-menu-panel a, .team-menu-panel button")) close();
  }

  documentObject.addEventListener("pointerdown", pointerDown, true);
  documentObject.addEventListener("keydown", keyDown);
  element.addEventListener("click", selected);
  return { close, destroy() {
    documentObject.removeEventListener("pointerdown", pointerDown, true);
    documentObject.removeEventListener("keydown", keyDown);
    element.removeEventListener("click", selected);
  } };
}
