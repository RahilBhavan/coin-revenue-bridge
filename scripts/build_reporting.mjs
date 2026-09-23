import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 2) {
    if (!argv[i].startsWith("--") || argv[i + 1] === undefined) throw new Error(`Invalid argument near ${argv[i]}`);
    args[argv[i].slice(2)] = argv[i + 1];
  }
  return args;
}

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted && char === '"' && text[i + 1] === '"') { field += '"'; i++; }
    else if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) { row.push(field); field = ""; }
    else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[i + 1] === "\n") i++;
      row.push(field); field = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else field += char;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift();
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

function requireColumns(rows, required, name) {
  if (!rows.length) throw new Error(`${name} has no data rows`);
  const present = new Set(Object.keys(rows[0]));
  const missing = required.filter((column) => !present.has(column));
  if (missing.length) throw new Error(`${name} is missing columns: ${missing.join(", ")}`);
}

function number(value, label, allowBlank = false) {
  if (value === "" && allowBlank) return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) throw new Error(`${label} must be numeric; received ${value}`);
  return parsed;
}

function truth(value) { return String(value).toUpperCase() === "TRUE"; }
function round(value, places = 1) { return Number(value.toFixed(places)); }
function display(value, places = 1) { return Number(value).toFixed(places); }
function sha256(buffer) { return crypto.createHash("sha256").update(buffer).digest("hex"); }
function excelDate(serialDate) { return new Date(`${serialDate}T00:00:00Z`); }

function renderTemplate(template, values) {
  return template.replace(/\{\{([A-Z0-9_]+)\}\}/g, (_, key) => {
    if (!(key in values)) throw new Error(`No value supplied for template token ${key}`);
    return String(values[key]);
  });
}

const args = parseArgs(process.argv.slice(2));
const metricsPath = path.resolve(args.metrics ?? "");
const forecastsPath = path.resolve(args.forecasts ?? "");
const outputDir = path.resolve(args["output-dir"] ?? "");
const statusLabel = args.label ?? "DRAFT";
if (!metricsPath || !forecastsPath || !outputDir) throw new Error("--metrics, --forecasts, and --output-dir are required");
if (!["DRAFT", "SAMPLE / NOT FOR SHARING"].includes(statusLabel)) throw new Error("--label must be DRAFT or SAMPLE / NOT FOR SHARING");
await fs.mkdir(outputDir, { recursive: true });
for (const generatedName of ["revenue-model.xlsx", "revenue-model.xlsx.inspect.ndjson", "forecast-review.png", "decision-memo.md", "reviewer-packet.md", "manifest.json", "build-inspection.ndjson"]) {
  await fs.rm(path.join(outputDir, generatedName), { force: true });
}

const metricsBuffer = await fs.readFile(metricsPath);
const forecastsBuffer = await fs.readFile(forecastsPath);
const metrics = parseCsv(metricsBuffer.toString("utf8"));
const forecasts = parseCsv(forecastsBuffer.toString("utf8"));

requireColumns(metrics, ["period_end", "consumer_transaction_revenue_mm", "consumer_trading_volume_bn", "published_at", "definition_family", "evidence_label", "source_reference"], "processed_metrics.csv");
requireColumns(forecasts, ["target_period", "model_id", "information_cutoff", "predicted_revenue_mm", "actual_revenue_mm", "forecast_volume_bn", "actual_volume_bn", "forecast_yield_pct", "actual_yield_pct", "eligible_for_score", "exclusion_reason", "definition_family"], "forecast_results.csv");

const permittedModels = new Set(["prior_quarter", "prior_year", "driver"]);
for (const [index, row] of forecasts.entries()) {
  if (!permittedModels.has(row.model_id)) throw new Error(`forecast row ${index + 2}: unsupported model_id ${row.model_id}`);
  number(row.predicted_revenue_mm, `forecast row ${index + 2} predicted_revenue_mm`);
  number(row.actual_revenue_mm, `forecast row ${index + 2} actual_revenue_mm`);
  if (row.model_id === "driver" && truth(row.eligible_for_score)) {
    for (const column of ["forecast_volume_bn", "actual_volume_bn", "forecast_yield_pct", "actual_yield_pct"]) number(row[column], `forecast row ${index + 2} ${column}`);
  }
}

const featured = [...forecasts].filter((row) => row.model_id === "driver" && truth(row.eligible_for_score)).sort((a, b) => a.target_period.localeCompare(b.target_period)).at(-1);
if (!featured) throw new Error("At least one eligible driver row is required");
const featuredIndex = forecasts.indexOf(featured);
const baseline = forecasts.find((row) => row.target_period === featured.target_period && row.model_id === "prior_quarter" && truth(row.eligible_for_score));
if (!baseline) throw new Error(`Missing eligible prior_quarter baseline for ${featured.target_period}`);
const definitionFamilies = new Set(forecasts.map((row) => row.definition_family));
if (definitionFamilies.size !== 1) throw new Error("Sample reporting build requires one definition_family; split incompatible vintages upstream");

const workbook = Workbook.create();
const review = workbook.worksheets.add("Forecast Review");
const build = workbook.worksheets.add("Forecast Build");
const inputs = workbook.worksheets.add("Metric Inputs");
review.tabColor = "#1652F0";
build.tabColor = "#5B7CF6";
inputs.tabColor = "#D9C7A2";
for (const sheet of [review, build, inputs]) sheet.showGridLines = false;

const font = "Arial";
const titleStyle = { font: { name: font, size: 15, bold: true, color: "#172B4D" }, verticalAlignment: "center" };
const sectionStyle = { fill: "#E9EFFD", font: { name: font, size: 10, bold: true, color: "#172B4D" }, borders: { preset: "outside", style: "thin", color: "#B7C4DF" } };
const headerStyle = { fill: "#172B4D", font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true };
const bodyStyle = { font: { name: font, size: 10, color: "#172B4D" }, verticalAlignment: "center" };
const sourceStyle = { font: { name: font, size: 10, color: "#0000FF" }, verticalAlignment: "center" };
const formulaStyle = { font: { name: font, size: 10, color: "#000000" }, verticalAlignment: "center" };
const linkStyle = { font: { name: font, size: 10, color: "#008000" }, verticalAlignment: "center" };

// Raw processed metric inputs.
inputs.getRange("A2:G2").values = [["Period end", "Consumer transaction revenue ($mm)", "Consumer trading volume ($bn)", "Published at", "Definition family", "Evidence label", "Source reference"]];
inputs.getRange("A3").write(metrics.map((row) => [excelDate(row.period_end), number(row.consumer_transaction_revenue_mm, "metric revenue"), number(row.consumer_trading_volume_bn, "metric volume"), excelDate(row.published_at), row.definition_family, row.evidence_label, row.source_reference]));
inputs.getRange("A1:G1").values = [[statusLabel, null, null, null, null, null, null]];
inputs.getRange("A1:G1").format = { fill: "#FFF2CC", font: { name: font, size: 11, bold: true, color: "#9C5700" }, borders: { preset: "outside", style: "thin", color: "#D6B656" } };
inputs.getRange("A2:G2").format = headerStyle;
inputs.getRange(`A3:G${metrics.length + 2}`).format = sourceStyle;
inputs.getRange(`A3:A${metrics.length + 2}`).format.numberFormat = "yyyy-mm-dd";
inputs.getRange(`D3:D${metrics.length + 2}`).format.numberFormat = "yyyy-mm-dd";
inputs.getRange(`B3:B${metrics.length + 2}`).format.numberFormat = "$#,##0.0;($#,##0.0);-";
inputs.getRange(`C3:C${metrics.length + 2}`).format.numberFormat = "#,##0.0";
inputs.freezePanes.freezeRows(2);
inputs.getRange("A:G").format.autofitColumns();
inputs.getRange("B:B").format.columnWidth = 24;
inputs.getRange("G:G").format.columnWidth = 32;

// Forecast rows plus formula-driven calculations.
const buildHeaders = ["Target period", "Model", "Information cutoff", "Predicted revenue ($mm)", "Actual revenue ($mm)", "Forecast volume ($bn)", "Actual volume ($bn)", "Forecast yield", "Actual yield", "Eligible", "Exclusion reason", "Definition family", "Signed error ($mm)", "Absolute error ($mm)", "Revenue from forecast drivers ($mm)", "Revenue from actual drivers ($mm)", "Volume effect ($mm)", "Yield effect ($mm)", "Bridge residual ($mm)", "Bridge difference ($mm)"];
build.getRange("A1:T1").values = [[statusLabel, ...Array(19).fill(null)]];
build.getRange("A2:T2").values = [["Forecast and exact variance bridge", ...Array(19).fill(null)]];
build.getRange("A4:T4").values = [buildHeaders];
build.getRange("A5").write(forecasts.map((row) => [excelDate(row.target_period), row.model_id, excelDate(row.information_cutoff), number(row.predicted_revenue_mm, "predicted revenue"), number(row.actual_revenue_mm, "actual revenue"), number(row.forecast_volume_bn, "forecast volume", true), number(row.actual_volume_bn, "actual volume", true), number(row.forecast_yield_pct, "forecast yield", true) === null ? null : number(row.forecast_yield_pct, "forecast yield") / 100, number(row.actual_yield_pct, "actual yield", true) === null ? null : number(row.actual_yield_pct, "actual yield") / 100, truth(row.eligible_for_score) ? "TRUE" : "FALSE", row.exclusion_reason, row.definition_family]));
const firstBuildRow = 5;
const lastBuildRow = forecasts.length + 4;
for (let row = firstBuildRow; row <= lastBuildRow; row++) {
  build.getRange(`M${row}:T${row}`).formulas = [[
    `=IF(J${row}="TRUE",D${row}-E${row},"")`,
    `=IF(J${row}="TRUE",ABS(M${row}),"")`,
    `=IF(AND(B${row}="driver",ISNUMBER(F${row}),ISNUMBER(H${row})),F${row}*H${row}*1000,"")`,
    `=IF(AND(B${row}="driver",ISNUMBER(G${row}),ISNUMBER(I${row})),G${row}*I${row}*1000,"")`,
    `=IF(AND(B${row}="driver",ISNUMBER(G${row}),ISNUMBER(F${row}),ISNUMBER(H${row})),(G${row}-F${row})*H${row}*1000,"")`,
    `=IF(AND(B${row}="driver",ISNUMBER(G${row}),ISNUMBER(I${row}),ISNUMBER(H${row})),G${row}*(I${row}-H${row})*1000,"")`,
    `=IF(B${row}="driver",E${row}-P${row},"")`,
    `=IF(B${row}="driver",Q${row}+R${row}+S${row}-(E${row}-D${row}),"")`,
  ]];
}
build.getRange("A1:T1").format = { fill: "#FFF2CC", font: { name: font, size: 11, bold: true, color: "#9C5700" }, borders: { preset: "outside", style: "thin", color: "#D6B656" } };
build.getRange("A2:T2").format = titleStyle;
build.getRange("A4:T4").format = headerStyle;
build.getRange(`A5:L${lastBuildRow}`).format = sourceStyle;
build.getRange(`M5:T${lastBuildRow}`).format = formulaStyle;
build.getRange(`A5:A${lastBuildRow}`).format.numberFormat = "yyyy-mm-dd";
build.getRange(`C5:C${lastBuildRow}`).format.numberFormat = "yyyy-mm-dd";
build.getRange(`D5:G${lastBuildRow}`).format.numberFormat = "$#,##0.0;($#,##0.0);-";
build.getRange(`H5:I${lastBuildRow}`).format.numberFormat = "0.000%";
build.getRange(`M5:T${lastBuildRow}`).format.numberFormat = "$#,##0.0;($#,##0.0);-";
build.freezePanes.freezeRows(4);
build.freezePanes.freezeColumns(2);
build.getRange("A:T").format.autofitColumns();
for (const col of ["B:B", "K:K", "L:L"]) build.getRange(col).format.columnWidth = 18;
build.getRange("A:T").format.rowHeight = 18;
build.getRange("A1:T2").format.rowHeight = 23;

// Reviewer view. Headline formulas link to the build and use one calculation owner.
const featuredBuildRow = featuredIndex + firstBuildRow;
const baselineBuildRow = forecasts.indexOf(baseline) + firstBuildRow;
const driverRows = forecasts.map((row, index) => row.model_id === "driver" && truth(row.eligible_for_score) ? index + firstBuildRow : null).filter(Boolean);
review.getRange("C2:J2").values = [["Coinbase Strategic Finance forecast review", ...Array(7).fill(null)]];
review.getRange("C3:J3").values = [[statusLabel, ...Array(7).fill(null)]];
review.getRange("C5:F5").values = [["Featured forecast", null, null, null]];
review.getRange("C6:D11").values = [["Target period", null], ["Information cutoff", null], ["Driver forecast ($mm)", null], ["Prior-quarter baseline ($mm)", null], ["Actual revenue ($mm)", null], ["Forecast variance ($mm)", null]];
review.getRange("D6:D11").formulas = [[`='Forecast Build'!A${featuredBuildRow}`], [`='Forecast Build'!C${featuredBuildRow}`], [`='Forecast Build'!D${featuredBuildRow}`], [`='Forecast Build'!D${baselineBuildRow}`], [`='Forecast Build'!E${featuredBuildRow}`], [`='Forecast Build'!E${featuredBuildRow}-'Forecast Build'!D${featuredBuildRow}`]];
review.getRange("F6:G11").values = [["Bridge", "Amount ($mm)"], ["Volume effect", null], ["Effective-yield effect", null], ["Residual", null], ["Reconciliation difference", null], ["Rounding tolerance", 0.1]];
review.getRange("G7:G10").formulas = [[`='Forecast Build'!Q${featuredBuildRow}`], [`='Forecast Build'!R${featuredBuildRow}`], [`='Forecast Build'!S${featuredBuildRow}`], [`='Forecast Build'!T${featuredBuildRow}`]];
review.getRange("C14:F14").values = [["Eligible holdout performance", null, null, null]];
review.getRange("C15:F15").values = [["Model", "Holdouts", "MAE ($mm)", "Signed bias ($mm)"]];
const models = ["prior_quarter", "prior_year", "driver"];
review.getRange("C16:C18").values = models.map((model) => [model]);
for (let row = 16; row <= 18; row++) {
  review.getRange(`D${row}:F${row}`).formulas = [[
    `=COUNTIFS('Forecast Build'!$B$5:$B$${lastBuildRow},C${row},'Forecast Build'!$J$5:$J$${lastBuildRow},"TRUE")`,
    `=IF(D${row}=0,"n.a.",SUMIFS('Forecast Build'!$N$5:$N$${lastBuildRow},'Forecast Build'!$B$5:$B$${lastBuildRow},C${row},'Forecast Build'!$J$5:$J$${lastBuildRow},"TRUE")/D${row})`,
    `=IF(D${row}=0,"n.a.",SUMIFS('Forecast Build'!$M$5:$M$${lastBuildRow},'Forecast Build'!$B$5:$B$${lastBuildRow},C${row},'Forecast Build'!$J$5:$J$${lastBuildRow},"TRUE")/D${row})`,
  ]];
}
review.getRange("H14:J14").values = [["Driver holdout totals", null, null]];
review.getRange("H15:I18").values = [["Metric", "Result"], ["Absolute error ($mm)", null], ["Actual revenue ($mm)", null], ["WAPE", null]];
review.getRange("I16:I18").formulas = [[
  `=SUMIFS('Forecast Build'!$N$5:$N$${lastBuildRow},'Forecast Build'!$B$5:$B$${lastBuildRow},"driver",'Forecast Build'!$J$5:$J$${lastBuildRow},"TRUE")`,
], [
  `=SUMIFS('Forecast Build'!$E$5:$E$${lastBuildRow},'Forecast Build'!$B$5:$B$${lastBuildRow},"driver",'Forecast Build'!$J$5:$J$${lastBuildRow},"TRUE")`,
], ["=IF(I17=0,\"n.a.\",I16/I17)"]];
review.getRange("C21:J21").values = [["Interpretation and limitation", ...Array(7).fill(null)]];
for (const row of [22, 23, 24]) review.mergeCells(`D${row}:J${row}`);
review.getRange("C22:J24").values = [["Recommendation", "Keep the prior-quarter baseline visible and use the driver model only after cutoff and definition checks pass.", null, null, null, null, null, null], ["Strongest objection", "Calculated effective yield is a proxy, not a reported causal driver; a small sample cannot establish stability.", null, null, null, null, null, null], ["Evidence boundary", statusLabel === "SAMPLE / NOT FOR SHARING" ? "All values are synthetic fixtures. Do not cite, share, or interpret them as Coinbase results." : "DRAFT output. Source and validation gates remain open; do not treat as final.", null, null, null, null, null, null]];

review.getRange("C2:J2").format = titleStyle;
review.getRange("C3:J3").format = { fill: "#FFF2CC", font: { name: font, size: 11, bold: true, color: "#9C5700" }, borders: { preset: "outside", style: "thin", color: "#D6B656" } };
for (const section of ["C5:F5", "C14:F14", "H14:J14", "C21:J21"]) review.getRange(section).format = sectionStyle;
for (const header of ["F6:G6", "C15:F15", "H15:I15"]) review.getRange(header).format = headerStyle;
review.getRange("C6:J24").format.font = { name: font, size: 10, color: "#172B4D" };
review.getRange("D6:D11").format = linkStyle;
review.getRange("G7:G10").format = linkStyle;
review.getRange("D16:F18").format = formulaStyle;
review.getRange("I16:I18").format = formulaStyle;
review.getRange("D6:D7").format.numberFormat = "yyyy-mm-dd";
review.getRange("D8:D11").format.numberFormat = "$#,##0.0;($#,##0.0);-";
review.getRange("G7:G11").format.numberFormat = "$#,##0.0;($#,##0.0);-";
review.getRange("E16:F18").format.numberFormat = "$#,##0.0;($#,##0.0);-";
review.getRange("I16:I17").format.numberFormat = "$#,##0.0;($#,##0.0);-";
review.getRange("I18").format.numberFormat = "0.0%";
review.getRange("C22:C24").format.font = { name: font, size: 10, bold: true, color: "#172B4D" };
review.getRange("D22:J24").format.wrapText = true;
review.getRange("C:C").format.columnWidth = 22;
review.getRange("D:D").format.columnWidth = 18;
review.getRange("E:E").format.columnWidth = 16;
review.getRange("F:F").format.columnWidth = 24;
review.getRange("G:G").format.columnWidth = 18;
review.getRange("H:H").format.columnWidth = 22;
review.getRange("I:I").format.columnWidth = 18;
review.getRange("J:J").format.columnWidth = 14;
review.getRange("C22:J24").format.rowHeight = 32;

workbook.recalculate();
await workbook.inspect({ kind: "table", range: "Forecast Review!C2:J24", include: "values,formulas", tableMaxRows: 30, tableMaxCols: 10, maxChars: 12000 });
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
if (/\"address\"/.test(errors.ndjson)) throw new Error(`Formula errors found: ${errors.ndjson}`);

const workbookPath = path.join(outputDir, "revenue-model.xlsx");
const previewPath = path.join(outputDir, "forecast-review.png");
const preview = await workbook.render({ sheetName: "Forecast Review", range: "C2:J24", scale: 1.5, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(workbookPath);

const driverEligible = forecasts.filter((row) => row.model_id === "driver" && truth(row.eligible_for_score));
const driverMae = driverEligible.reduce((sum, row) => sum + Math.abs(number(row.predicted_revenue_mm, "predicted") - number(row.actual_revenue_mm, "actual")), 0) / driverEligible.length;
const driverBias = driverEligible.reduce((sum, row) => sum + number(row.predicted_revenue_mm, "predicted") - number(row.actual_revenue_mm, "actual"), 0) / driverEligible.length;
const driverWape = driverEligible.reduce((sum, row) => sum + Math.abs(number(row.predicted_revenue_mm, "predicted") - number(row.actual_revenue_mm, "actual")), 0) / driverEligible.reduce((sum, row) => sum + number(row.actual_revenue_mm, "actual"), 0) * 100;
const volumeEffect = (number(featured.actual_volume_bn, "actual volume") - number(featured.forecast_volume_bn, "forecast volume")) * (number(featured.forecast_yield_pct, "forecast yield") / 100) * 1000;
const yieldEffect = number(featured.actual_volume_bn, "actual volume") * ((number(featured.actual_yield_pct, "actual yield") - number(featured.forecast_yield_pct, "forecast yield")) / 100) * 1000;
const totalVariance = number(featured.actual_revenue_mm, "actual") - number(featured.predicted_revenue_mm, "predicted");
const residual = totalVariance - volumeEffect - yieldEffect;
const limitation = statusLabel === "SAMPLE / NOT FOR SHARING" ? "All values are synthetic fixtures and must not be cited as Coinbase results." : "Source, validation, and human-review gates remain open.";
const templateValues = {
  STATUS_LABEL: statusLabel,
  ARTIFACT_TYPE: statusLabel === "SAMPLE / NOT FOR SHARING" ? "sample" : "draft",
  FEATURED_PERIOD: featured.target_period,
  INFORMATION_CUTOFF: featured.information_cutoff,
  DRIVER_FORECAST_MM: display(number(featured.predicted_revenue_mm, "driver forecast")),
  BASELINE_FORECAST_MM: display(number(baseline.predicted_revenue_mm, "baseline forecast")),
  ACTUAL_REVENUE_MM: display(number(featured.actual_revenue_mm, "actual revenue")),
  VOLUME_EFFECT_MM: display(volumeEffect),
  YIELD_EFFECT_MM: display(yieldEffect),
  BRIDGE_RESIDUAL_MM: display(residual),
  TOTAL_VARIANCE_MM: display(totalVariance),
  DRIVER_HOLDOUT_COUNT: driverEligible.length,
  DRIVER_MAE_MM: display(driverMae),
  DRIVER_BIAS_MM: display(driverBias),
  DRIVER_WAPE_PCT: display(driverWape),
  DEFINITION_FAMILY: featured.definition_family,
  LIMITATION_TEXT: limitation,
};

const memoTemplate = await fs.readFile(path.join(projectRoot, "templates/decision-memo.md"), "utf8");
const packetTemplate = await fs.readFile(path.join(projectRoot, "templates/reviewer-packet.md"), "utf8");
const memoPath = path.join(outputDir, "decision-memo.md");
const packetPath = path.join(outputDir, "reviewer-packet.md");
await fs.writeFile(memoPath, renderTemplate(memoTemplate, templateValues));
await fs.writeFile(packetPath, renderTemplate(packetTemplate, templateValues));

const outputFiles = [workbookPath, previewPath, memoPath, packetPath];
const manifest = {
  schema_version: "1.0",
  generated_at: "deterministic-from-inputs",
  status_label: statusLabel,
  definition_family: featured.definition_family,
  featured_period: featured.target_period,
  information_cutoff: featured.information_cutoff,
  inputs: [
    { role: "processed_metrics", path: path.relative(projectRoot, metricsPath), sha256: sha256(metricsBuffer), rows: metrics.length },
    { role: "forecast_results", path: path.relative(projectRoot, forecastsPath), sha256: sha256(forecastsBuffer), rows: forecasts.length },
  ],
  outputs: await Promise.all(outputFiles.map(async (file) => ({ path: path.basename(file), sha256: sha256(await fs.readFile(file)) }))),
  workbook: { sheets: ["Forecast Review", "Forecast Build", "Metric Inputs"], formula_error_scan: "PASS", inspected_range: "Forecast Review!C2:J24" },
  caveats: [limitation, "Workbook formulas were calculated in the bundled artifact runtime; validate in the intended desktop spreadsheet engine before external use."],
};
await fs.writeFile(path.join(outputDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(JSON.stringify({ status: "built", outputDir, workbook: workbookPath, files: [...outputFiles.map((file) => path.basename(file)), "manifest.json"] }));
