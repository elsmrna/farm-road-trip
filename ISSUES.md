# Issues — Farm Road Trip

> Lightweight issue tracker. Format: `## #N — Title` with Status, Priority, and notes.
> Statuses: `open` · `in progress` · `done` · `blocked`

---

## #1 — Bootstrap single-file HTML prototype
**Status:** done ✅  
**Priority:** high  
**Type:** feature

`src/index.html` created — dark-themed Leaflet map, click-to-query, GPS button, road trip mode (watchPosition). All crop logic inline in the single file. Also closes #2, #3, #11 (see notes below).

---

## #2 — Build CropScape API client module
**Status:** done ✅ (inline in index.html for now)  
**Priority:** high  
**Type:** feature

Create `src/cropscape.js` with:
- `getCropAtPoint(lat, lng, year?)` → returns `{ code, name }` 
- `getCropsInBoundingBox(lat, lng, radiusMiles)` → samples a grid of points and returns unique crops found
- Error handling for non-crop codes (water, developed land, etc.)
- Caching layer to avoid redundant requests while driving

Reference: https://nassgeodata.gmu.edu/CropScape/devhelp/help.html

---

## #3 — Build CDL crop code lookup table
**Status:** done ✅ (inline in index.html as CROP_CODES object)  
**Priority:** high  
**Type:** feature

Create `src/crop-codes.js` mapping all 256 CDL codes to:
- Human-readable name (e.g. `1 → "Corn"`)
- Category (grain, vegetable, fruit, oilseed, fallow, non-crop)
- Emoji or icon identifier
- Fun fact string (optional, can seed with a few)

Source: https://www.nass.usda.gov/Research_and_Science/Cropland/docs/cdl_codes_colors.xlsx

---

## #4 — Swap Leaflet for Google Maps
**Status:** open  
**Priority:** medium  
**Type:** feature  
**Blocked by:** #1

Once prototype is working, migrate the map layer to Google Maps JS API for:
- Better mobile UX and satellite view
- Street View integration (fun to see the actual fields)
- Directions API for road trip routing later

Requires: Google Maps API key, Maps JS API enabled in Cloud Console.

---

## #5 — Add geolocation tracking (road trip mode)
**Status:** open  
**Priority:** high  
**Type:** feature  
**Blocked by:** #1, #2

Use `navigator.geolocation.watchPosition()` to continuously update location while driving. Debounce queries to CropScape so we're not hammering the API — trigger a new lookup only when position changes by >0.1 miles.

Show a "You're driving through: Corn fields" toast as crops change.

---

## #6 — Design crop info panel / sidebar
**Status:** open  
**Priority:** medium  
**Type:** feature / UX

When a crop is identified, show a panel with:
- Crop name + emoji
- What it's used for (food, fuel, fiber, etc.)
- Typical harvest season
- Fun trivia ("Iowa grows 25% of US corn")

Decide: sidebar panel vs. bottom sheet vs. map popup.

---

## #7 — Integrate OpenFarm API for crop enrichment
**Status:** open  
**Priority:** low  
**Type:** feature  
**Blocked by:** #6

Query `https://openfarm.cc/api/v1/crops?q={crop_name}` to pull in richer crop descriptions and images. Cache results by crop name (only ~100 distinct crops will ever appear).

---

## #8 — Handle non-crop CDL codes gracefully
**Status:** open  
**Priority:** medium  
**Type:** bug / UX

CDL codes 110-195 are non-agricultural (water, forests, developed land). Currently these would show raw codes or "Unknown". Handle them with friendly messages:
- Water → "You're near a river or lake"
- Developed → "Urban area — no crops here"
- Forest → "Woodland / timberland"

---

## #9 — Mobile layout and PWA support
**Status:** open  
**Priority:** medium  
**Type:** feature

Road trips happen on phones. Optimize for mobile:
- Full-screen map with minimal chrome
- Large tap targets for the crop info panel
- Add a `manifest.json` and service worker so it can be installed as a PWA (works offline with cached crop code data)

---

## #10 — Add a "What's around me?" bounding box view
**Status:** open  
**Priority:** medium  
**Type:** feature  
**Blocked by:** #2

Show not just the crop at your exact location, but all distinct crops within a ~5-mile radius. Render as a small legend card in the corner of the map: "Nearby: 🌽 Corn, 🌱 Soybeans, 🌾 Winter Wheat".

Sampling strategy: query a 3x3 or 5x5 grid around current position, deduplicate results.

---

## #11 — Test CropScape API CORS behavior
**Status:** open — needs live browser test  
**Priority:** high  
**Type:** investigation

The prototype detects CORS failures and shows a warning banner + helpful message when blocked. Open `src/index.html` via `npx serve src/` (not `file://`) and click a US farm region to confirm the API responds.

If CORS is blocked from a browser, add a Cloudflare Worker proxy:
```js
// workers.dev — just forward the request
fetch("https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue" + url.search)
```

---

## #12 — Decide on hosting and deployment
**Status:** open  
**Priority:** low  
**Type:** ops

Options:
- GitHub Pages (free, static, custom domain support)
- Netlify (free tier, better for adding serverless functions if #11 requires a proxy)
- Vercel (same as Netlify)

Recommendation: start with Netlify so we have the option of adding a proxy without changing the setup.

---

## Completed

- **#1** Bootstrap single-file HTML prototype — `src/index.html` with Leaflet, CropScape, GPS + road trip mode
- **#2** CropScape API client — inline in prototype (`queryCropScape`, `getCropAt` with caching)
- **#3** CDL crop code lookup table — 100+ codes with emoji, category, and fun fact
