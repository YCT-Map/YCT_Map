const TARGETED_TYPES = new Set(["CORRECT_LOCATION", "ADD_INFORMATION"]);

function csrfToken() {
  return document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
}

export function createContributions({ panel, openButton, features, endpoint, onOpen, onClose,
  onPickPoint, onClearPoint, request = fetch }) {
  const form = panel.querySelector("#contribution-form");
  const formState = panel.querySelector("#contribution-form-state");
  const success = panel.querySelector("#contribution-success");
  const type = panel.querySelector("#contribution-type");
  const target = panel.querySelector("#contribution-target");
  const targetGroup = panel.querySelector("#contribution-target-group");
  const name = panel.querySelector("#contribution-name");
  const nameGroup = panel.querySelector("#contribution-name-group");
  const categoryGroup = panel.querySelector("#contribution-category-group");
  const submit = panel.querySelector("#submit-contribution");
  const error = panel.querySelector("#contribution-error");
  const pointStatus = panel.querySelector("#contribution-point-status");
  const clearPoint = panel.querySelector("#clear-contribution-point");
  const pickPoint = panel.querySelector("#pick-contribution-point");
  let point = null;
  let requestId = null;

  target.replaceChildren();
  const placeholder = document.createElement("option");
  Object.assign(placeholder, { value: "", textContent: "Choose a place" });
  target.append(placeholder);
  for (const feature of features) {
    const option = document.createElement("option");
    option.value = feature.properties.id;
    option.textContent = feature.properties.name;
    target.append(option);
  }

  function updateFields() {
    const targeted = TARGETED_TYPES.has(type.value);
    targetGroup.hidden = !targeted;
    target.required = targeted;
    const adding = type.value === "ADD_LOCATION";
    nameGroup.hidden = !adding;
    categoryGroup.hidden = !adding;
    name.required = adding;
  }

  function setPoint(nextPoint) {
    point = nextPoint;
    clearPoint.hidden = !point;
    pointStatus.textContent = point ? "Proposed point selected. You can choose it again to adjust it." : "A map point is optional.";
  }

  function reset() {
    form.reset();
    requestId = null;
    setPoint(null);
    onClearPoint?.();
    error.hidden = true;
    formState.hidden = false;
    success.hidden = true;
    updateFields();
  }

  function open() {
    panel.hidden = false;
    onOpen?.();
    type.focus();
  }

  function close() {
    panel.hidden = true;
    onClearPoint?.();
    onClose?.();
    openButton.focus();
  }

  async function send(event) {
    event.preventDefault();
    error.hidden = true;
    if (!form.reportValidity()) return;
    requestId ||= globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
    submit.disabled = true;
    submit.textContent = "Submitting…";
    const payload = {
      request_id: requestId, type: type.value, target_location: targetGroup.hidden ? null : target.value,
      proposed_name: nameGroup.hidden ? "" : name.value,
      proposed_category: categoryGroup.hidden ? "" : panel.querySelector("#contribution-category").value,
      context: panel.querySelector("#contribution-context").value,
      description: panel.querySelector("#contribution-description").value,
      proposed_point: point ? {
        latitude: Number(point.latitude.toFixed(6)),
        longitude: Number(point.longitude.toFixed(6)),
      } : null,
      website: panel.querySelector("#contribution-website").value,
    };
    try {
      const response = await request(endpoint, { method: "POST", headers: {
        Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": csrfToken(),
      }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Your report could not be submitted.");
      panel.querySelector("#contribution-reference").textContent = String(result.id).slice(0, 8).toUpperCase();
      formState.hidden = true;
      success.hidden = false;
      success.querySelector("h2").focus?.();
    } catch (submissionError) {
      error.textContent = submissionError.message;
      error.hidden = false;
    } finally {
      submit.disabled = false;
      submit.textContent = "Submit for review";
    }
  }

  openButton.addEventListener("click", open);
  panel.querySelector("#close-contribution").addEventListener("click", close);
  panel.querySelector("#cancel-contribution").addEventListener("click", close);
  panel.querySelector("#finish-contribution").addEventListener("click", close);
  panel.querySelector("#new-contribution").addEventListener("click", () => { reset(); type.focus(); });
  type.addEventListener("change", updateFields);
  form.addEventListener("submit", send);
  pickPoint.addEventListener("click", () => {
    panel.hidden = true;
    onPickPoint?.((coordinates) => {
      setPoint({ longitude: coordinates[0], latitude: coordinates[1] });
      panel.hidden = false;
      pickPoint.focus();
    });
  });
  clearPoint.addEventListener("click", () => { setPoint(null); onClearPoint?.(); });
  updateFields();
  return { open, close, reset, setMapAvailable: (available) => { pickPoint.disabled = !available; } };
}
