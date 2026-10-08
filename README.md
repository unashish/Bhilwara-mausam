# भीलवाड़ा मौसम (Bhilwara Mausam)

A free, simple Hindi weather site for farmers in Bhilwara district, Rajasthan.
For each tehsil it shows, for the next 7 days:

- **हाँ / नहीं** — will it rain? (green = yes, red = no)
- **बारिश का मौका** — chance of rain in %
- **कितनी / कब** — how much rain, and at what time of day
- **दिन / रात** — day and night temperature
- **सावधान** — warnings for heavy rain, heat, cold/frost and strong wind
- **सुनें** — the phone reads the forecast aloud in Hindi

Everything is free: the data (ECMWF open data), the computer that updates it
(GitHub Actions) and the hosting (GitHub Pages).

## How it works

```
ECMWF open data ──► GitHub Action (twice a day) ──► pipeline/ (Python)
                                                        │
                    farmer's phone ◄── GitHub Pages ◄── docs/forecast.json
```

1. `pipeline/fetch.py` downloads the newest 00 or 12 UTC run of the ECMWF IFS:
   - **Ensemble (51 members):** accumulated rain at each day boundary.
   - **High-resolution run:** 2 m temperature, 10 m wind and rain every 3–6 h.
2. `pipeline/process.py` reads each field at every tehsil centre and works out:
   - **Chance of rain** = share of the 51 members with at least 2.5 mm that day
     (IMD's rainy-day threshold). 50% or more shows **हाँ**.
   - **How much** = median of the members that do rain, as an IMD category
     (हल्की, मध्यम, भारी…) with a likely range in mm.
   - **When** = the ~6 hour window with the most rain in the high-res run.
   - **Day/night temperature** and **warnings** from the rules in `pipeline/config.py`.
   - Days run midnight to midnight India time.
3. The result is one small file, `docs/forecast.json`, all text already in Hindi.
4. `docs/index.html` reads that file and draws the tehsil boxes. It works on
   cheap phones, keeps the last forecast for offline use, and can be added to
   the home screen like an app.

## Setup (one time)

1. **Settings → Pages → Build and deployment → Source: "GitHub Actions".**
2. **Actions → Daily forecast → Run workflow** to build the first forecast.
3. The site is at `https://<your-username>.github.io/bhilwara-mausam/`.

After that it updates by itself at about 05:00 and 16:00 IST.

## Change things

| What | Where |
|---|---|
| Add/move a tehsil, change its box position | `TEHSILS` in `pipeline/config.py` |
| Rain/heat/cold/wind thresholds | `pipeline/config.py` |
| Any Hindi wording or warning advice | `pipeline/hindi.py` |
| Colours, layout | `docs/index.html` (`:root` colours at the top) |

## Test without internet access to ECMWF

```bash
pip install -r requirements.txt
python -m tests.make_fake_grib raw_test          # fake ECMWF-like files
python -m pipeline.run --skip-fetch --raw raw_test --out docs/forecast.json
cd docs && python -m http.server 8000             # open http://localhost:8000
```

## Data and licence

Forecast data: adapted from ECMWF IFS ensemble and high-resolution open data
by ECMWF, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
available at <https://data.ecmwf.int/forecasts/>. ECMWF does not endorse this
site. Warnings are our own estimate, not official IMD warnings — always follow
[IMD](https://mausam.imd.gov.in/) for official alerts.

Tehsil centre points were derived from 2011 sub-district boundaries.
