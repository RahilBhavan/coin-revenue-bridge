import contextlib
import csv
import importlib.util
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from strategic_finance.core import (  # noqa: E402
    AnalysisError,
    FORECAST_GATE_QUARTERS,
    comparable_quarter_count,
    compute_bridge,
    descriptive_bridge,
    forecast_gate,
    forecast_target,
    ingest_csv,
    planning_sensitivity,
    score_forecasts,
    symmetric_attribution,
)


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        schema = (ROOT / "sql" / "schema.sql").read_text()
        self.connection.executescript(schema)
        ingest_csv(self.connection, ROOT / "tests" / "fixtures" / "reported_metrics.csv")

    def test_cutoff_and_lag_only_forecast(self):
        forecast = forecast_target(
            self.connection, "2025-03-31", "2025-02-15", "consumer_v1"
        )
        self.assertEqual(Decimal("144"), forecast.prior_quarter)
        self.assertEqual(Decimal("100"), forecast.prior_year)
        self.assertEqual(Decimal("144"), forecast.driver_revenue)
        self.assertEqual(Decimal("1200"), forecast.forecast_volume)
        self.assertEqual(Decimal("0.12"), forecast.forecast_yield)
        self.assertNotIn("2025-03-31", forecast.input_periods)

    def test_definition_family_and_post_cutoff_rows_fail_closed(self):
        with self.assertRaisesRegex(AnalysisError, "no compatible history"):
            forecast_target(
                self.connection, "2025-03-31", "2024-01-01", "consumer_v1"
            )
        with self.assertRaisesRegex(AnalysisError, "incompatible definition"):
            forecast_target(
                self.connection, "2025-03-31", "2025-02-15", "consumer_v2"
            )

    def test_missing_and_zero_volume_fail_safely(self):
        self.connection.execute(
            "UPDATE reported_metric_observation SET value_decimal='0' "
            "WHERE metric_name='consumer_trading_volume' AND period_end='2024-12-31'"
        )
        with self.assertRaisesRegex(AnalysisError, "positive volume"):
            forecast_target(
                self.connection, "2025-03-31", "2025-02-15", "consumer_v1"
            )

        connection = sqlite3.connect(":memory:")
        connection.executescript((ROOT / "sql" / "schema.sql").read_text())
        ingest_csv(connection, ROOT / "tests" / "fixtures" / "reported_metrics.csv")
        connection.execute(
            "DELETE FROM reported_metric_observation "
            "WHERE metric_name='consumer_trading_volume' AND period_end='2024-12-31' "
            "AND definition_family='consumer_v1'"
        )
        with self.assertRaisesRegex(AnalysisError, "missing revenue or volume"):
            forecast_target(connection, "2025-03-31", "2025-02-15", "consumer_v1")
        connection.close()

    def test_scores_use_literal_expected_formulas(self):
        metrics = score_forecasts(
            [(Decimal("80"), Decimal("100")), (Decimal("110"), Decimal("100"))]
        )
        self.assertEqual(Decimal("15"), metrics.mae)
        self.assertEqual(Decimal("-5"), metrics.signed_bias)
        self.assertEqual(Decimal("0.15"), metrics.wape)
        with self.assertRaisesRegex(AnalysisError, "actual total"):
            score_forecasts([(Decimal("1"), Decimal("0"))])

    def test_fixed_order_bridge_reconciles_exactly(self):
        bridge = compute_bridge(
            Decimal("1200"), Decimal("1300"), Decimal("0.12"), Decimal("169")
        )
        self.assertEqual(Decimal("12.00"), bridge.volume_effect)
        self.assertEqual(Decimal("13.00"), bridge.yield_effect)
        self.assertEqual(Decimal("0.00"), bridge.residual)
        self.assertEqual(Decimal("25.00"), bridge.actual_revenue - bridge.forecast_revenue)

    def test_symmetric_attribution_reconciles_and_splits_interaction(self):
        result = symmetric_attribution(
            Decimal("483.3"), Decimal("1347.1"), Decimal("34000"), Decimal("94000")
        )
        self.assertAlmostEqual(Decimal("856.3667083855"), result.symmetric_volume, places=8)
        self.assertAlmostEqual(Decimal("7.4332916145"), result.symmetric_yield, places=8)
        self.assertLess(abs(result.residual), Decimal("0.000000001"))
        with self.assertRaisesRegex(AnalysisError, "positive volume"):
            symmetric_attribution(Decimal("1"), Decimal("2"), Decimal("0"), Decimal("1"))

    def test_planning_sensitivity_uses_explicit_reference_changes(self):
        downside = planning_sensitivity(
            Decimal("1347.1"), Decimal("94000"), Decimal("-0.20"), Decimal("-0.0010")
        )
        self.assertEqual(Decimal("75200.00"), downside.volume)
        self.assertEqual(Decimal("1002.480000000000000000000000"), downside.implied_revenue)
        with self.assertRaisesRegex(AnalysisError, "invalid volume or yield"):
            planning_sensitivity(Decimal("1"), Decimal("1"), Decimal("-1"), Decimal("0"))

    def test_cli_reproduces_json_without_writing_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "analysis.sqlite"
            command = [
                sys.executable,
                str(ROOT / "scripts" / "analyze.py"),
                "--database",
                str(database),
                "--input",
                str(ROOT / "tests" / "fixtures" / "reported_metrics.csv"),
                "--target-period",
                "2025-03-31",
                "--information-cutoff",
                "2025-02-15",
                "--definition-family",
                "consumer_v1",
            ]
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(Decimal("144"), Decimal(payload["forecast"]["driver_revenue"]))
            self.assertEqual("fixed-volume-then-yield", payload["bridge"]["bridge_order"])

    def test_processed_source_contract_adapter(self):
        connection = sqlite3.connect(":memory:")
        connection.executescript((ROOT / "sql" / "schema.sql").read_text())
        count = ingest_csv(
            connection, ROOT / "data" / "processed" / "reported-metric-observations.csv"
        )
        self.assertEqual(30, count)
        with self.assertRaisesRegex(AnalysisError, "descriptive_only"):
            forecast_target(
                connection,
                "2025-03-31",
                "2025-02-15",
                "REV-POST-2024Q1|VOL-SPOT-MATCHED-PRE-2025Q4",
            )
        connection.close()

    def test_analytics_ready_data_allows_only_labeled_descriptive_bridge(self):
        connection = sqlite3.connect(":memory:")
        connection.executescript((ROOT / "sql" / "schema.sql").read_text())
        source = ROOT / "data" / "processed" / "analytics-ready-metric-observations.csv"
        self.assertEqual(18, ingest_csv(connection, source))
        family = "PAIR-REV-POST2024Q1-VOL-SPOT-PRE2025Q4"
        with self.assertRaisesRegex(AnalysisError, "descriptive_only"):
            forecast_target(connection, "2025-03-31", "2025-02-15", family)
        result = descriptive_bridge(
            connection, "2024-12-31", "2025-03-31", "2025-05-08", family
        )
        self.assertEqual("descriptive", result.analysis_type)
        self.assertEqual("USD_millions", result.revenue_unit)
        self.assertEqual("USD_millions", result.volume_unit)
        self.assertEqual(
            result.revenue_change,
            result.volume_effect + result.yield_effect + result.residual,
        )
        connection.close()

    def test_descriptive_cli_emits_reporting_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [
                sys.executable, str(ROOT / "scripts" / "descriptive_bridge.py"),
                "--database", str(Path(directory) / "bridge.sqlite"),
                "--input", str(ROOT / "data" / "processed" / "analytics-ready-metric-observations.csv"),
                "--comparison-period", "2024-12-31", "--target-period", "2025-03-31",
                "--information-cutoff", "2025-05-08",
                "--definition-family", "PAIR-REV-POST2024Q1-VOL-SPOT-PRE2025Q4",
                "--format", "csv",
            ]
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, completed.returncode, completed.stderr)
            rows = list(csv.DictReader(completed.stdout.splitlines()))
            self.assertEqual("descriptive", rows[0]["analysis_type"])
            self.assertEqual("USD_millions", rows[0]["volume_unit"])


def _gate_rows(periods, family="PAIR-TEST"):
    lines = ["observation_id,period,period_end,metric_name,value_decimal,currency,scale,definition_family,metric_definition_family,vintage_status,source_id,published_at,analysis_use"]
    for index, (label, end) in enumerate(periods):
        for metric, value, scale in (("consumer_transaction_revenue", "100", "millions"), ("consumer_trading_volume", "10", "billions")):
            lines.append(f"{family}-{index}-{metric[-6:]},{label},{end},{metric},{value},USD,{scale},{family},{family},original,SRC-T,2030-01-01T00:00:00Z,descriptive_only")
    return "\n".join(lines) + "\n"


def _quarters(count, start_year=2020):
    ends = ("03-31", "06-30", "09-30", "12-31")
    return [(f"{start_year + i // 4}-Q{i % 4 + 1}", f"{start_year + i // 4}-{ends[i % 4]}") for i in range(count)]


class ForecastGateTests(unittest.TestCase):
    def load(self, text):
        connection = sqlite3.connect(":memory:")
        connection.executescript((ROOT / "sql" / "schema.sql").read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.csv"
            path.write_text(text)
            ingest_csv(connection, path)
        return connection

    def test_real_panel_counts_nine_and_never_splices_families(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from forecast_gate import all_periods, gate_report
        report = gate_report()
        self.assertEqual(9, report["comparable_quarters"])
        self.assertEqual(5, sorted(report["by_family"].values())[0])
        self.assertFalse(report["gate_open"])
        # Twelve calendar quarters have data, which is exactly the gate size.
        # They are not comparable, so the gate must not open on that count.
        self.assertEqual(FORECAST_GATE_QUARTERS, all_periods())

    def test_gate_opens_only_with_twelve_consecutive_quarters_in_one_family(self):
        twelve = self.load(_gate_rows(_quarters(12)))
        self.assertEqual(12, comparable_quarter_count(twelve, "PAIR-TEST"))
        self.assertTrue(forecast_gate({"PAIR-TEST": 12})["gate_open"])
        eleven = self.load(_gate_rows(_quarters(11)))
        self.assertEqual(11, comparable_quarter_count(eleven, "PAIR-TEST"))
        self.assertFalse(forecast_gate({"PAIR-TEST": 11})["gate_open"])

    def test_gap_and_missing_metric_shorten_the_run(self):
        quarters = _quarters(12)
        gapped = self.load(_gate_rows(quarters[:6] + quarters[7:]))
        self.assertEqual(6, comparable_quarter_count(gapped, "PAIR-TEST"))
        text = _gate_rows(quarters).splitlines()
        text = [line for line in text if not (line.startswith("PAIR-TEST-11-volume"))]
        missing = self.load("\n".join(text) + "\n")
        self.assertEqual(11, comparable_quarter_count(missing, "PAIR-TEST"))

    def test_refusal_reports_the_real_count(self):
        connection = self.load(_gate_rows(_quarters(9)))
        with self.assertRaisesRegex(AnalysisError, r"descriptive_only \(9 of 12 comparable quarters\)"):
            forecast_target(connection, "2022-06-30", "2030-01-01", "PAIR-TEST")


class LatestBridgeTests(unittest.TestCase):
    def test_latest_bridge_matches_independent_arithmetic(self):
        with (ROOT / "outputs" / "final-package" / "latest-bridge.csv").open(newline="") as handle:
            rows = {row["method"]: row for row in csv.DictReader(handle)}
        first = rows["Volume first"]
        r0, r1 = Decimal(first["from_revenue_mm"]), Decimal(first["to_revenue_mm"])
        v0, v1 = Decimal(first["from_volume_bn"]), Decimal(first["to_volume_bn"])
        self.assertEqual(("2026-03-31", "2026-06-30"), (first["from_period"], first["to_period"]))
        volume_effect = (v1 - v0) * (r0 / v0)
        yield_effect = r1 - r0 - volume_effect
        self.assertAlmostEqual(float(volume_effect), float(first["volume_effect_mm"]), places=2)
        self.assertAlmostEqual(float(yield_effect), float(first["yield_effect_mm"]), places=2)
        for row in rows.values():
            total = Decimal(row["volume_effect_mm"]) + Decimal(row["yield_effect_mm"])
            self.assertAlmostEqual(float(r1 - r0), float(total), places=2)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_final_evidence", ROOT / "scripts" / "validate_final_evidence.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FinalEvidenceTests(unittest.TestCase):
    def test_validator_skips_missing_prep_inputs_and_exits_1_on_fail(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("artifacts", "data", "sql", "dist"):
                (root / name).symlink_to(ROOT / name)
            (root / "outputs").mkdir()
            for name in ("final-package", "descriptive-bridge"):
                (root / "outputs" / name).symlink_to(ROOT / "outputs" / name)
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                code = validator.main(root)
            self.assertEqual(1, code)
            self.assertIn("scripts/build_enhanced_analysis.py", stderr.getvalue())
            self.assertIn("FAIL: public_case_study", stderr.getvalue())
            (root / "outputs" / "public-case-study").symlink_to(ROOT / "outputs" / "public-case-study")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(0, validator.main(root))

    def test_site_numbers_match_final_package_data(self):
        validator = load_validator()
        final = ROOT / "outputs" / "final-package"
        html = (ROOT / "dist" / "index.html").read_text(encoding="utf-8")
        self.assertEqual([], validator.site_number_problems(html, final))
        self.assertEqual(["$1,002.5M"], validator.site_number_problems(html.replace("$1,002.5M", "$1,000.0M"), final))


if __name__ == "__main__":
    unittest.main()
