import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { createElapsedClock, createLifecycleSubmissionGate, createReviewMap, createSurveyController, formatDuration, qualityFor, shouldRecord, traceFeature } from "../../static/yct_map/js/path-survey.js";

test("accuracy bands are explicit and no non-active state records", () => {
  assert.equal(qualityFor(8).classification, "ACCEPTED");
  assert.equal(qualityFor(40).classification, "WEAK");
  assert.equal(qualityFor(70).classification, "REJECTED");
  assert.equal(shouldRecord("ACTIVE"), true);
  for (const state of ["DRAFT","PAUSED","COMPLETED","REVIEWED","ABANDONED"]) assert.equal(shouldRecord(state), false);
});

test("survey module uses IndexedDB and does not auto-start an interrupted survey", () => {
  const source = readFileSync(new URL("../../static/yct_map/js/path-survey.js", import.meta.url), "utf8");
  assert.match(source, /indexedDB\.open/);
  assert.doesNotMatch(source, /if \(root\.dataset\.status === "ACTIVE"\)\s*controller\.start/);
  assert.match(source, /#begin-gps/);
});

test("active clock advances only while explicitly running and resumes accumulated time", () => {
  let callback; let time=1_000; const rendered=[];
  const clock=createElapsedClock({initial:4,onTick:(value)=>rendered.push(value),now:()=>time,
    setTimer:(fn)=>{callback=fn;return 1;},clearTimer:()=>{callback=null;}});
  clock.start(); time=6_500; callback(); assert.equal(clock.seconds,9);
  clock.stop(); assert.equal(callback,null); assert.equal(clock.seconds,9);
  time=10_000; clock.start(); time=13_200; callback(); assert.equal(clock.seconds,12);
  assert.equal(formatDuration(clock.seconds),"0:12"); assert.deepEqual(rendered,[4,9,9,12]);
});

test("survey capture waits for the private buffer and continues sequence numbers safely", async () => {
  let releaseBuffer; let watchCallback; let watchCount=0; const batches=[]; const stored=[];
  const geolocation={watchPosition(callback){watchCallback=callback;watchCount+=1;return 7;},clearWatch(){}};
  const controller=createSurveyController({id:"survey-1",status:"ACTIVE",nextSequence:0,geolocation,
    onStatus(){},loadBuffered:()=>new Promise((resolve)=>{releaseBuffer=resolve;}),
    storeBuffered:async (_id,items)=>{stored.push(items.map((item)=>item.sequence));},
    send:async (items)=>{batches.push(items.map((item)=>item.sequence));return {raw:items.length,usable:items.length,rejected:0,trace:[]};}});
  assert.equal(controller.start(),true);
  assert.equal(watchCount,0,"GPS must not start before pending evidence is loaded");
  await Promise.resolve();
  releaseBuffer([{sequence:4,captured_at:"2026-09-25T10:00:00.000Z",latitude:6.518,longitude:3.374,accuracy:8}]);
  await controller.ready;
  assert.equal(watchCount,1);
  watchCallback({timestamp:Date.parse("2026-09-25T10:00:01.000Z"),coords:{latitude:6.518,longitude:3.37401,accuracy:8,speed:null,heading:null}});
  await new Promise((resolve)=>setTimeout(resolve,0));
  await controller.flush();
  assert.deepEqual(batches,[[4],[5]]);
  assert.ok(stored.some((items)=>items.length===0));
});

test("counter UI consumes authoritative raw usable and rejected totals", () => {
  const source=readFileSync(new URL("../../static/yct_map/js/path-survey.js",import.meta.url),"utf8");
  assert.match(source,/counts\.raw/); assert.match(source,/counts\.usable/); assert.match(source,/counts\.rejected/);
});

test("field trace renders only synchronized usable coordinates", () => {
  assert.deepEqual(traceFeature([[3.374,6.518]]),{type:"FeatureCollection",features:[]});
  assert.deepEqual(traceFeature([[3.374,6.518],[3.3742,6.5181]]).geometry.coordinates,
    [[3.374,6.518],[3.3742,6.5181]]);
  const source=readFileSync(new URL("../../static/yct_map/js/path-survey.js",import.meta.url),"utf8");
  assert.match(source,/updateTrace\(counts\.trace\)/);
  assert.match(source,/GPS recording and evidence synchronization remain available/);
  assert.match(source,/Pending survey evidence must synchronize before changing the survey state/);
});

test("lifecycle gate coalesces delayed duplicate finish taps", async () => {
  let release; let synchronizations=0; const submissions=[]; const busy=[];
  const gate=createLifecycleSubmissionGate({
    synchronize:()=>{synchronizations+=1;return new Promise((resolve)=>{release=resolve;});},
    submit:(action)=>submissions.push(action), onBusy:(action)=>busy.push(action),
  });
  const first=gate.request("finish");
  const second=gate.request("finish");
  await Promise.resolve();
  assert.equal(synchronizations,1);
  release(true);
  assert.equal(await first,true); assert.equal(await second,true);
  assert.deepEqual(submissions,["finish"]); assert.deepEqual(busy,["finish"]);
});

test("completed review map uses independent read-only evidence sources", () => {
  const handlers={}; const sources=[]; const layers=[];
  class Bounds { extend(){return this;} }
  class Map { on(name,callback){handlers[name]=callback;} addSource(id,config){sources.push([id,config]);}
    addLayer(layer){layers.push(layer);} fitBounds(){} resize(){} }
  const element={dataset:{}}; const statusElement={textContent:""};
  createReviewMap({maplibregl:{Map,LngLatBounds:Bounds},element,statusElement,
    network:{type:"FeatureCollection",features:[{type:"Feature",properties:{match_classification:"STRONG"},geometry:{type:"LineString",coordinates:[[3.374,6.518],[3.375,6.518]]}}]},
    trace:[[3.374,6.518],[3.3745,6.518]]});
  handlers.load();
  assert.deepEqual(sources.map(([id])=>id),["survey-review-network","survey-review-trace"]);
  assert.deepEqual(layers.map((layer)=>layer.id),["survey-review-network-unmatched","survey-review-network-candidates","survey-review-trace"]);
  assert.match(statusElement.textContent,/Read-only evidence overview ready/);
});
