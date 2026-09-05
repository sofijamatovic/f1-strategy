# Pitwall — F1 Race Strategy & Telemetry Dashboard

An interactive Streamlit dashboard built on official Formula 1 timing data (via [FastF1](https://github.com/theOehrly/Fast-F1)) for tyre-degradation analysis, pit-strategy simulation, and session results — for any Grand Prix from 2018 onward.

**Live demo:** https://f1-strategy-pj2t.onrender.com
*(hosted on Render's free tier — the app spins down after inactivity, so the first load after a while can take 30–60s to wake up)*

## What it does

- **Telemetry & Degradation** — per-stint tyre degradation, with a fuel-corrected regression that separates tyre wear from the fuel-burn effect that otherwise masks it in raw lap times
- **Qualifying breakdown** — Q1/Q2/Q3 pace per driver, showing only the segments they actually reached
- **Pit Strategy Simulator** — undercut/overcut "what-if" tool: estimates the time delta of pitting on a different lap, based on the driver's actual stint degradation slope
- **Head-to-Head Pace** — lap-by-lap pace delta between two drivers
- **Session Results** — final classification for races, qualifying, and sprints; best-lap ranking for practice sessions (which aren't officially classified)
- **Championship Standings** — current Drivers' and Constructors' standings (via the [Ergast API](https://ergast.com/mrd/))

## Why

Built to practice the kind of tooling a race strategy/engineering team actually uses: pulling real timing data, turning it into a degradation model, and using that model to answer a concrete strategic question ("would pitting 3 laps earlier have gained us anything?") — rather than a generic data-visualization exercise.

## Tech stack

Python · Streamlit · [FastF1](https://github.com/theOehrly/Fast-F1) · Plotly · pandas · NumPy

## Design notes

A few decisions worth knowing about if you're reading the code:

- **Fuel-corrected degradation, everywhere.** Raw lap times get faster over a stint from fuel burn-off even while the tyres are wearing out — on a normal stint those two effects can roughly cancel, making the *raw* lap-time trend look almost flat. Both the degradation view and the pit-strategy simulator apply a fuel-correction term before fitting the degradation slope, so the number reflects tyre wear specifically, not the combination of both effects.
- **The pit simulator is a clean-air estimate, not a full race simulator.** It doesn't model traffic, Safety Car resets, or a different rejoin gap — it answers "how much faster/slower would this stint's tyres have been on a different pit lap," not "where would this driver have finished." `pit_loss_seconds` is reported for context but cancels out of the delta, since both the actual and simulated scenario involve exactly one pit stop.
- **`session.load(telemetry=False)`.** FastF1's telemetry/position channels (per-car speed, throttle, GPS at high frequency) are by far the largest part of a session's data, and nothing in this app uses them — every view is built from laps, weather, race control messages, and results. Turning telemetry loading off was the fix for an out-of-memory crash on free-tier deployment (Streamlit Community Cloud and Render both have tight RAM limits).
- **Standings team colours are a static reference map**, not live data — the Ergast API (unlike FastF1's own session results) doesn't return team colours, so `TEAM_COLOR_FALLBACK` in `app.py` is a best-effort lookup for recent-era teams, not something pulled from the API itself.

## Known limitations

- Practice session "results" are a best-clean-lap ranking, not an official classification (none exists for practice)
- The pit-strategy model assumes a single pit stop in both compared scenarios
- Team colours in the Standings view won't be accurate for older/renamed teams not in the fallback map

## Running locally

```bash
git clone https://github.com/sofijamatovic/f1-strategy.git
cd f1-strategy
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
python -m unittest discover tests
```# f1-strategy
