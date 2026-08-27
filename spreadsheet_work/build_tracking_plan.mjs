import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "../outputs/01a040c5-e1e9-7541-930d-50096afc5180";
const events = JSON.parse(
  await fs.readFile(new URL("../data/tracking-events.json", import.meta.url), "utf8"),
);

const figmaUrl =
  "https://www.figma.com/design/YxOzcNURPPgfDq9qiXj1uk/%E5%8F%B0%E7%81%A3_%E6%85%A2%E7%97%85_%E9%86%AB%E7%99%82%E4%BA%BA%E5%93%A1_UX_V7.9.0?node-id=11575-278819&t=7045CWobqjzr4MW6-1";

const columns = [
  ["id", "編號"],
  ["page", "頁面/區塊"],
  ["eventName", "事件名稱 (En)"],
  ["trigger", "觸發時機/事件定義 (Trigger/Event Definition)"],
  ["purpose", "追蹤目的"],
  ["analysisValue", "目標/數據分析意義"],
  ["properties", "屬性參數 (Property)"],
  ["propertyDefinitions", "屬性定義 (Property Definition)"],
  ["dataTypes", "Data Type"],
  ["sampleValues", "Sample Values"],
  ["priority", "優先級"],
  ["status", "狀態"],
];

const workbook = Workbook.create();
const summary = workbook.worksheets.add("分析摘要");
const plan = workbook.worksheets.add("埋點計畫");
const codebook = workbook.worksheets.add("欄位說明");

const darkGreen = "#214A1D";
const green = "#2F6B42";
const lightGreen = "#E7F2E5";
const soft = "#F9FBF7";
const line = "#D9E3D5";
const amber = "#FFF2CC";
const blue = "#E8F1FB";
const red = "#FFE8E0";

function writeTitle(sheet, title, subtitle, span = "A1:L1") {
  sheet.getRange(span).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1").format = {
    fill: darkGreen,
    font: { bold: true, color: "#FFFFFF", size: 18 },
  };
  sheet.getRange("A1").format.rowHeight = 34;

  const subtitleRange = span.replace("1", "2");
  sheet.getRange(subtitleRange).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format = {
    fill: soft,
    font: { color: "#4B5F4C", size: 10 },
  };
  sheet.getRange("A2").format.rowHeight = 28;
}

function applyHeader(range) {
  range.format = {
    fill: darkGreen,
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
  };
  range.format.borders = {
    bottom: { style: "medium", color: "#7AA36F" },
  };
}

function applyBody(range) {
  range.format = {
    wrapText: true,
    font: { color: "#223027", size: 10 },
  };
  range.format.borders = {
    insideHorizontal: { style: "thin", color: line },
    insideVertical: { style: "thin", color: "#EEF2EC" },
    bottom: { style: "thin", color: line },
  };
}

writeTitle(
  plan,
  "慢病醫療人員 UX 第一階段埋點計畫",
  `來源：Figma 設計檔與附件範例。新增欄位：追蹤目的。Figma URL：${figmaUrl}`,
);

const headerRow = columns.map(([, label]) => label);
const bodyRows = events.map((event) =>
  columns.map(([key]) => String(event[key]).replace(/; /g, "\n")),
);
const lastRow = bodyRows.length + 4;

plan.getRange("A4:L4").values = [headerRow];
plan.getRange(`A5:L${lastRow}`).values = bodyRows;
applyHeader(plan.getRange("A4:L4"));
applyBody(plan.getRange(`A5:L${lastRow}`));
plan.getRange(`A4:L${lastRow}`).format.autofitRows();
plan.freezePanes.freezeRows(4);
plan.showGridLines = false;

const widths = {
  A: 12,
  B: 18,
  C: 22,
  D: 36,
  E: 34,
  F: 38,
  G: 26,
  H: 30,
  I: 18,
  J: 34,
  K: 10,
  L: 12,
};

for (const [column, width] of Object.entries(widths)) {
  plan.getRange(`${column}1:${column}${lastRow}`).format.columnWidth = width;
}

plan.getRange(`K5:K${lastRow}`).dataValidation = {
  rule: { type: "list", values: ["P0", "P1", "P2"] },
};
plan.getRange(`L5:L${lastRow}`).dataValidation = {
  rule: { type: "list", values: ["第一階段", "第二階段", "待確認"] },
};

const planTable = plan.tables.add(`A4:L${lastRow}`, true, "TrackingPlan");
planTable.style = "TableStyleMedium4";
planTable.showFilterButton = true;

writeTitle(
  summary,
  "埋點計畫摘要",
  "第一階段聚焦大方向事件：功能使用率、入口點擊率、流程完成率與錯誤阻力。",
  "A1:H1",
);

summary.getRange("A4:B8").values = [
  ["指標", "數值"],
  ["事件總數", null],
  ["P0 核心事件", null],
  ["點擊/功能事件", null],
  ["驗證錯誤事件", null],
];
summary.getRange("B5").formulas = [[`=COUNTA('埋點計畫'!$A$5:$A$${lastRow})`]];
summary.getRange("B6").formulas = [[`=COUNTIF('埋點計畫'!$K$5:$K$${lastRow},"P0")`]];
summary.getRange("B7").formulas = [
  [
    `=COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"*click*")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"open*")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"change*")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"manage*")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"reorder*")`,
  ],
];
summary.getRange("B8").formulas = [[`=E9`]];
applyHeader(summary.getRange("A4:B4"));
applyBody(summary.getRange("A5:B8"));
summary.getRange("A4:B8").format.borders = { preset: "all", style: "thin", color: line };
summary.getRange("B5:B8").format = { fill: lightGreen, font: { bold: true, color: "#173F24" } };

summary.getRange("D4:E9").values = [
  ["事件類型", "數量"],
  ["View", null],
  ["Click", null],
  ["Feature", null],
  ["Flow", null],
  ["Validation", null],
];
for (let row = 5; row <= 9; row += 1) {
  const formulaByRow = {
    5: `=COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"view_page")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"view_chart")`,
    6: `=COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"click_tab")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"click_button")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"open_abnormal_report_detail")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"change_chart_filter")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"open_modal")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"open_patient_info_drawer")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"click_sidebar_nav")`,
    7: `=COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"manage_report_tag")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"reorder_report_tag")`,
    8: `=COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"submit_form")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"delete_custom_plan")+COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"abandon_flow")`,
    9: `=COUNTIF('埋點計畫'!$C$5:$C$${lastRow},"validation_error")`,
  };
  summary.getRange(`E${row}`).formulas = [[formulaByRow[row]]];
}
summary.getRange("B7").formulas = [["=E6+E7"]];
applyHeader(summary.getRange("D4:E4"));
applyBody(summary.getRange("D5:E9"));
summary.getRange("D4:E9").format.borders = { preset: "all", style: "thin", color: line };

summary.getRange("A11:H15").merge(true);
summary.getRange("A11").values = [["資料邊界"]];
summary.getRange("A12").values = [["第一階段建議只追蹤功能與流程屬性，不收集病患姓名、身分證、病歷號、完整電話或完整地址。"]];
summary.getRange("A13").values = [["若未來需要串接真實 Figma API 與 LLM，建議在後端保存分析任務，不把 Figma token 或 OpenAI key 放在前端。"]];
summary.getRange("A14").values = [["事件 payload 應以 user_role、page_name、feature_name、action_type、count、status 等去識別欄位為主。"]];
summary.getRange("A15").values = [["此檔案根據 Figma metadata 與使用者提供之欄位範例產出，最終事件仍需與工程埋點 SDK 命名規範對齊。"]];
summary.getRange("A11:H11").format = {
  fill: amber,
  font: { bold: true, color: "#654D0E" },
};
summary.getRange("A12:H15").format = {
  fill: "#FFFBEB",
  font: { color: "#4B5563", size: 10 },
  wrapText: true,
};
summary.getRange("A11:H15").format.borders = { preset: "outside", style: "thin", color: "#E5D394" };

summary.getRange("A18:D23").values = [
  ["下一步建議", "說明", "負責角色", "輸出"],
  ["事件命名確認", "確認 view/click/submit/error 是否符合目前 SDK 或 CDP 規範", "PM / Engineer", "命名規則"],
  ["Figma 節點抽取", "讀取 pages、frames、component names，轉成可分析 UI 結構", "Engineer", "Figma parser"],
  ["AI 判讀規則", "建立醫療場景 prompt 與風險詞彙，避免輸出個資欄位", "PM / Data", "分析規則"],
  ["Excel 匯出", "依本表欄位匯出並保留可篩選表格", "Engineer", ".xlsx"],
  ["追蹤驗收", "以實作事件和 QA checklist 驗證 trigger 與 property", "QA / Engineer", "驗收清單"],
];
applyHeader(summary.getRange("A18:D18"));
applyBody(summary.getRange("A19:D23"));
summary.getRange("A18:D23").format.borders = { preset: "all", style: "thin", color: line };

summary.getRange("A1:H23").format.autofitRows();
summary.getRange("A19:D23").format.rowHeight = 34;
for (const [column, width] of Object.entries({ A: 18, B: 44, C: 16, D: 20, E: 12, F: 18, G: 18, H: 18 })) {
  summary.getRange(`${column}1:${column}24`).format.columnWidth = width;
}
summary.freezePanes.freezeRows(4);
summary.showGridLines = false;

const chart = summary.charts.add("bar", summary.getRange("D4:E9"));
chart.title = "事件類型分布";
chart.hasLegend = false;
chart.setPosition("G4", "L17");

writeTitle(
  codebook,
  "欄位說明",
  "欄位定義對齊附件範例，並新增「追蹤目的」作為每個事件應被追蹤的產品/數據理由。",
  "A1:D1",
);

codebook.getRange("A4:D17").values = [
  ["欄位", "定義", "填寫規則", "範例"],
  ["編號", "埋點需求唯一識別碼", "使用模組縮寫加流水號", "CDM_001"],
  ["頁面/區塊", "事件發生的頁面或功能區", "使用產品設計中的 page、frame 或主要功能名稱", "健康計畫"],
  ["事件名稱 (En)", "工程可實作的英文事件名稱", "使用 snake_case，動詞加物件", "click_button"],
  ["觸發時機/事件定義", "事件發生條件", "明確寫出觸發、成功或失敗時點", "點擊新增自訂計畫按鈕時"],
  ["追蹤目的", "為什麼要追蹤此事件", "以產品問題或使用者行為假設描述", "衡量醫療人員是否有建立個案化追蹤計畫的需求"],
  ["目標/數據分析意義", "事件可回答的分析問題", "說明可計算的指標或決策用途", "計算新增流程轉換率"],
  ["屬性參數 (Property)", "事件 payload 欄位", "避免病患個資，以功能、狀態、數量、類型為主", "page_name; button_name"],
  ["屬性定義", "每個 property 的中文定義", "順序需對應屬性參數", "頁面名稱; 按鈕名稱"],
  ["Data Type", "屬性的資料型態", "使用 string、integer、boolean、date、number", "string; integer"],
  ["Sample Values", "可供工程理解的範例值", "使用去識別化範例", "health_plan; add_custom_plan"],
  ["優先級", "埋點導入優先順序", "P0 必做、P1 建議、P2 觀察", "P0"],
  ["狀態", "導入階段或確認狀態", "第一階段、第二階段、待確認", "第一階段"],
  ["資料邊界", "醫療產品資料保護原則", "不可寫入病患姓名、身分證、病歷號等可識別資訊", "使用 user_role 取代 user_name"],
];
applyHeader(codebook.getRange("A4:D4"));
applyBody(codebook.getRange("A5:D17"));
codebook.getRange("A4:D17").format.borders = { preset: "all", style: "thin", color: line };
for (const [column, width] of Object.entries({ A: 22, B: 38, C: 42, D: 36 })) {
  codebook.getRange(`${column}1:${column}18`).format.columnWidth = width;
}
codebook.getRange("A1:D17").format.autofitRows();
codebook.freezePanes.freezeRows(4);
codebook.showGridLines = false;

summary.getRange("A5:B8").conditionalFormats.add("containsText", {
  text: "P0",
  format: { fill: red },
});
plan.getRange(`K5:K${lastRow}`).conditionalFormats.add("containsText", {
  text: "P0",
  format: { fill: lightGreen, font: { bold: true, color: green } },
});
plan.getRange(`K5:K${lastRow}`).conditionalFormats.add("containsText", {
  text: "P1",
  format: { fill: amber, font: { color: "#7A5511" } },
});
plan.getRange(`K5:K${lastRow}`).conditionalFormats.add("containsText", {
  text: "P2",
  format: { fill: blue, font: { color: "#315F91" } },
});

await fs.mkdir(outputDir, { recursive: true });

const checks = await workbook.inspect({
  kind: "table",
  range: `埋點計畫!A4:L${lastRow}`,
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 12,
});
console.log(checks.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

for (const sheetName of ["分析摘要", "埋點計畫", "欄位說明"]) {
  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(
    `${outputDir}/${sheetName}.png`,
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/慢病醫療人員_UX_第一階段埋點計畫.xlsx`);
