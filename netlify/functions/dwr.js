/**
 * Netlify Function: dwr
 *
 * Proxies California DWR 2023 Statewide Crop Mapping queries.
 * Accepts ?lat=&lng=, builds an ArcGIS point-in-polygon query,
 * and forwards the JSON response to the browser.
 *
 * Local dev equivalent: server.py proxy_dwr()
 */

const DWR_QUERY_URL =
  "https://utility.arcgis.com/usrsvcs/servers/d94e891e00364e49a2ed9e9e2e27837d" +
  "/rest/services/Planning/i15_Crop_Mapping_2023/MapServer/0/query";

export default async (req) => {
  const url    = new URL(req.url);
  const params = url.searchParams;

  const lat = parseFloat(params.get("lat"));
  const lng = parseFloat(params.get("lng"));

  if (isNaN(lat) || isNaN(lng)) {
    return new Response("Missing or invalid lat/lng params", { status: 400 });
  }

  const arcgisParams = new URLSearchParams({
    geometry:     `${lng},${lat}`,
    geometryType: "esriGeometryPoint",
    inSR:         "4326",
    spatialRel:   "esriSpatialRelIntersects",
    outFields:    "*",
    returnGeometry: "false",
    f:            "json",
  });

  const target = `${DWR_QUERY_URL}?${arcgisParams}`;
  console.log(`[dwr] → ${target}`);

  try {
    const upstream = await fetch(target, {
      headers: {
        "User-Agent": "FarmRoadTrip/1.0",
        "Referer":    "https://www.arcgis.com/",
      },
    });
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("[dwr] upstream error:", err);
    return new Response(err.message, { status: 502 });
  }
};

export const config = { path: "/dwr/query" };
