import { createEntrancePointSelector } from "./entrance-point-selector.js?v=p4s2-owner-correction-1";

const element = document.querySelector("#entrance-map");
const latitudeInput = document.querySelector("#id_latitude");
const longitudeInput = document.querySelector("#id_longitude");
const statusElement = document.querySelector("#entrance-map-status");

async function start() {
  if (!element || !latitudeInput || !longitudeInput || !statusElement) return;
  try {
    const maplibregl = await import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs");
    createEntrancePointSelector({ element, latitudeInput, longitudeInput, statusElement, maplibregl });
  } catch (error) {
    console.error("Entrance map selector failed to initialize", error);
    element.dataset.state = "error";
    statusElement.textContent = "The entrance map could not load. Refresh and try again before saving.";
    statusElement.setAttribute("role", "alert");
  }
}

start();
