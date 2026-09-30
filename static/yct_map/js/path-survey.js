const root = typeof document === "undefined" ? null : document.querySelector(".survey-console");
const csrf = () => document.cookie.split("; ").find((x) => x.startsWith("csrftoken="))?.split("=")[1] || "";

export function qualityFor(accuracy) {
  if (accuracy <= 25) return { classification: "ACCEPTED", label: `Good GPS accuracy (${Math.round(accuracy)} m)` };
  if (accuracy <= 50) return { classification: "WEAK", label: `Weak GPS accuracy (${Math.round(accuracy)} m)` };
  return { classification: "REJECTED", label: `GPS sample rejected (${Math.round(accuracy)} m accuracy)` };
}

export function shouldRecord(status) { return status === "ACTIVE"; }
export function formatDuration(totalSeconds) { const value = Math.max(0, Math.floor(Number(totalSeconds) || 0)); return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, "0")}`; }
export function createElapsedClock({initial=0, onTick=()=>{}, setTimer=setInterval, clearTimer=clearInterval,
  now=()=>globalThis.performance?.now?.() ?? Date.now()}) {
  let committed = Math.max(0, Number(initial) || 0); let startedAt = null; let timer = null;
  const current = () => committed + (startedAt === null ? 0 : Math.max(0, Math.floor((now() - startedAt) / 1000)));
  const render = () => onTick(current());
  const start = () => { if (timer !== null) return; startedAt = now(); timer = setTimer(render, 1000); };
  const stop = () => { if (timer !== null) { committed = current(); clearTimer(timer); } timer = null; startedAt = null; render(); };
  render(); return {start, stop, get seconds(){return current();}};
}

function openBuffer() { return new Promise((resolve, reject) => { const request = indexedDB.open("yct-map-surveys", 1);
  request.onupgradeneeded = () => request.result.createObjectStore("batches", {keyPath:"survey"});
  request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error); }); }
async function buffered(id) { const db = await openBuffer(); return new Promise((resolve) => { const request = db.transaction("batches").objectStore("batches").get(id); request.onsuccess = () => resolve(request.result?.samples || []); request.onerror = () => resolve([]); }); }
async function saveBuffer(id, samples) { const db = await openBuffer(); return new Promise((resolve, reject) => { const request = db.transaction("batches", "readwrite").objectStore("batches").put({survey:id, samples}); request.onsuccess=()=>resolve(); request.onerror=()=>reject(request.error); }); }

export function createSurveyController({id, status, nextSequence=0, send, geolocation, onStatus, onBatch=()=>{}, onPosition=()=>{}, onCaptureStart=()=>{}, onCaptureStop=()=>{}, loadBuffered=buffered, storeBuffered=saveBuffer}) {
  let watchId = null; let sequence = Number(nextSequence); let queue = []; let flushing = false;
  let bufferReady = false; let startRequested = false; let bufferAvailable = true;
  async function flush() {
    if (!bufferReady || !queue.length || flushing) return queue.length === 0;
    flushing = true;
    const batch = [...queue];
    let sent = false;
    try { const result = await send(batch); queue = queue.slice(batch.length); await storeBuffered(id, queue); bufferAvailable = true; onBatch(result); sent = true; }
    catch {
      try { await storeBuffered(id, queue); bufferAvailable = true; } catch { bufferAvailable = false; }
      onStatus(bufferAvailable ? "Samples are safely buffered on this device until connectivity returns."
        : "Samples remain in this page only. Keep it open and restore connectivity before pausing or finishing.");
    } finally {
      flushing = false;
      if (sent && queue.length) void flush();
    }
    return queue.length === 0;
  }
  function start() {
    if (!shouldRecord(status) || watchId !== null) return;
    if (!geolocation) { onStatus("Location is unavailable in this browser."); return; }
    if (!bufferReady) { startRequested = true; onStatus("Preparing the private survey buffer..."); return true; }
    onStatus("Requesting location permission…");
    watchId = geolocation.watchPosition((position) => {
      const q = qualityFor(position.coords.accuracy); onStatus(q.label);
      onPosition(position, q);
      queue.push({sequence: ++sequence, captured_at: new Date(position.timestamp).toISOString(),
        latitude: position.coords.latitude, longitude: position.coords.longitude,
        accuracy: position.coords.accuracy, speed: position.coords.speed, heading: position.coords.heading});
      storeBuffered(id, queue).then(() => { bufferAvailable = true; return flush(); })
        .catch(() => { bufferAvailable = false; onStatus("Offline storage is unavailable; attempting immediate synchronization."); return flush(); });
    }, (error) => { onStatus(error.code === 1 ? "Location permission denied. No samples were recorded." : "Location temporarily unavailable."); stop(); },
    {enableHighAccuracy: true, maximumAge: 0, timeout: 15000});
    onCaptureStart(); return true;
  }
  function stop() { startRequested = false; if (watchId !== null) { geolocation?.clearWatch(watchId); watchId = null; onCaptureStop(); } }
  const ready = Promise.resolve().then(() => loadBuffered(id)).then((items) => {
    queue = [...items].sort((a,b) => Number(a.sequence) - Number(b.sequence));
    sequence = Math.max(sequence, ...queue.map((x) => Number(x.sequence)), 0);
    bufferReady = true;
    if (startRequested) { startRequested = false; start(); }
    return flush();
  }).catch(() => { bufferReady = true; bufferAvailable = false; onStatus("Offline storage is unavailable. Keep this page open while recording."); if (startRequested) { startRequested = false; start(); } return false; });
  return {start, stop, flush, ready, get bufferSize() { return queue.length; }, get bufferAvailable() { return bufferAvailable; }};
}

export function traceFeature(coordinates) { return coordinates.length < 2 ? {type:"FeatureCollection",features:[]} : {type:"Feature",properties:{evidence:true},geometry:{type:"LineString",coordinates}}; }
export function createLifecycleSubmissionGate({synchronize, submit, onBusy=()=>{}, onBlocked=()=>{}}) {
  let pending = null;
  let submitted = false;
  return {
    request(action) {
      if (submitted) return Promise.resolve(true);
      if (pending) return pending;
      onBusy(action);
      pending = Promise.resolve().then(synchronize).then((synchronized) => {
        if (!synchronized) {
          pending = null;
          onBlocked();
          return false;
        }
        submitted = true;
        submit(action);
        return true;
      }).catch((error) => {
        pending = null;
        onBlocked(error);
        return false;
      });
      return pending;
    },
    get busy() { return pending !== null; },
    get submitted() { return submitted; },
  };
}

export function createFieldMap({maplibregl, element, statusElement, network, trace}) {
  const map = new maplibregl.Map({container:element,style:"https://tiles.openfreemap.org/styles/liberty",center:[3.37424,6.51857],zoom:16});
  let currentTrace=trace; let currentPosition=null;
  const setStatus = (message,state="ready") => { element.dataset.state=state; statusElement.textContent=message; };
  map.on("error",()=>setStatus("Basemap detail is temporarily unavailable. GPS recording and evidence synchronization continue.","error"));
  map.on("load",()=>{
    map.addSource("survey-network",{type:"geojson",data:network});
    map.addLayer({id:"survey-network",type:"line",source:"survey-network",paint:{"line-color":"#7557b7","line-width":3,"line-opacity":.65,"line-dasharray":[2,1.5]}});
    map.addSource("survey-trace",{type:"geojson",data:traceFeature(currentTrace)});
    map.addLayer({id:"survey-trace",type:"line",source:"survey-trace",paint:{"line-color":"#1769e0","line-width":6,"line-opacity":.9}});
    map.addSource("survey-position",{type:"geojson",data:{type:"FeatureCollection",features:[]}});
    map.addLayer({id:"survey-position",type:"circle",source:"survey-position",paint:{"circle-color":"#1769e0","circle-radius":8,"circle-stroke-color":"#fff","circle-stroke-width":3}});
    const coordinates=network.features.flatMap((feature)=>feature.geometry.coordinates);
    if(coordinates.length){const bounds=coordinates.reduce((value,point)=>value.extend(point),new maplibregl.LngLatBounds(coordinates[0],coordinates[0]));map.fitBounds(bounds,{padding:35,maxZoom:18,duration:0});}
    if(currentPosition)map.getSource("survey-position").setData({type:"Feature",properties:{accuracy:currentPosition.coords.accuracy},geometry:{type:"Point",coordinates:[currentPosition.coords.longitude,currentPosition.coords.latitude]}});
    setStatus("Field map ready. Existing paths and synchronized usable evidence are shown."); map.resize();
  });
  return {
    updateTrace(coordinates){currentTrace=coordinates;const source=map.getSource("survey-trace");if(source)source.setData(traceFeature(coordinates));},
    updatePosition(position){currentPosition=position;const source=map.getSource("survey-position");if(source)source.setData({type:"Feature",properties:{accuracy:position.coords.accuracy},geometry:{type:"Point",coordinates:[position.coords.longitude,position.coords.latitude]}});},
  };
}

export function createReviewMap({maplibregl, element, statusElement, network, trace}) {
  const map = new maplibregl.Map({container:element,style:"https://tiles.openfreemap.org/styles/liberty",center:[3.37424,6.51857],zoom:16});
  const setStatus = (message,state="ready") => { element.dataset.state=state; statusElement.textContent=message; };
  map.on("error",()=>setStatus("Basemap detail is temporarily unavailable. The persisted evidence summary remains unchanged.","error"));
  map.on("load",()=>{
    map.addSource("survey-review-network",{type:"geojson",data:network});
    map.addLayer({id:"survey-review-network-unmatched",type:"line",source:"survey-review-network",filter:["==",["get","match_classification"],"UNMATCHED"],paint:{
      "line-color":"#8b9690","line-width":2,"line-opacity":.38,"line-dasharray":[2,2],
    }});
    map.addLayer({id:"survey-review-network-candidates",type:"line",source:"survey-review-network",filter:["!=",["get","match_classification"],"UNMATCHED"],paint:{
      "line-color":["match",["get","match_classification"],"DISCREPANCY","#b43b2d","STRONG","#17663c","PARTIAL","#c47a12","AMBIGUOUS","#7656b5","#8b9690"],
      "line-width":4,"line-opacity":.82,
    }});
    map.addSource("survey-review-trace",{type:"geojson",data:traceFeature(trace)});
    map.addLayer({id:"survey-review-trace",type:"line",source:"survey-review-trace",paint:{"line-color":"#1769e0","line-width":5,"line-opacity":.82}});
    const coordinates=[...network.features.flatMap((feature)=>feature.geometry.coordinates),...trace];
    if(coordinates.length){const bounds=coordinates.reduce((value,point)=>value.extend(point),new maplibregl.LngLatBounds(coordinates[0],coordinates[0]));map.fitBounds(bounds,{padding:35,maxZoom:18,duration:0});}
    setStatus("Read-only evidence overview ready. Blue is the usable trace; graph colours show persisted candidate analysis.");
    map.resize();
  });
  return map;
}

if (root) {
  const quality = document.querySelector("#survey-quality");
  const activeDisplay = document.querySelector("#survey-elapsed");
  const activeInput = document.querySelector("#active-capture-seconds");
  const sessionDisplay = document.querySelector("#survey-session-duration");
  let heartbeat = null; let timingAvailable = root.dataset.timingStarted === "true" || !["COMPLETED","REVIEWED","ABANDONED"].includes(root.dataset.status);
  const clock = createElapsedClock({initial:root.dataset.activeSeconds, onTick:(seconds)=>{if(timingAvailable)activeDisplay.textContent=formatDuration(seconds);if(activeInput)activeInput.value=String(seconds);}});
  const persistTiming = () => fetch(root.dataset.timingUrl, {method:"POST", headers:{"Content-Type":"application/json","X-CSRFToken":csrf()}, body:JSON.stringify({active_capture_seconds:clock.seconds}), keepalive:true}).catch(()=>{});
  const startClock = () => { timingAvailable=true; activeDisplay.textContent=formatDuration(clock.seconds); clock.start(); if(!heartbeat) heartbeat=setInterval(persistTiming,5000); persistTiming(); };
  const stopClock = () => { clock.stop(); clearInterval(heartbeat); heartbeat=null; persistTiming(); };
  if (sessionDisplay) sessionDisplay.textContent = formatDuration(sessionDisplay.dataset.seconds);
  let fieldMap = null; let pendingPosition = null;
  const controller = createSurveyController({id: root.dataset.surveyId, status: root.dataset.status,
    nextSequence: root.dataset.nextSequence,
    geolocation: navigator.geolocation, onStatus: (message) => { quality.textContent = message; }, onCaptureStart:startClock, onCaptureStop:stopClock,
    onPosition:(position)=>{pendingPosition=position;fieldMap?.updatePosition(position);},
    onBatch: (counts) => { document.querySelector("#survey-raw").textContent=counts.raw; document.querySelector("#survey-usable").textContent=counts.usable; document.querySelector("#survey-rejected").textContent=counts.rejected; fieldMap?.updateTrace(counts.trace); },
    send: async (samples) => { const response = await fetch(root.dataset.sampleUrl, {method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrf()}, body: JSON.stringify({samples})});
      if (!response.ok) throw new Error("Upload failed"); return response.json(); }});
  if (root.dataset.status === "ACTIVE") {
    quality.textContent = "Survey was interrupted. Select Begin GPS capture to restart location collection.";
    // ACTIVE persisted state is deliberately not enough to restart browser geolocation.
  }
  window.addEventListener("online", () => controller.flush());
  window.addEventListener("pagehide", () => controller.stop());
  document.querySelector("#begin-gps")?.addEventListener("click", () => controller.start());
  let lifecycleApproved = false;
  const actionsForm = document.querySelector("#survey-actions");
  const lifecycleGate = createLifecycleSubmissionGate({
    synchronize: async () => {
      await controller.ready;
      const synchronized = await controller.flush();
      return Boolean(synchronized && !controller.bufferSize);
    },
    onBusy: () => actionsForm?.querySelectorAll('button[name="action"]').forEach((button)=>{button.disabled=true;}),
    onBlocked: () => {
      actionsForm?.querySelectorAll('button[name="action"]').forEach((button)=>{button.disabled=false;});
      quality.textContent = "Pending survey evidence must synchronize before changing the survey state.";
    },
    submit: (action) => {
      lifecycleApproved = true;
      const actionInput = document.createElement("input");
      actionInput.type = "hidden"; actionInput.name = "action"; actionInput.value = action;
      actionsForm.append(actionInput);
      actionsForm.requestSubmit();
    },
  });
  actionsForm?.addEventListener("submit", (event) => {
    controller.stop();
    if (lifecycleApproved) return;
    event.preventDefault();
    const action = event.submitter?.value;
    if (action) void lifecycleGate.request(action);
  });
  const fieldMapElement=document.querySelector("#survey-field-map");
  const reviewMapElement=document.querySelector("#survey-review-map");
  const mapElement=fieldMapElement || reviewMapElement;
  if(mapElement){const network=JSON.parse(document.querySelector("#survey-network-data").textContent);const trace=JSON.parse(document.querySelector("#survey-trace-data").textContent);import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl)=>{if(fieldMapElement){fieldMap=createFieldMap({maplibregl,element:fieldMapElement,statusElement:document.querySelector("#survey-map-status"),network,trace});if(pendingPosition)fieldMap.updatePosition(pendingPosition);}else{createReviewMap({maplibregl,element:reviewMapElement,statusElement:document.querySelector("#survey-map-status"),network,trace});}}).catch(()=>{mapElement.dataset.state="error";document.querySelector("#survey-map-status").textContent=fieldMapElement?"The field map could not load. GPS recording and evidence synchronization remain available.":"The evidence map could not load. Persisted review evidence remains available below.";});}
}
