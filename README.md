# 🌾 Farm Road Trip

> An interactive map that shows what crops are being grown around you as you drive through the US.

## What It Does

Point your phone at any road in America and see a live overlay of what's growing in the surrounding fields — corn, soybeans, almonds, vineyards, wheat, and 100+ other crop types — powered by USDA satellite data.

---

## Data Sources

### USDA Cropland Data Layer (CDL) via CropScape
- **What it is:** Annual, satellite-derived crop map of the entire continental US
- **Resolution:** 10 meters (as of 2024)
- **Coverage:** 100+ crop types, updated every year
- **API:** Free, no auth key required
- **Docs:** https://nassgeodata.gmu.edu/CropScape/devhelp/help.html

Query example (returns crop type at a lat/lng):
```
GET https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue?year=2025&x=-93.5&y=41.8
```

### Google Maps JavaScript API
- Map display, tile rendering, and GPS location
- Requires a Maps API key from Google Cloud Console
- Used for: map tiles, geolocation, marker/overlay rendering

### OpenFarm API (optional enrichment)
- Crop descriptions, growing info, images
- https://openfarm.cc/api/v1/crops?q={crop_name}

---

## Architecture

```
Browser (GPS) → Current lat/lng
      ↓
CropScape REST API → Crop type at location
      ↓
Crop name + code
      ↓
Google Maps overlay → Marker / info panel
      ↓
(optional) OpenFarm API → Crop description + image
```

### Key Flow
1. On page load, get user's GPS coordinates via `navigator.geolocation`
2. As location updates (road trip mode), query CropScape for crop at current coords
3. Also query a bounding box around current location to show nearby crops
4. Render results as map markers or a color-coded overlay on the map
5. Tap a marker to see crop name, description, and fun facts

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Map | Google Maps JS API | Can swap for Leaflet + OpenStreetMap (no key needed) |
| Crop data | USDA CropScape REST API | Free, no auth |
| Enrichment | OpenFarm API | Free, no auth |
| Frontend | Vanilla JS + HTML | Single-file to start; can grow into React |
| Hosting | GitHub Pages / Netlify | Static site, no backend needed |

---

## Project Structure

```
farm-road-trip/
├── README.md
├── ISSUES.md
├── public/
│   └── icons/          # Crop emoji / SVG icons
├── src/
│   ├── index.html      # Main app entry point
│   ├── app.js          # Core app logic
│   ├── cropscape.js    # CropScape API client
│   ├── openfarm.js     # OpenFarm API client (optional)
│   └── crop-codes.js   # CDL crop code → name mapping
└── docs/
    └── cdl-crop-codes.md   # Reference: all 256 CDL crop codes
```

---

## Getting Started

### Prerequisites
- A Google Maps API key (get one at https://console.cloud.google.com)
- A modern browser with geolocation support

### Running locally
```bash
# No build step needed — just open the HTML file
open src/index.html

# Or serve with any static server
npx serve src/
```

### API Key Setup
In `src/index.html`, replace:
```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_KEY_HERE"></script>
```

---

## CDL Crop Codes (Key Examples)

| Code | Crop |
|---|---|
| 1 | Corn |
| 2 | Cotton |
| 3 | Rice |
| 4 | Sorghum |
| 5 | Soybeans |
| 6 | Sunflower |
| 21 | Barley |
| 22 | Durum Wheat |
| 23 | Spring Wheat |
| 24 | Winter Wheat |
| 27 | Rye |
| 28 | Oats |
| 36 | Alfalfa |
| 61 | Fallow/Idle Cropland |
| 66 | Cherries |
| 67 | Peaches |
| 68 | Apples |
| 69 | Grapes |
| 72 | Almonds |
| 75 | Pecans |
| 77 | Potatoes |
| 204 | Pistachios |
| 211 | Olives |

Full code list: https://www.nass.usda.gov/Research_and_Science/Cropland/docs/cdl_codes_colors.xlsx

---

## Notes & Constraints

- CropScape API returns **raster pixel values** — you're querying a satellite image, not a farm registry. Accuracy is high (~85-95%) but not perfect.
- Data is updated **annually** (2025 CDL released Feb 2026). Not real-time.
- Urban/suburban areas return non-crop codes (open water, developed land, etc.) — handle gracefully.
- The API uses **EPSG:4326** (standard lat/lng) — pass coordinates directly.
- No CORS issues — CropScape supports cross-origin requests.
