/**
 * Netlify Function: cropscape
 *
 * Proxies USDA CropScape GetCDLValue requests, converting WGS84 lat/lng
 * (sent by the browser as x=lng&y=lat) to EPSG:5070 (Albers) before
 * forwarding to the USDA API.
 *
 * Local dev equivalent: server.py proxy_cropscape()
 */

const CROPSCAPE_BASE = "https://nassgeodata.gmu.edu/axis2/services/CDLService";

// ── Albers Equal Area Conic projection (EPSG:5070 / NAD83 Conus Albers) ──
// Ported from server.py. Reference: Snyder (1987), USGS PP-1395.
function wgs84ToEpsg5070(latDeg, lonDeg) {
  const a  = 6378137.0;               // GRS80 semi-major axis (m)
  const f  = 1 / 298.257222101;       // GRS80 flattening
  const e2 = 2*f - f*f;
  const e  = Math.sqrt(e2);

  const toRad = d => d * Math.PI / 180;

  const phi1 = toRad(29.5);   // first standard parallel
  const phi2 = toRad(45.5);   // second standard parallel
  const phi0 = toRad(23.0);   // latitude of origin
  const lam0 = toRad(-96.0);  // central meridian

  const phi = toRad(latDeg);
  const lam = toRad(lonDeg);

  const m = p => Math.cos(p) / Math.sqrt(1 - e2 * Math.sin(p)**2);
  const q = p => {
    const s = Math.sin(p);
    return (1 - e2) * (s / (1 - e2*s*s) - (1/(2*e)) * Math.log((1 - e*s) / (1 + e*s)));
  };

  const m1 = m(phi1), m2 = m(phi2);
  const q0 = q(phi0), q1 = q(phi1), q2 = q(phi2), qp = q(phi);

  const n    = (m1*m1 - m2*m2) / (q2 - q1);
  const C    = m1*m1 + n*q1;
  const rho0 = a * Math.sqrt(C - n*q0) / n;
  const rho  = a * Math.sqrt(C - n*qp) / n;
  const theta = n * (lam - lam0);

  return { x: rho * Math.sin(theta), y: rho0 - rho * Math.cos(theta) };
}

export default async (req) => {
  const url    = new URL(req.url);
  const params = url.searchParams;

  const lngRaw = params.get("x");
  const latRaw = params.get("y");
  const year   = params.get("year") || "2024";

  const lng = parseFloat(lngRaw);
  const lat = parseFloat(latRaw);

  if (isNaN(lat) || isNaN(lng)) {
    return new Response("Missing or invalid x/y params", { status: 400 });
  }

  const { x, y } = wgs84ToEpsg5070(lat, lng);
  const target = `${CROPSCAPE_BASE}/GetCDLValue?year=${year}&x=${x.toFixed(2)}&y=${y.toFixed(2)}`;

  console.log(`[cropscape] WGS84 (${lat.toFixed(5)}, ${lng.toFixed(5)}) → Albers (${x.toFixed(0)}, ${y.toFixed(0)})`);

  try {
    const upstream = await fetch(target, {
      headers: { "User-Agent": "FarmRoadTrip/1.0" },
    });
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: { "Content-Type": "text/xml" },
    });
  } catch (err) {
    console.error("[cropscape] upstream error:", err);
    return new Response(err.message, { status: 502 });
  }
};

export const config = { path: "/cropscape/*" };
