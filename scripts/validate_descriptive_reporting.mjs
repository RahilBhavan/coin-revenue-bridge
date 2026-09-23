import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const index = process.argv.indexOf("--output-dir");
if (index < 0 || !process.argv[index + 1]) throw new Error("--output-dir is required");
const outputDir = path.resolve(process.argv[index + 1]);
const manifest = JSON.parse(await fs.readFile(path.join(outputDir, "manifest.json"), "utf8"));
const check = (condition, message) => { if (!condition) throw new Error(message); };
const hash = (buffer) => crypto.createHash("sha256").update(buffer).digest("hex");
check(manifest.analysis_type === "descriptive_bridge", "Manifest analysis type is not descriptive_bridge");
check(manifest.status_label.includes("DESCRIPTIVE / NOT A FORECAST"), "Required descriptive status is missing");
check(manifest.units.revenue === "USD millions" && manifest.units.volume === "USD billions" && manifest.units.yield === "percentage points", "Manifest units are incomplete");
for (const output of manifest.outputs) check(hash(await fs.readFile(path.join(outputDir, output.path))) === output.sha256, `Checksum mismatch: ${output.path}`);
const workbookPath = path.join(outputDir, "descriptive-revenue-bridge.xlsx");
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 3000 });
for (const name of ["Descriptive Review", "Bridge Calculation", "Definition Appendix", "Metric Inputs"]) check(sheets.ndjson.includes(name), `Missing worksheet: ${name}`);
const enhanced = manifest.workbook_sheets.includes("Planning Sensitivity");
if (enhanced) for (const name of ["Planning Sensitivity", "Bridge Attribution", "Definition Reconciliation"]) check(sheets.ndjson.includes(name), `Missing enhanced worksheet: ${name}`);
const review = workbook.worksheets.getItem("Descriptive Review");
check(String(review.getRange("B3").values[0][0]).includes("DESCRIPTIVE / NOT A FORECAST"), "Visible descriptive label missing");
const residual = review.getRange("F6:F7").values.flat();
check(typeof residual[0] === "number" && Math.abs(residual[0]) <= residual[1], `Residual ${residual[0]} exceeds tolerance ${residual[1]}`);
const formulas = await workbook.inspect({ kind: "formula", sheetId: "Bridge Calculation", range: "M4:P200", maxChars: 6000, options: { maxResults: 500 } });
for (const token of ["E4-D4", "*1000", "M4-N4-O4"]) check(formulas.ndjson.includes(token), `Missing bridge formula token: ${token}`);
const appendix = workbook.worksheets.getItem("Definition Appendix");
check(appendix.getRange("C6:D7").values.flat().join("|") === "274.5|247|492.5|468.9", "Original/recast definition values are incorrect");
const appendixFormulas = appendix.getRange("E6:F7").formulas.flat().join("|");
check(appendixFormulas.includes("D6-C6") && appendixFormulas.includes("E7/C7"), "Definition appendix formulas are missing");
const inputs = workbook.worksheets.getItem("Metric Inputs");
const trendQuarters = manifest.trend_quarters;
check(Number.isInteger(trendQuarters) && trendQuarters >= 2, "Trend-quarter count is invalid");
if (!manifest.status_label.includes("SAMPLE")) check(trendQuarters === 9, "Nine-quarter SEC trend is incomplete");
check(inputs.getRange(`A4:A${trendQuarters + 3}`).values.flat().length === trendQuarters, "Trend data is incomplete");
const firstRevenue = inputs.getRange("C4").values[0][0];
const firstVolume = inputs.getRange("D4").values[0][0];
check(Math.abs(inputs.getRange("E4").values[0][0] - (firstRevenue / firstVolume / 1000)) < 1e-9, "Calculated effective yield is not stored as a decimal rate");
const provenance = inputs.getRange(`J4:J${trendQuarters + 3}`).values.flat();
check(manifest.status_label.includes("SAMPLE") ? provenance.every((value) => String(value).length > 0) : provenance.every((value) => String(value).includes("https://www.sec.gov/")), "Visible SEC provenance is incomplete");
check(review.charts.items.length === 1, "Expected one native revenue trend chart");
const trend = review.charts.items[0];
check(trend.title.text === "Consumer transaction revenue trend ($mm)", "Native revenue trend chart title is missing");
check(trend.series.items.length === 1, "Revenue trend must contain one series");
check(String(trend.series.items[0].categoryFormula).includes(`$B$16:$B$${trendQuarters + 15}`) && String(trend.series.items[0].formula).includes(`$C$16:$C$${trendQuarters + 15}`), "Trend chart bindings are incomplete");
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 } });
check(!/\"address\"/.test(errors.ndjson), `Formula errors found: ${errors.ndjson}`);
for (const name of ["descriptive-memo.md", "descriptive-reviewer-packet.md"]) {
  const text = await fs.readFile(path.join(outputDir, name), "utf8");
  check(text.includes("DESCRIPTIVE / NOT A FORECAST"), `${name}: descriptive label missing`);
  check(!text.includes("{{"), `${name}: unresolved template token`);
}
await fs.rm(`${workbookPath}.inspect.ndjson`, { force: true });
if (enhanced) {
  const attribution = workbook.worksheets.getItem("Bridge Attribution");
  const shapley = attribution.getRange("C8:F8").values[0];
  check(Math.abs(shapley[0] - 856.3667) < 0.01 && Math.abs(shapley[1] - 7.4333) < 0.01 && Math.abs(shapley[3]) < 0.01, "Symmetric attribution is incorrect");
  const planning = workbook.worksheets.getItem("Planning Sensitivity");
  const scenarioRevenue = planning.getRange("G6:G8").values.flat();
  check(Math.abs(scenarioRevenue[0] - 1002.48) < 0.01 && Math.abs(scenarioRevenue[1] - 1347.1) < 0.01 && Math.abs(scenarioRevenue[2] - 1729.32) < 0.01, "Planning sensitivity outputs are incorrect");
  const reconciliation = workbook.worksheets.getItem("Definition Reconciliation");
  check(reconciliation.getRange("B6:F8").values.flat().join("|") === "2025-Q2|43|41.5|-1.5|-0.03488372|2025-Q3|59|57.4|-1.6|-0.02711864|2025-Q4|56|53.7|-2.3|-0.04107143", "Definition reconciliation values are incorrect");
  check(manifest.workbook_sheets.length === 7, "Enhanced workbook sheet manifest is incomplete");
} else {
  check(manifest.workbook_sheets.length === 4, "Base workbook sheet manifest is incomplete");
}
console.log(JSON.stringify({ status: "PASS", checks: ["manifest checksums and units", enhanced ? "seven worksheets" : "four worksheets", "visible descriptive status", "bridge reconciliation", "formula structure and error scan", "native trend chart", "original/recast definition appendix", "visible source provenance", ...(enhanced ? ["symmetric bridge attribution", "planning sensitivities", "Q2-Q4 2025 definition reconciliation"] : []), "memo and reviewer packet labels"] }));
