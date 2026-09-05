import unittest
import pandas as pd
from main import F1StrategyEngine


class PitWindowMathTests(unittest.TestCase):
    def _engine_with_laps(self):
        """Build the smallest in-memory stint needed to test the estimator."""
        engine = F1StrategyEngine.__new__(F1StrategyEngine)
        # Raw laps fall by 0.005 s/lap from fuel burn, while the 0.035 s/lap
        # correction yields 0.030 s/lap tyre degradation: 3 laps => 0.090 s.
        engine.clean_laps = pd.DataFrame({
            "Driver": ["TST"] * 6,
            "LapNumber": [10, 11, 12, 13, 14, 15],
            "Stint": [1] * 6,
            "Compound": ["MEDIUM"] * 6,
            "LapTimeSeconds": [90.000, 89.995, 89.990, 89.985, 89.980, 89.975],
        })
        return engine

    def test_undercut_uses_fuel_corrected_slope_and_cancels_pit_loss(self):
        result = self._engine_with_laps().simulate_what_if_pit(
            "TST", actual_pit_lap=16, target_pit_lap=13, pit_loss_seconds=24.0
        )
        self.assertEqual(result["ScenarioType"], "Undercut")
        self.assertAlmostEqual(result["EstimatedTyreDeltaPerLap_s"], 0.030, places=3)
        self.assertAlmostEqual(result["EstimatedTimeDelta_s"], 0.090, places=3)
        self.assertEqual(result["PitLossBaseline_s"], 24.0)


if __name__ == "__main__":
    unittest.main()