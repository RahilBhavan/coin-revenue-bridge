import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 2) args[argv[i].replace(/^--/, "")] = argv[i + 1];
  return args;
}
function check(condition, message) { if (!condition) throw new Error(message); }
function sha256(buffer) { return crypto.createHash("sha256").update(buffer).digest("hex"); }

const args = parseArgs(process.argv.slice(2));
const outputDir = path.resolve(args["output-dir"] ?? "");
check(outputDir, "--output-dir is required");
const manifestPath = path.join(outputDir, "manifest.json");
const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
check(["DRAFT", "SAMPLE / NOT FOR SHARING"].includes(manifest.status_label), "Invalid status label");
for (const output of manifest.outputs) {
  const buffer = await fs.readFile(path.join(outputDir, output.path));
  check(sha256(buffer) === output.sha256, `Checksum mismatch: ${output.path}`);
}

const workbookPath = path.join(outputDir, "revenue-model.xlsx");
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 4000 });
for (const name of ["Forecast Review", "Forecast Build", "Metric Inputs"]) check(sheets.ndjson.includes(name), `Missing worksheet: ${name}`);
const review = await workbook.inspect({ kind: "table", range: "Forecast Review!C2:J24", include: "values,formulas", tableMaxRows: 30, tableMaxCols: 10 });
check(review.ndjson.includes(manifest.status_label), "Visible status label missing from Forecast Review");
check(review.ndjson.includes("Strongest objection"), "Strongest objection is missing");
check(review.ndjson.includes("Rounding tolerance"), "Rounding tolerance is missing");
const formulas = await workbook.inspect({ kind: "formula", sheetId: "Forecast Build", range: "M5:T200", maxChars: 12000, options: { maxResults: 1000 } });
for (const token of ["ABS(", "*1000", "Q5+R5+S5"]) check(formulas.ndjson.includes(token), `Expected formula token missing: ${token}`);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 300 }, summary: "validation formula error scan" });
check(!/\"address\"/.test(errors.ndjson), `Formula error scan failed: ${errors.ndjson}`);
const reviewSheet = workbook.worksheets.getItem("Forecast Review");
const buildSheet = workbook.worksheets.getItem("Forecast Build");
const inputsSheet = workbook.worksheets.getItem("Metric Inputs");
check(reviewSheet.getRange("C3").values[0][0] === manifest.status_label, "Forecast Review status label mismatch");
check(buildSheet.getRange("A1").values[0][0] === manifest.status_label, "Forecast Build status label mismatch");
check(inputsSheet.getRange("A1").values[0][0] === manifest.status_label, "Metric Inputs status label mismatch");
const bridgeValues = reviewSheet.getRange("G7:G11").values.flat();
check(bridgeValues.slice(0, 4).every((value) => typeof value === "number" && Number.isFinite(value)), "Bridge contains a nonnumeric calculated result");
check(Math.abs(bridgeValues[3]) <= bridgeValues[4], `Bridge difference ${bridgeValues[3]} exceeds tolerance ${bridgeValues[4]}`);
const holdoutValues = reviewSheet.getRange("D16:F18").values;
check(holdoutValues.every((row) => row[0] === 3), "Fixture should show three eligible holdouts per model");
check(holdoutValues.every((row) => typeof row[1] === "number" && typeof row[2] === "number"), "Holdout MAE or bias is not numeric");

const memo = await fs.readFile(path.join(outputDir, "decision-memo.md"), "utf8");
const packet = await fs.readFile(path.join(outputDir, "reviewer-packet.md"), "utf8");
for (const [name, text] of [["decision-memo.md", memo], ["reviewer-packet.md", packet]]) {
  check(text.includes(manifest.status_label), `${name}: visible status label missing`);
  check(!text.includes("{{"), `${name}: unresolved template token`);
  if (manifest.status_label === "SAMPLE / NOT FOR SHARING") check(text.toLowerCase().includes("synthetic"), `${name}: synthetic-data warning missing`);
}
if (args["visual-dir"]) {
  const visualDir = path.resolve(args["visual-dir"]);
  await fs.mkdir(visualDir, { recursive: true });
  for (const [sheetName, fileName] of [["Forecast Review", "forecast-review.png"], ["Forecast Build", "forecast-build.png"], ["Metric Inputs", "metric-inputs.png"]]) {
    const rendered = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
    await fs.writeFile(path.join(visualDir, fileName), new Uint8Array(await rendered.arrayBuffer()));
  }
}
await fs.rm(`${workbookPath}.inspect.ndjson`, { force: true });
console.log(JSON.stringify({ status: "PASS", checks: ["manifest checksums", "three worksheets", "visible status labels", "formula structure", "formula error scan", "bridge reconciliation", "holdout metrics", "memo and packet tokens", ...(args["visual-dir"] ? ["all-sheet renders"] : [])] }));
