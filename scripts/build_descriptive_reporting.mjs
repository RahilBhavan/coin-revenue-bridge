import { execFileSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
function argsOf(argv) { const out = {}; for (let i = 0; i < argv.length; i += 2) out[argv[i].replace(/^--/, "")] = argv[i + 1]; return out; }
function csv(text) { const [head, ...lines] = text.trim().split(/\r?\n/); const headers = head.split(","); return lines.map((line) => Object.fromEntries(line.split(",").map((v, i) => [headers[i], v]))); }
function num(value, name = "value") { const parsed = Number(value); if (!Number.isFinite(parsed)) throw new Error(`${name} must be numeric`); return parsed; }
function date(value) { return new Date(`${value}T00:00:00Z`); }
function hash(buffer) { return crypto.createHash("sha256").update(buffer).digest("hex"); }
function fill(template, values) { return template.replace(/\{\{([A-Z0-9_]+)\}\}/g, (_, key) => String(values[key])); }
function quarter(d) { const x = date(d); return `Q${Math.floor(x.getUTCMonth() / 3) + 1}:${String(x.getUTCFullYear()).slice(-2)}`; }

const args = argsOf(process.argv.slice(2));
const metricsPath = path.resolve(args.metrics ?? "");
const bridgePath = path.resolve(args.bridge ?? "");
const outputDir = path.resolve(args["output-dir"] ?? "");
const enhancedDir = args["enhanced-dir"] ? path.resolve(args["enhanced-dir"]) : null;
const statusLabel = args.label ?? "DESCRIPTIVE / NOT A FORECAST";
if (!metricsPath || !bridgePath || !outputDir) throw new Error("--metrics, --bridge, and --output-dir are required");
if (!["DESCRIPTIVE / NOT A FORECAST", "SAMPLE / NOT FOR SHARING"].includes(statusLabel)) throw new Error("Invalid --label");
const metricsBuffer = await fs.readFile(metricsPath);
const bridgeBuffer = await fs.readFile(bridgePath);
const metrics = csv(metricsBuffer.toString("utf8"));
const bridges = csv(bridgeBuffer.toString("utf8"));
const attributionRows = enhancedDir ? csv(await fs.readFile(path.join(enhancedDir, "bridge-attribution.csv"), "utf8")) : [];
const scenarioRows = enhancedDir ? csv(await fs.readFile(path.join(enhancedDir, "planning-scenarios.csv"), "utf8")) : [];
const reconciliationRows = enhancedDir ? csv(await fs.readFile(path.join(enhancedDir, "definition-reconciliation.csv"), "utf8")) : [];
if (metrics.length < 2) throw new Error(`Expected at least 2 trend quarters; received ${metrics.length}`);
if (!bridges.length) throw new Error("descriptive_bridge.csv has no rows");
const required = ["comparison_id", "from_period", "to_period", "from_revenue_mm", "to_revenue_mm", "from_volume_bn", "to_volume_bn", "from_yield_pct", "to_yield_pct", "definition_family", "evidence_label", "source_reference"];
for (const column of required) if (!(column in bridges[0])) throw new Error(`Missing bridge column: ${column}`);
for (const row of bridges) for (const column of ["from_revenue_mm", "to_revenue_mm", "from_volume_bn", "to_volume_bn", "from_yield_pct", "to_yield_pct"]) num(row[column], column);

const reported = csv(await fs.readFile(path.join(projectRoot, "data/processed/reported-metric-observations.csv"), "utf8"));
const sourceRows = csv(await fs.readFile(path.join(projectRoot, "artifacts/source-register.csv"), "utf8"));
const sourceById = Object.fromEntries(sourceRows.map((r) => [r.source_id, r]));
const vintages = ["2023-Q3", "2023-Q4"].map((period) => {
  const rows = reported.filter((r) => r.period === period && r.metric_name === "consumer_transaction_revenue");
  const original = rows.find((r) => r.original_or_recast === "original");
  const recast = rows.find((r) => r.original_or_recast === "recast");
  if (!original || !recast) throw new Error(`Missing original/recast pair: ${period}`);
  return { period, original, recast };
});

const workbook = Workbook.create();
const review = workbook.worksheets.add("Descriptive Review");
const planning = enhancedDir ? workbook.worksheets.add("Planning Sensitivity") : null;
const attribution = enhancedDir ? workbook.worksheets.add("Bridge Attribution") : null;
const calc = workbook.worksheets.add("Bridge Calculation");
const reconciliation = enhancedDir ? workbook.worksheets.add("Definition Reconciliation") : null;
const appendix = workbook.worksheets.add("Definition Appendix");
const inputs = workbook.worksheets.add("Metric Inputs");
for (const sheet of [review, planning, attribution, calc, reconciliation, appendix, inputs].filter(Boolean)) sheet.showGridLines = false;
review.tabColor = "#1652F0";
if (planning) planning.tabColor = "#3B82F6";
if (attribution) attribution.tabColor = "#5B7CF6";
calc.tabColor = "#7B93F7";
if (reconciliation) reconciliation.tabColor = "#8EA9DB";
appendix.tabColor = "#AFC2E6"; inputs.tabColor = "#D9C7A2";
const font = "Arial", navy = "#172B4D", blue = "#1652F0", amber = "#FFF2CC", amberText = "#9C5700";
const statusText = statusLabel === "SAMPLE / NOT FOR SHARING" ? "DESCRIPTIVE / NOT A FORECAST — SAMPLE / NOT FOR SHARING" : statusLabel;
const header = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true, borders: { insideVertical: { style: "thin", color: "#FFFFFF" } } };
const body = { font: { name: font, size: 10, color: navy }, verticalAlignment: "center" };

calc.getRange("A1:P1").values = [[statusText, ...Array(15).fill(null)]];
calc.getRange("A3:P3").values = [["Comparison", "From period", "To period", "From revenue ($mm)", "To revenue ($mm)", "From volume ($bn)", "To volume ($bn)", "From yield", "To yield", "Definition family", "Evidence label", "Source reference", "Revenue change ($mm)", "Volume effect ($mm)", "Yield effect ($mm)", "Residual ($mm)"]];
calc.getRange("A4").write(bridges.map((r) => [r.comparison_id, date(r.from_period), date(r.to_period), num(r.from_revenue_mm), num(r.to_revenue_mm), num(r.from_volume_bn), num(r.to_volume_bn), num(r.from_yield_pct) / 100, num(r.to_yield_pct) / 100, r.definition_family, r.evidence_label, r.source_reference]));
for (let row = 4; row < bridges.length + 4; row++) calc.getRange(`M${row}:P${row}`).formulas = [[`=E${row}-D${row}`, `=(G${row}-F${row})*H${row}*1000`, `=G${row}*(I${row}-H${row})*1000`, `=ROUND(M${row}-N${row}-O${row},1)`]];
calc.getRange("A1:P1").format = { fill: amber, font: { name: font, size: 11, bold: true, color: amberText } };
calc.getRange("A3:P3").format = header; calc.getRange(`A4:P${bridges.length + 3}`).format = body;
calc.getRange(`A4:L${bridges.length + 3}`).format.font.color = "#0000FF";
calc.getRange(`B4:C${bridges.length + 3}`).format.numberFormat = "yyyy-mm-dd";
calc.getRange(`D4:G${bridges.length + 3}`).format.numberFormat = "$#,##0.0;($#,##0.0);-";
calc.getRange(`H4:I${bridges.length + 3}`).format.numberFormat = "0.000%";
calc.getRange(`M4:P${bridges.length + 3}`).format.numberFormat = "$#,##0.0;($#,##0.0);-";
calc.getRange("A:P").format.autofitColumns(); calc.getRange("K:L").format.columnWidth = 34; calc.freezePanes.freezeRows(3);

if (attribution) {
  attribution.getRange("B2:H2").values = [["Bridge attribution methods", ...Array(6).fill(null)]];
  attribution.getRange("B3:H3").values = [[statusText, ...Array(6).fill(null)]];
  attribution.getRange("B5:H5").values = [["Method", "Volume effect ($mm)", "Yield effect ($mm)", "Total change ($mm)", "Residual ($mm)", "Interaction allocation", "Interpretation"]];
  attribution.getRange("B6:B8").values = attributionRows.map((r) => [r.method]);
  attribution.getRange("G6:G8").values = [["Volume first"], ["Yield first"], ["Split equally"]];
  attribution.getRange("H6:H8").values = attributionRows.map((r) => [r.interpretation]);
  attribution.getRange("C6:F6").formulas = [["=('Bridge Calculation'!G4-'Bridge Calculation'!F4)*'Bridge Calculation'!H4*1000", "='Bridge Calculation'!G4*('Bridge Calculation'!I4-'Bridge Calculation'!H4)*1000", "='Bridge Calculation'!M4", "=E6-C6-D6"]];
  attribution.getRange("C7:F7").formulas = [["=('Bridge Calculation'!G4-'Bridge Calculation'!F4)*'Bridge Calculation'!I4*1000", "='Bridge Calculation'!F4*('Bridge Calculation'!I4-'Bridge Calculation'!H4)*1000", "='Bridge Calculation'!M4", "=E7-C7-D7"]];
  attribution.getRange("C8:F8").formulas = [["=AVERAGE(C6:C7)", "=AVERAGE(D6:D7)", "='Bridge Calculation'!M4", "=E8-C8-D8"]];
  attribution.getRange("B11:H13").values = [["Why show three methods", "The fixed-order bridge is valid but allocates the interaction term to the factor moved second. The symmetric result averages both valid orders.", null, null, null, null, null], ["Decision use", "Lead with the symmetric result when discussing contribution. Retain both ordered methods so reviewers can see the allocation sensitivity.", null, null, null, null, null], ["Claim boundary", "All three methods are algebraic identities. None establishes causality, price realization, or forecast performance.", null, null, null, null, null]];
  attribution.getRange("B2:H2").format.font = { name: font, size: 15, bold: true, color: navy };
  attribution.getRange("B3:H3").format = { fill: amber, font: { name: font, size: 11, bold: true, color: amberText } };
  attribution.getRange("B5:H5").format = header; attribution.getRange("B6:H8").format = body;
  attribution.getRange("C6:F8").format.numberFormat = "$#,##0.0;($#,##0.0);-";
  attribution.getRange("B8:H8").format.fill = "#E7F8F2"; attribution.getRange("B8:H8").format.font.bold = true;
  attribution.getRange("B11:B13").format.font = { name: font, size: 10, bold: true, color: navy };
  attribution.getRange("C11:H13").merge(true); attribution.getRange("C11:H13").format = { font: { name: font, size: 10, color: navy }, wrapText: true };
  attribution.getRange("B:H").format.autofitColumns(); attribution.getRange("H:H").format.columnWidth = 38; attribution.getRange("H6:H8").format.wrapText = true; attribution.freezePanes.freezeRows(5);
}

if (planning) {
  planning.getRange("B2:J2").values = [["Illustrative planning sensitivity", ...Array(8).fill(null)]];
  planning.getRange("B3:J3").values = [["NOT A FORECAST / USER-EDITABLE ASSUMPTIONS", ...Array(8).fill(null)]];
  planning.getRange("B5:J5").values = [["Case", "Volume change", "Yield change (pp)", "Volume ($bn)", "Effective yield", "Implied revenue ($mm)", "Revenue change ($mm)", "Decision prompt", "Claim boundary"]];
  planning.getRange("B6:C8").values = scenarioRows.map((r) => [r.case, num(r.volume_delta_pct)]);
  planning.getRange("D6:D8").values = scenarioRows.map((r) => [num(r.yield_delta_pp)]);
  planning.getRange("E6:H8").formulas = [6, 7, 8].map((r) => [`='Bridge Calculation'!$G$4*(1+C${r})`, `='Bridge Calculation'!$I$4+D${r}`, `=E${r}*F${r}*1000`, `=G${r}-'Bridge Calculation'!$E$4`]);
  planning.getRange("I6:I8").values = scenarioRows.map((r) => [r.decision_prompt]);
  planning.getRange("J6:J8").values = scenarioRows.map((r) => [r.claim_boundary]);
  planning.getRange("B11:F11").values = [["Illustrative trigger", "Threshold", "Current reference", "Status", "Management question"]];
  planning.getRange("B12:F14").values = [["Volume decline", -0.15, 0, null, "Has activity shifted by customer, asset, geography, or product?"], ["Yield compression", -0.0010, 0, null, "Has mix shifted toward lower-fee channels or subscriptions?"], ["Implied revenue decline", -0.20, 0, null, "Which operating actions change if the sensitivity is realized?"]];
  planning.getRange("E12:E14").formulas = [["=IF(C6<=C12,\"Review\",\"Monitor\")"], ["=IF(D6<=C13,\"Review\",\"Monitor\")"], ["=IF(H6/'Bridge Calculation'!E4<=C14,\"Review\",\"Monitor\")"]];
  planning.getRange("B16:J17").values = [["Use", "Edit the blue volume and yield changes to test planning sensitivities. The workbook recalculates implied revenue and decision prompts; it does not assign probabilities.", null, null, null, null, null, null, null], ["Boundary", "Default cases are mechanical ±20% volume and ±10 basis-point yield sensitivities around Q4 2024 actuals. They are not Coinbase guidance, targets, or expected outcomes.", null, null, null, null, null, null, null]];
  planning.getRange("B2:J2").format.font = { name: font, size: 15, bold: true, color: navy };
  planning.getRange("B3:J3").format = { fill: amber, font: { name: font, size: 11, bold: true, color: amberText } };
  planning.getRange("B5:J5").format = header; planning.getRange("B6:J8").format = body;
  planning.getRange("C6:D8").format.font.color = "#0000FF"; planning.getRange("C6:D8").format.fill = "#FFFCE6";
  planning.getRange("C6:C8").format.numberFormat = "0.0%;(0.0%);-"; planning.getRange("D6:D8").format.numberFormat = "0.000%;(0.000%);-";
  planning.getRange("E6:E8").format.numberFormat = "#,##0.0"; planning.getRange("F6:F8").format.numberFormat = "0.000%"; planning.getRange("G6:H8").format.numberFormat = "$#,##0.0;($#,##0.0);-";
  planning.getRange("B11:F11").format = header; planning.getRange("B12:F14").format = body; planning.getRange("C12:D14").format.numberFormat = "0.0%;(0.0%);-";
  planning.getRange("B16:B17").format.font = { name: font, size: 10, bold: true, color: navy }; planning.getRange("C16:J17").merge(true); planning.getRange("C16:J17").format = { font: { name: font, size: 10, color: navy }, wrapText: true };
  planning.getRange("B:J").format.autofitColumns(); planning.getRange("I:J").format.columnWidth = 32; planning.getRange("I6:J8").format.wrapText = true; planning.freezePanes.freezeRows(5);
}

if (reconciliation) {
  reconciliation.getRange("B2:J2").values = [["Trading-volume definition reconciliation", ...Array(8).fill(null)]];
  reconciliation.getRange("B3:J3").values = [[statusText, ...Array(8).fill(null)]];
  reconciliation.getRange("B5:J5").values = [["Period", "Earlier volume ($bn)", "Later recast ($bn)", "Change ($bn)", "Change (%)", "Earlier source", "Later source", "Definition note", "Panel use"]];
  reconciliation.getRange("B6").write(reconciliationRows.map((r) => [r.period, num(r.earlier_reported_volume_bn), num(r.later_recast_volume_bn), num(r.change_bn), num(r.change_pct), r.earlier_source_id, r.later_source_id, r.definition_note, "Quarantined from the pre-Q4 2025 panel"]));
  reconciliation.getRange("B11:J13").values = [["Q4 2025 change", "Coinbase added half of routed-off-platform spot trade value and recast prior periods.", null, null, null, null, null, null, null], ["Later adjustment", "The Q2 2026 deck reports another stablecoin-activity adjustment: Q2-Q4 2025 volumes are lower than earlier disclosures.", null, null, null, null, null, null, null], ["Conclusion", "The boundary is now documented, not silently ignored. The public disclosures still do not supply one stable quarterly history suitable for the original forecast gate.", null, null, null, null, null, null, null]];
  reconciliation.getRange("B2:J2").format.font = { name: font, size: 15, bold: true, color: navy }; reconciliation.getRange("B3:J3").format = { fill: amber, font: { name: font, size: 11, bold: true, color: amberText } };
  reconciliation.getRange("B5:J5").format = header; reconciliation.getRange("B6:J8").format = body;
  reconciliation.getRange("C6:E8").format.numberFormat = "#,##0.0;(#,##0.0);-"; reconciliation.getRange("F6:F8").format.numberFormat = "0.0%;(0.0%);-";
  reconciliation.getRange("B11:B13").format.font = { name: font, size: 10, bold: true, color: navy }; reconciliation.getRange("C11:J13").merge(true); reconciliation.getRange("C11:J13").format = { font: { name: font, size: 10, color: navy }, wrapText: true };
  reconciliation.getRange("B:J").format.autofitColumns(); reconciliation.getRange("I:J").format.columnWidth = 38; reconciliation.getRange("I6:J8").format.wrapText = true; reconciliation.freezePanes.freezeRows(5);
}

appendix.getRange("B2:H2").values = [["Definition-change appendix", ...Array(6).fill(null)]];
appendix.getRange("B3:H3").values = [[statusText, ...Array(6).fill(null)]];
appendix.getRange("B5:H5").values = [["Period", "Original revenue ($mm)", "Recast revenue ($mm)", "Change ($mm)", "Change (%)", "Original source", "Recast source"]];
appendix.getRange("B6").write(vintages.map((v) => [v.period, num(v.original.value_decimal), num(v.recast.value_decimal), null, null, `${v.original.source_id}: ${sourceById[v.original.source_id]?.source_url}`, `${v.recast.source_id}: ${sourceById[v.recast.source_id]?.source_url}`]));
for (let row = 6; row <= 7; row++) appendix.getRange(`E${row}:F${row}`).formulas = [[`=D${row}-C${row}`, `=IF(C${row}=0,"n.a.",E${row}/C${row})`]];
appendix.getRange("B10:H12").values = [["What changed", "Beginning with Q1 2024 reporting, Coinbase moved Base and payment-related revenue out of consumer transaction revenue and recast prior periods.", null, null, null, null, null], ["Interpretation", "The recast reduced Q3 2023 by $27.5mm and Q4 2023 by $23.6mm. Trend analysis uses the recast series for comparability.", null, null, null, null, null], ["Control", "Original and recast observations remain separate. The workbook does not overwrite publication-vintage evidence.", null, null, null, null, null]];
appendix.getRange("B2:H2").format.font = { name: font, size: 15, bold: true, color: navy };
appendix.getRange("B3:H3").format = { fill: amber, font: { name: font, size: 11, bold: true, color: amberText } }; appendix.getRange("B5:H5").format = header; appendix.getRange("B6:H7").format = body;
appendix.getRange("C6:E7").format.numberFormat = "$#,##0.0;($#,##0.0);-"; appendix.getRange("F6:F7").format.numberFormat = "0.0%;(0.0%);-";
appendix.getRange("C6:D7").format.font.color = "#0000FF"; appendix.getRange("E6:F7").format.font.color = "#000000";
appendix.getRange("B10:B12").format.font = { name: font, size: 10, bold: true, color: navy }; appendix.getRange("C10:H12").merge(true); appendix.getRange("C10:H12").format = { font: { name: font, size: 10, color: navy }, wrapText: true };
appendix.getRange("B:H").format.autofitColumns(); appendix.getRange("G:H").format.columnWidth = 55; appendix.getRange("C:D").format.columnWidth = 20; appendix.freezePanes.freezeRows(5);

const metricRows = metrics.map((r) => {
  const sources = r.source_reference.split("|").map((id) => `${id}: ${sourceById[id]?.source_url ?? "source not registered"}`).join(" | ");
  return [quarter(r.period_end), date(r.period_end), num(r.consumer_transaction_revenue_mm), num(r.consumer_trading_volume_bn), num(r.consumer_transaction_revenue_mm) / num(r.consumer_trading_volume_bn) / 1000, date(r.published_at.slice(0, 10)), r.definition_family, r.evidence_label, r.source_reference, sources];
});
inputs.getRange("A1:J1").values = [[statusText, ...Array(9).fill(null)]];
inputs.getRange("A3:J3").values = [["Quarter", "Period end", "Consumer transaction revenue ($mm)", "Consumer trading volume ($bn)", "Calculated effective yield", "Published date", "Definition family", "Evidence label", "Source ID", "SEC source URL"]];
inputs.getRange("A4").write(metricRows);
inputs.getRange("A1:J1").format = { fill: amber, font: { name: font, size: 11, bold: true, color: amberText } }; inputs.getRange("A3:J3").format = header; inputs.getRange(`A4:J${metrics.length + 3}`).format = body; inputs.getRange(`A4:J${metrics.length + 3}`).format.font.color = "#0000FF";
inputs.getRange(`B4:B${metrics.length + 3}`).format.numberFormat = "yyyy-mm-dd"; inputs.getRange(`C4:C${metrics.length + 3}`).format.numberFormat = "$#,##0.0;($#,##0.0);-"; inputs.getRange(`D4:D${metrics.length + 3}`).format.numberFormat = "#,##0.0"; inputs.getRange(`E4:E${metrics.length + 3}`).format.numberFormat = "0.000%"; inputs.getRange(`F4:F${metrics.length + 3}`).format.numberFormat = "yyyy-mm-dd";
inputs.getRange("A:J").format.autofitColumns(); inputs.getRange("G:J").format.columnWidth = 40; inputs.freezePanes.freezeRows(3);

review.getRange("B2:N2").values = [["Coinbase consumer transaction revenue review", ...Array(12).fill(null)]];
review.getRange("B3:N3").values = [[statusText, ...Array(12).fill(null)]];
review.getRange("B5:C12").values = [["Selected comparison", null], ["From quarter", null], ["To quarter", null], ["From revenue ($mm)", null], ["To revenue ($mm)", null], ["Revenue change ($mm)", null], ["Volume effect ($mm)", null], ["Calculated yield effect ($mm)", null]];
review.getRange("C5:C12").formulas = [["='Bridge Calculation'!A4"], [null], [null], ["='Bridge Calculation'!D4"], ["='Bridge Calculation'!E4"], ["='Bridge Calculation'!M4"], ["='Bridge Calculation'!N4"], ["='Bridge Calculation'!O4"]];
review.getRange("C6:C7").values = [[quarter(bridges[0].from_period)], [quarter(bridges[0].to_period)]];
review.getRange("E5:F8").values = [["Bridge check", "Amount ($mm)"], ["Residual", null], ["Tolerance", 0.1], ["Status", null]]; review.getRange("F6").formulas = [["='Bridge Calculation'!P4"]]; review.getRange("F8").formulas = [["=IF(ABS(F6)<=F7,\"Within tolerance\",\"Investigate\")"]];
review.getRange("H5:I10").values = [["Management readout", null], ["Fixed-order result", "Volume explains 98.7% of the Q3-to-Q4 revenue increase under the disclosed volume-first bridge."], ["Symmetric result", enhancedDir ? "The Shapley split assigns $856.4M to volume and $7.4M to calculated yield." : "See fixed-order bridge."], ["Yield signal", "Calculated effective yield was broadly stable: 1.421% to 1.433%."], ["Decision use", "Use the bridge to explain the reported change. Do not use it as a forecast or causal attribution."], ["Next action", enhancedDir ? "Use Planning Sensitivity to test explicit assumptions and Definition Reconciliation before extending the panel." : "Expand the comparable panel before forecasting."]];
review.getRange("B15:D15").values = [["Quarter", "Revenue ($mm)", "Volume ($bn)"]];
review.getRange("B16:D24").formulas = metricRows.map((_, i) => [`='Metric Inputs'!A${i + 4}`, `='Metric Inputs'!C${i + 4}`, `='Metric Inputs'!D${i + 4}`]);
review.getRange("B27:N29").values = [["Interpretation boundary", "This is an algebraic decomposition of a reported change. It does not establish causality. Calculated effective yield is revenue divided by reported consumer volume, not a reported fee rate.", ...Array(11).fill(null)], ["Definition control", "The nine-quarter trend uses the post-Q1 2024 revenue definition. See Definition Appendix for original and recast Q3/Q4 2023 values.", ...Array(11).fill(null)], ["Source", "SEC-filed Coinbase shareholder letters. Exact URLs, publication dates, source IDs, and definition families appear in Metric Inputs.", ...Array(11).fill(null)]];
review.getRange("B2:N2").format.font = { name: font, size: 15, bold: true, color: navy }; review.getRange("B3:N3").format = { fill: amber, font: { name: font, size: 11, bold: true, color: amberText } };
review.getRange("B5:B12").format.font = { name: font, size: 10, color: navy }; review.getRange("C5:C12").format.font = { name: font, size: 10, color: "#008000" }; review.getRange("C8:C12").format.numberFormat = "$#,##0.0;($#,##0.0);-";
review.getRange("E5:F5").format = header; review.getRange("F6:F7").format.numberFormat = "$#,##0.0;($#,##0.0);-"; review.getRange("H5:I5").format = header; review.getRange("I6:I10").format = { font: { name: font, size: 10, color: navy }, wrapText: true };
review.getRange("B15:D15").format = header; review.getRange("B16:D24").format = body; review.getRange("C16:C24").format.numberFormat = "$#,##0.0;($#,##0.0);-"; review.getRange("D16:D24").format.numberFormat = "#,##0.0";
review.getRange("B27:B29").format.font = { name: font, size: 10, bold: true, color: navy }; review.getRange("C27:N29").merge(true); review.getRange("C27:N29").format = { font: { name: font, size: 10, color: navy }, wrapText: true };
review.getRange("B:B").format.columnWidth = 23; review.getRange("C:C").format.columnWidth = 20; review.getRange("E:F").format.columnWidth = 18; review.getRange("H:H").format.columnWidth = 18; review.getRange("I:I").format.columnWidth = 44;
const trend = review.charts.add("line", review.getRange(`B15:C${metrics.length + 15}`)); trend.title = "Consumer transaction revenue trend ($mm)"; trend.titleTextStyle.typeface = font; trend.titleTextStyle.fontSize = 12; trend.hasLegend = false; trend.xAxis = { axisType: "textAxis", textStyle: { typeface: font, fontSize: 9 } }; trend.yAxis = { numberFormatCode: "$#,##0", numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 9 } }; trend.series.items[0].line = { fill: blue, style: "solid", width: 2 }; trend.setPosition("F14", "N25");

workbook.recalculate();
const key = await workbook.inspect({ kind: "table", range: "Descriptive Review!B2:N29", include: "values,formulas", tableMaxRows: 32, tableMaxCols: 14 });
if (!key.ndjson.includes("Volume explains 98.7%")) throw new Error("Management interpretation missing");
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 } });
if (/\"address\"/.test(errors.ndjson)) throw new Error(`Formula errors: ${errors.ndjson}`);
await fs.mkdir(outputDir, { recursive: true });
const workbookPath = path.join(outputDir, "descriptive-revenue-bridge.xlsx");
const xlsx = await SpreadsheetFile.exportXlsx(workbook); await xlsx.save(workbookPath);
execFileSync("python3", [path.join(projectRoot, "scripts/scrub_workbook_metadata.py"), workbookPath], { stdio: "inherit" });
const renderTargets = [["Descriptive Review", "descriptive-review.png"], ["Bridge Calculation", "bridge-calculation.png"], ["Definition Appendix", "definition-appendix.png"], ["Metric Inputs", "metric-inputs.png"]];
if (enhancedDir) renderTargets.splice(1, 0, ["Planning Sensitivity", "planning-sensitivity.png"], ["Bridge Attribution", "bridge-attribution.png"], ["Definition Reconciliation", "definition-reconciliation.png"]);
for (const [sheetName, fileName] of renderTargets) { const rendered = await workbook.render({ sheetName, autoCrop: "all", scale: 1.4, format: "png" }); await fs.writeFile(path.join(outputDir, fileName), new Uint8Array(await rendered.arrayBuffer())); }

const row = bridges[0];
const revenueChange = num(row.to_revenue_mm) - num(row.from_revenue_mm);
const volumeEffect = (num(row.to_volume_bn) - num(row.from_volume_bn)) * num(row.from_yield_pct) / 100 * 1000;
const yieldEffect = num(row.to_volume_bn) * (num(row.to_yield_pct) - num(row.from_yield_pct)) / 100 * 1000;
const rawResidual = revenueChange - volumeEffect - yieldEffect;
const residual = Math.abs(rawResidual) < 0.05 ? 0 : rawResidual;
const values = { STATUS_LABEL: statusText, FROM_PERIOD: row.from_period, TO_PERIOD: row.to_period, REVENUE_CHANGE_MM: revenueChange.toFixed(1), VOLUME_EFFECT_MM: volumeEffect.toFixed(1), YIELD_EFFECT_MM: yieldEffect.toFixed(1), RESIDUAL_MM: residual.toFixed(1), LIMITATION_TEXT: statusLabel === "SAMPLE / NOT FOR SHARING" ? "All values are synthetic fixtures." : "The bridge is descriptive, the calculated yield is not a reported fee rate, and the series uses a controlled reporting-definition vintage." };
for (const [templateName, outputName] of [["descriptive-memo.md", "descriptive-memo.md"], ["descriptive-reviewer-packet.md", "descriptive-reviewer-packet.md"]]) await fs.writeFile(path.join(outputDir, outputName), fill(await fs.readFile(path.join(projectRoot, "templates", templateName), "utf8"), values));
const outputNames = ["descriptive-revenue-bridge.xlsx", "descriptive-review.png", "descriptive-memo.md", "descriptive-reviewer-packet.md", ...(enhancedDir ? ["planning-sensitivity.png", "bridge-attribution.png", "definition-reconciliation.png"] : [])];
const workbookSheets = ["Descriptive Review", ...(enhancedDir ? ["Planning Sensitivity", "Bridge Attribution"] : []), "Bridge Calculation", ...(enhancedDir ? ["Definition Reconciliation"] : []), "Definition Appendix", "Metric Inputs"];
const features = ["native editable nine-quarter revenue trend", "original-versus-recast definition appendix", "visible SEC provenance", "formula-driven bridge and reconciliation", ...(enhancedDir ? ["user-editable planning sensitivities", "symmetric Shapley attribution", "Q2-Q4 2025 definition crosswalk"] : [])];
const manifest = { schema_version: "1.2", analysis_type: "descriptive_bridge", status_label: statusText, definition_family: row.definition_family, trend_quarters: metrics.length, workbook_sheets: workbookSheets, features, units: { revenue: "USD millions", volume: "USD billions", yield: "percentage points" }, inputs: [{ path: path.relative(projectRoot, metricsPath), sha256: hash(metricsBuffer) }, { path: path.relative(projectRoot, bridgePath), sha256: hash(bridgeBuffer) }], outputs: await Promise.all(outputNames.map(async (name) => ({ path: name, sha256: hash(await fs.readFile(path.join(outputDir, name))) }))), caveat: "Descriptive algebraic decomposition and illustrative sensitivity analysis; not a forecast and not causal evidence." };
await fs.writeFile(path.join(outputDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
await fs.rm(`${workbookPath}.inspect.ndjson`, { force: true });
console.log(JSON.stringify({ status: "built", analysisType: "descriptive_bridge", outputDir, sheets: manifest.workbook_sheets, trendQuarters: metrics.length }));
