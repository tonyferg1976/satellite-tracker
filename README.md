# Satellite tracker: who owns orbit

A 3D globe of every working satellite, coloured by the country or organisation that owns it, with orbit tracks and checkbox filters.

**Live site:** https://tonyferg1976.github.io/satellite-tracker/

## How it works

- `index.html` is the whole app (WebGL globe, orbit maths, filters). No build step.
- `scripts/update_data.py` downloads CelesTrak's active-satellite orbits and the SATCAT owner catalogue, keeps working payloads only, splits Starlink out from other US satellites, and writes `data/sats.json`.
- `.github/workflows/update-data.yml` runs that script every 6 hours, commits the new data, and deploys the site to GitHub Pages. You can also run it by hand from the **Actions** tab ("Run workflow").

Positions are computed in the browser from the orbital elements (Kepler orbit with J2 drift), which is accurate to a few tens of kilometres for several days after the data date.

Data: [CelesTrak](https://celestrak.org) (GP data and SATCAT). Please respect CelesTrak's usage policy; the schedule here downloads each file at most four times a day.
