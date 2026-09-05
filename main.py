import os
import fastf1
import pandas as pd
import numpy as np

# Create cache directory if it doesn't exist and enable cache
if not os.path.exists('cache_dir'):
    os.makedirs('cache_dir')
fastf1.Cache.enable_cache('cache_dir')


class F1StrategyEngine:
    """
    Comprehensive F1 Race Strategy and Telemetry Analytics Engine.
    Handles tyre degradation, fuel mass corrections, competitor gap analysis,
    Safety Car/VSC event extraction, and Undercut/Overcut 'What-If' simulations.
    """

    def __init__(self, year: int, grand_prix: str, session_type: str = 'R'):
        self.year = year
        self.grand_prix = grand_prix
        self.session_type = session_type
        self.session = None
        self.laps = None
        self.clean_laps = None
        self.weather = None
        self.race_control = None
        self._load_data()

    def _load_data(self):
        """Fetches, cleans, and structures FastF1 session data.

        telemetry=False: none of this engine's methods touch car telemetry
        or position data (session.car_data / session.pos_data) — only laps,
        weather, race control messages and results. Telemetry channels are
        by far the largest part of a FastF1 session (high-frequency
        per-car data for the whole session duration), so this is almost
        certainly what was blowing past the free-tier memory limit on
        Streamlit Cloud / Render.
        """
        self.session = fastf1.get_session(self.year, self.grand_prix, self.session_type)
        self.session.load(telemetry=False)

        # Raw DataFrames
        self.laps = self.session.laps.copy()
        self.weather = self.session.weather_data.copy()
        self.race_control = self.session.race_control_messages.copy()

        # Convert lap duration to total seconds for arithmetic operations
        self.laps['LapTimeSeconds'] = self.laps['LapTime'].dt.total_seconds()

        # Filter clean laps (excludes in/out laps, SC periods, and telemetry anomalies)
        self.clean_laps = self.laps.pick_accurate().pick_wo_box()

    # -------------------------------------------------------------------------
    # 1. TYRE DEGRADATION & FUEL CORRECTION MODEL
    # -------------------------------------------------------------------------
    def analyze_tyre_degradation(self, fuel_effect_per_lap: float = 0.035):
        """
        Calculates lap time degradation per compound and stint.
        :param fuel_effect_per_lap: Estimated lap time reduction (seconds/lap) due to fuel burn.
        """
        results = []
        for (driver, stint, compound), group in self.clean_laps.groupby(['Driver', 'Stint', 'Compound']):
            if len(group) < 5 or pd.isna(compound):
                continue

            group = group.copy()
            group['FuelCorrectedLapTime'] = group['LapTimeSeconds'] + (group['LapNumber'] * fuel_effect_per_lap)

            x = group['LapNumber'].values
            y_raw = group['LapTimeSeconds'].values
            y_corrected = group['FuelCorrectedLapTime'].values

            raw_slope, _ = np.polyfit(x, y_raw, 1)
            corrected_slope, _ = np.polyfit(x, y_corrected, 1)

            results.append({
                'Driver': driver,
                'Stint': stint,
                'Compound': compound,
                'LapsInStint': len(group),
                'RawDegradation_sPerLap': float(round(raw_slope, 4)),
                'CorrectedDegradation_sPerLap': float(round(corrected_slope, 4))
            })
        return pd.DataFrame(results)

    # -------------------------------------------------------------------------
    # 2. SAFETY CAR & VSC DETECTION
    # -------------------------------------------------------------------------
    def get_safety_car_periods(self):
        """Extracts exact laps and timestamps corresponding to SC or VSC deployments.

        FIX: TrackStatus is a string of concatenated status codes (a lap can carry
        more than one, e.g. "26"), so exact-matching with .isin(['5','6']) misses
        composite entries — and '5' is actually Red Flag, not Safety Car. Per
        FastF1's own status codes: '4' = Safety Car, '6' = VSC Deployed,
        '7' = VSC Ending. This now uses Laps.pick_track_status(..., how='any'),
        FastF1's own composite-safe filter, with the correct codes.
        """
        sc_messages = self.race_control[
            self.race_control['Message'].str.contains('SAFETY CAR|VIRTUAL SAFETY CAR', case=False, na=False)
        ]
        sc_laps = self.laps.pick_track_status(['4', '6', '7'], how='any')[
            ['LapNumber', 'TrackStatus', 'Time']
        ].drop_duplicates()
        return sc_laps, sc_messages[['Time', 'Category', 'Message']]

    # -------------------------------------------------------------------------
    # 3. COMPETITOR PACE & GAP ANALYSIS
    # -------------------------------------------------------------------------
    def compare_driver_pace(self, driver_a: str, driver_b: str):
        """Generates a lap-by-lap pace and delta comparison between two drivers."""
        laps_a = self.clean_laps[self.clean_laps['Driver'] == driver_a][['LapNumber', 'LapTimeSeconds', 'Compound']]
        laps_b = self.clean_laps[self.clean_laps['Driver'] == driver_b][['LapNumber', 'LapTimeSeconds', 'Compound']]
        merged = pd.merge(laps_a, laps_b, on='LapNumber', suffixes=(f'_{driver_a}', f'_{driver_b}'))
        merged['PaceDelta_s'] = merged[f'LapTimeSeconds_{driver_b}'] - merged[f'LapTimeSeconds_{driver_a}']
        return merged

    # -------------------------------------------------------------------------
    # 4. WEATHER IMPACT MATRIX
    # -------------------------------------------------------------------------
    def get_weather_impact(self):
        """Retrieves track temperature, ambient conditions, and precipitation flags."""
        weather_df = self.weather.copy()
        return weather_df[['Time', 'AirTemp', 'TrackTemp', 'Humidity', 'Rainfall']]

    # -------------------------------------------------------------------------
    # 5. PIT STOP STRATEGY ANALYZER
    # -------------------------------------------------------------------------
    def analyze_pit_stops(self):
        """Extracts driver pit stop laps, stint counts, and tyre compound changes."""
        pit_laps = self.laps[self.laps['PitInTime'].notna()].copy()
        summary = pit_laps[['Driver', 'LapNumber', 'Stint', 'Compound', 'PitOutTime']].copy()
        return summary

    # -------------------------------------------------------------------------
    # 6. "WHAT-IF?" UNDERCUT / OVERCUT SIMULATION MODEL
    # -------------------------------------------------------------------------
    def simulate_what_if_pit(self, driver: str, actual_pit_lap: int, target_pit_lap: int, pit_loss_seconds: float = 20.0):
        """
        Simulates the race time delta if a driver had pitted on `target_pit_lap` instead of `actual_pit_lap`.

        Uses the linear degradation slope (s/lap) of the stint the driver was on
        approaching `actual_pit_lap`, rather than a narrow percentile snapshot —
        the previous version clipped its estimate to a 0.5s/lap floor, which
        dominated whenever real degradation was gentle (a common case), making
        every scenario collapse to a fixed lap_difference * 0.5 regardless of
        the driver's actual pace trend.
        """
        drv_laps = self.clean_laps[self.clean_laps['Driver'] == driver].sort_values('LapNumber').copy()
        if drv_laps.empty:
            return {"Error": f"Driver {driver} not found."}

        pre_pit_laps = drv_laps[drv_laps['LapNumber'] < actual_pit_lap]
        if pre_pit_laps.empty:
            return {"Error": f"No laps found before lap {actual_pit_lap} for {driver}."}

        stint = pre_pit_laps.iloc[-1]['Stint']
        compound = pre_pit_laps.iloc[-1]['Compound']
        stint_laps = drv_laps[drv_laps['Stint'] == stint]

        if len(stint_laps) >= 4:
            x = stint_laps['LapNumber'].values
            y = stint_laps['LapTimeSeconds'].values
            slope, _ = np.polyfit(x, y, 1)
            tyre_delta_per_lap = float(np.clip(slope, 0.02, 3.0))
            method = "stint degradation slope"
        else:
            # Not enough laps on this stint for a reliable regression — fall back
            # to the percentile-window estimate, with a much lower floor so it
            # can't silently dominate the result the way 0.5 did.
            start_lap = min(actual_pit_lap, target_pit_lap) - 1
            end_lap = max(actual_pit_lap, target_pit_lap) + 2
            window_laps = drv_laps[(drv_laps['LapNumber'] >= start_lap) & (drv_laps['LapNumber'] <= end_lap)]
            fresh = np.percentile(window_laps['LapTimeSeconds'], 20)
            degraded = np.percentile(window_laps['LapTimeSeconds'], 80)
            tyre_delta_per_lap = float(np.clip(degraded - fresh, 0.02, 3.0))
            method = "percentile window (short stint fallback)"

        lap_difference = actual_pit_lap - target_pit_lap
        estimated_gain = lap_difference * tyre_delta_per_lap

        return {
            'Driver': driver,
            'ScenarioType': "Undercut" if lap_difference > 0 else ("Overcut" if lap_difference < 0 else "Neutral"),
            'ActualPitLap': actual_pit_lap,
            'TargetPitLap': target_pit_lap,
            'LapDifference': lap_difference,
            'Compound': compound,
            'Method': method,
            'EstimatedTyreDeltaPerLap_s': float(round(tyre_delta_per_lap, 3)),
            'EstimatedTimeDelta_s': float(round(estimated_gain, 3)),
            'PitLossBaseline_s': float(pit_loss_seconds)
        }


# =============================================================================
# CLI TEST RIG
# =============================================================================
if __name__ == "__main__":
    print("Initializing engine and loading 2025 British Grand Prix data...")
    engine = F1StrategyEngine(2025, "British Grand Prix", "R")

    print("\n--- 1. TYRE DEGRADATION SUMMARY ---")
    print(engine.analyze_tyre_degradation().head())

    print("\n--- 2. WHAT-IF SIMULATION (NOR 3-Lap Undercut) ---")
    print(engine.simulate_what_if_pit('NOR', actual_pit_lap=20, target_pit_lap=17))

    print("\n--- 3. SAFETY CAR / VSC PERIODS ---")
    sc_laps, sc_msgs = engine.get_safety_car_periods()
    print(sc_laps.head())