#!/usr/bin/env python3
"""
Local dev server for Farm Road Trip.
Serves static files from ./src/ and proxies CropScape API requests,
converting WGS84 lat/lng → EPSG:5070 (Albers) before forwarding.

Usage:
    python3 server.py
Then open: http://localhost:3000
"""

import http.server
import urllib.request
import urllib.parse
import math
from functools import partial

PORT = 3000
STATIC_DIR = "src"
CROPSCAPE_BASE = "https://nassgeodata.gmu.edu/axis2/services/CDLService"
DWR_BASE = "https://utility.arcgis.com/usrsvcs/servers/d94e891e00364e49a2ed9e9e2e27837d/rest/services/Planning/i15_Crop_Mapping_2023/MapServer/0/query"


def wgs84_to_epsg5070(lat_deg, lon_deg):
    """
    Convert WGS84 lat/lng to EPSG:5070 (NAD83 / Conus Albers) x/y in meters.
    CropScape's CDL raster is in this projection — coordinates must be converted
    before querying GetCDLValue.

    Implements the ellipsoidal Albers Equal Area Conic formula.
    Reference: https://pubs.usgs.gov/pp/1395/report.pdf (Snyder, 1987)
    """
    # GRS80 ellipsoid (NAD83 uses GRS80)
    a  = 6378137.0
    f  = 1 / 298.257222101
    e2 = 2*f - f**2
    e  = math.sqrt(e2)

    # EPSG:5070 projection parameters
    phi1 = math.radians(29.5)   # first standard parallel
    phi2 = math.radians(45.5)   # second standard parallel
    phi0 = math.radians(23.0)   # latitude of origin
    lam0 = math.radians(-96.0)  # central meridian

    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)

    def m(p):
        return math.cos(p) / math.sqrt(1 - e2 * math.sin(p)**2)

    def q(p):
        s = math.sin(p)
        return (1 - e2) * (s / (1 - e2*s**2) - (1/(2*e)) * math.log((1 - e*s) / (1 + e*s)))

    m1, m2 = m(phi1), m(phi2)
    q0, q1, q2, qp = q(phi0), q(phi1), q(phi2), q(phi)

    n    = (m1**2 - m2**2) / (q2 - q1)
    C    = m1**2 + n * q1
    rho0 = a * math.sqrt(C - n * q0) / n
    rho  = a * math.sqrt(C - n * qp) / n
    theta = n * (lam - lam0)

    x = rho  * math.sin(theta)
    y = rho0 - rho * math.cos(theta)
    return x, y


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/cropscape/"):
            self.proxy_cropscape()
        elif self.path.startswith("/dwr/query"):
            self.proxy_dwr()
        else:
            super().do_GET()

    def proxy_cropscape(self):
        # Parse incoming request (frontend sends WGS84 x=lng, y=lat)
        parsed   = urllib.parse.urlparse(self.path)
        endpoint = parsed.path[len("/cropscape"):]   # e.g. /GetCDLValue
        params   = urllib.parse.parse_qs(parsed.query)

        try:
            lng = float(params["x"][0])
            lat = float(params["y"][0])
            albers_x, albers_y = wgs84_to_epsg5070(lat, lng)
        except (KeyError, ValueError, IndexError) as e:
            self._send_text(400, f"Bad coords: {e}")
            return

        # Rebuild query with projected coordinates
        new_params = {k: v[0] for k, v in params.items()}
        new_params["x"] = f"{albers_x:.2f}"
        new_params["y"] = f"{albers_y:.2f}"
        target = CROPSCAPE_BASE + endpoint + "?" + urllib.parse.urlencode(new_params)

        print(f"[proxy] WGS84 ({lat:.5f}, {lng:.5f}) → Albers ({albers_x:.0f}, {albers_y:.0f})")
        print(f"[proxy] → {target}")

        try:
            req = urllib.request.Request(target, headers={"User-Agent": "FarmRoadTrip/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "text/xml"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                print(f"[proxy] ✓ response: {body.decode()[:120]}")
        except Exception as e:
            print(f"[proxy] ✗ error: {e}")
            self._send_text(502, str(e))

    def proxy_dwr(self):
        # Forward to California DWR ArcGIS service, injecting lat/lng from our
        # simple ?lat=&lng= params and building the full ArcGIS query string.
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        try:
            lat = float(params["lat"][0])
            lng = float(params["lng"][0])
        except (KeyError, ValueError, IndexError) as e:
            self._send_text(400, f"Bad coords: {e}")
            return

        arcgis_params = urllib.parse.urlencode({
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json",
        })
        target = f"{DWR_BASE}?{arcgis_params}"
        print(f"[dwr]   → {target}")
        try:
            req = urllib.request.Request(target, headers={
                "User-Agent": "FarmRoadTrip/1.0",
                "Referer": "https://www.arcgis.com/",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                print(f"[dwr]   ✓ {len(body)} bytes")
        except Exception as e:
            print(f"[dwr]   ✗ {e}")
            self._send_text(502, str(e))

    def _send_text(self, code, msg):
        body = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silence default access logs; proxy calls print their own


if __name__ == "__main__":
    handler = partial(Handler, directory=STATIC_DIR)
    with http.server.HTTPServer(("", PORT), handler) as httpd:
        print(f"🌾 Farm Road Trip → http://localhost:{PORT}")
        print(f"   Proxy: /cropscape/* → {CROPSCAPE_BASE}/* (WGS84→Albers conversion enabled)")
        print("   Press Ctrl+C to stop.\n")
        httpd.serve_forever()
