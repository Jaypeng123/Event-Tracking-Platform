"use client";

import { useMemo, useState } from "react";
import trackingEvents from "../data/tracking-events.json";

type TrackingEvent = {
  id: string;
  page: string;
  area: string;
  eventName: string;
  eventType: "View" | "Click" | "Feature" | "Flow" | "Validation";
  trigger: string;
  purpose: string;
  analysisValue: string;
  properties: string;
  propertyDefinitions: string;
  dataTypes: string;
  sampleValues: string;
  priority: "P0" | "P1" | "P2";
  status: string;
};

type Scope = "file" | "page" | "node";
type EventFilter = "All" | TrackingEvent["eventType"];

const events = trackingEvents as TrackingEvent[];

const DEFAULT_FIGMA_URL =
  "https://www.figma.com/design/YxOzcNURPPgfDq9qiXj1uk/%E5%8F%B0%E7%81%A3_%E6%85%A2%E7%97%85_%E9%86%AB%E7%99%82%E4%BA%BA%E5%93%A1_UX_V7.9.0?node-id=11575-278819&t=7045CWobqjzr4MW6-1";

const scopeOptions: Array<{ value: Scope; label: string; meta: string }> = [
  { value: "file", label: "整份檔案", meta: "全站功能使用率" },
  { value: "page", label: "指定 Page", meta: "專案封面" },
  { value: "node", label: "指定節點", meta: "慢病管理-個案詳情" },
];

const filterOptions: Array<{ value: EventFilter; label: string }> = [
  { value: "All", label: "全部" },
  { value: "View", label: "瀏覽" },
  { value: "Click", label: "點擊" },
  { value: "Feature", label: "功能" },
  { value: "Flow", label: "流程" },
  { value: "Validation", label: "驗證" },
];

const exportColumns: Array<{ key: keyof TrackingEvent; label: string }> = [
  { key: "id", label: "編號" },
  { key: "page", label: "頁面/區塊" },
  { key: "eventName", label: "事件名稱 (En)" },
  { key: "trigger", label: "觸發時機/事件定義 (Trigger/Event Definition)" },
  { key: "purpose", label: "追蹤目的" },
  { key: "analysisValue", label: "目標/數據分析意義" },
  { key: "properties", label: "屬性參數 (Property)" },
  { key: "propertyDefinitions", label: "屬性定義 (Property Definition)" },
  { key: "dataTypes", label: "Data Type" },
  { key: "sampleValues", label: "Sample Values" },
  { key: "priority", label: "優先級" },
  { key: "status", label: "狀態" },
];

const typeLabels: Record<TrackingEvent["eventType"], string> = {
  View: "瀏覽",
  Click: "點擊",
  Feature: "功能",
  Flow: "流程",
  Validation: "驗證",
};

function parseFigmaUrl(url: string) {
  const fileKey = url.match(/figma\.com\/(?:design|file)\/([^/?#]+)/)?.[1] ?? "未解析";
  let nodeId = "未指定";

  try {
    const parsed = new URL(url);
    nodeId = parsed.searchParams.get("node-id")?.replace("-", ":") ?? "未指定";
  } catch {
    const fallbackNode = url.match(/node-id=([^&#]+)/)?.[1];
    nodeId = fallbackNode ? fallbackNode.replace("-", ":") : "未指定";
  }

  return { fileKey, nodeId };
}

function escapeCsv(value: string) {
  return `"${value.replace(/"/g, '""')}"`;
}

function escapeXml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function download(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function toCsv(rows: TrackingEvent[]) {
  const header = exportColumns.map((column) => escapeCsv(column.label)).join(",");
  const body = rows
    .map((row) => exportColumns.map((column) => escapeCsv(String(row[column.key]))).join(","))
    .join("\n");

  return `\uFEFF${header}\n${body}`;
}

function toExcelXml(rows: TrackingEvent[]) {
  const header = exportColumns
    .map(
      (column) =>
        `<Cell ss:StyleID="Header"><Data ss:Type="String">${escapeXml(column.label)}</Data></Cell>`,
    )
    .join("");

  const body = rows
    .map((row) => {
      const cells = exportColumns
        .map((column) => {
          const value = String(row[column.key]).replace(/; /g, "\n");
          return `<Cell ss:StyleID="Body"><Data ss:Type="String">${escapeXml(value)}</Data></Cell>`;
        })
        .join("");
      return `<Row>${cells}</Row>`;
    })
    .join("");

  return `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
  <Styles>
    <Style ss:ID="Header">
      <Font ss:Bold="1" ss:Color="#FFFFFF"/>
      <Interior ss:Color="#214A1D" ss:Pattern="Solid"/>
      <Alignment ss:Vertical="Center" ss:WrapText="1"/>
    </Style>
    <Style ss:ID="Body">
      <Alignment ss:Vertical="Top" ss:WrapText="1"/>
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#E5E7EB"/>
      </Borders>
    </Style>
  </Styles>
  <Worksheet ss:Name="埋點計畫">
    <Table>
      <Column ss:Width="86"/>
      <Column ss:Width="132"/>
      <Column ss:Width="148"/>
      <Column ss:Width="260"/>
      <Column ss:Width="240"/>
      <Column ss:Width="260"/>
      <Column ss:Width="200"/>
      <Column ss:Width="220"/>
      <Column ss:Width="130"/>
      <Column ss:Width="260"/>
      <Column ss:Width="72"/>
      <Column ss:Width="82"/>
      <Row ss:Height="34">${header}</Row>
      ${body}
    </Table>
    <WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">
      <FreezePanes/>
      <FrozenNoSplit/>
      <SplitHorizontal>1</SplitHorizontal>
      <TopRowBottomPane>1</TopRowBottomPane>
      <ActivePane>2</ActivePane>
    </WorksheetOptions>
  </Worksheet>
</Workbook>`;
}

export default function Home() {
  const [figmaUrl, setFigmaUrl] = useState(DEFAULT_FIGMA_URL);
  const [scope, setScope] = useState<Scope>("node");
  const [filter, setFilter] = useState<EventFilter>("All");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(events[0].id);
  const [analysisState, setAnalysisState] = useState("已套用 Figma 節點命名與第一階段追蹤策略");

  const figmaInfo = useMemo(() => parseFigmaUrl(figmaUrl), [figmaUrl]);

  const visibleRows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return events.filter((row) => {
      const scopeMatch =
        scope === "file" ||
        (scope === "page" && row.page !== "全站") ||
        (scope === "node" && row.page !== "全站");
      const typeMatch = filter === "All" || row.eventType === filter;
      const queryMatch =
        !normalizedQuery ||
        [
          row.id,
          row.page,
          row.area,
          row.eventName,
          row.trigger,
          row.purpose,
          row.analysisValue,
          row.properties,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      return scopeMatch && typeMatch && queryMatch;
    });
  }, [filter, query, scope]);

  const selectedRow = visibleRows.find((row) => row.id === selectedId) ?? visibleRows[0] ?? events[0];

  const summary = useMemo(() => {
    const p0Count = visibleRows.filter((row) => row.priority === "P0").length;
    const pages = new Set(visibleRows.map((row) => row.page));
    const clickable = visibleRows.filter((row) => row.eventType === "Click" || row.eventType === "Feature").length;

    return [
      { label: "建議事件", value: visibleRows.length, note: "第一階段可先開規格" },
      { label: "核心頁面", value: pages.size, note: "含個案詳情與健康計畫" },
      { label: "P0 事件", value: p0Count, note: "優先驗證使用率" },
      { label: "點擊/功能", value: clickable, note: "主要看入口點擊率" },
    ];
  }, [visibleRows]);

  function handleAnalyze() {
    setAnalysisState(
      scope === "file"
        ? "已產生整份檔案的第一層功能使用率事件"
        : scope === "page"
          ? "已聚焦指定 Page 的頁面、點擊與流程事件"
          : "已聚焦慢病管理-個案詳情節點的健康計畫與病患數據事件",
    );
  }

  function handleExportExcel() {
    download(
      "慢病醫療人員_UX_第一階段埋點計畫.xls",
      toExcelXml(visibleRows),
      "application/vnd.ms-excel;charset=utf-8",
    );
  }

  function handleExportCsv() {
    download("慢病醫療人員_UX_第一階段埋點計畫.csv", toCsv(visibleRows), "text/csv;charset=utf-8");
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Healthcare Analytics</p>
          <h1>埋點分析建立工具</h1>
        </div>
        <div className="topbar-actions" aria-label="匯出工具">
          <button className="secondary-button" type="button" onClick={handleExportCsv}>
            CSV
          </button>
          <button className="primary-button" type="button" onClick={handleExportExcel}>
            匯出 Excel
          </button>
        </div>
      </header>

      <section className="workspace">
        <aside className="control-panel" aria-label="Figma 分析控制台">
          <div className="panel-section">
            <div className="section-heading">
              <span className="section-index">01</span>
              <h2>Figma 來源</h2>
            </div>
            <label className="field-label" htmlFor="figma-url">
              Figma 連結
            </label>
            <textarea
              id="figma-url"
              value={figmaUrl}
              onChange={(event) => setFigmaUrl(event.target.value)}
              rows={5}
            />
            <div className="figma-meta">
              <span>File key</span>
              <strong>{figmaInfo.fileKey}</strong>
              <span>Node</span>
              <strong>{figmaInfo.nodeId}</strong>
            </div>
          </div>

          <div className="panel-section">
            <div className="section-heading">
              <span className="section-index">02</span>
              <h2>分析範圍</h2>
            </div>
            <div className="scope-list" role="radiogroup" aria-label="分析範圍">
              {scopeOptions.map((option) => (
                <button
                  key={option.value}
                  className={scope === option.value ? "scope-option active" : "scope-option"}
                  type="button"
                  onClick={() => setScope(option.value)}
                  aria-pressed={scope === option.value}
                >
                  <span>{option.label}</span>
                  <small>{option.meta}</small>
                </button>
              ))}
            </div>
            <button className="primary-button full-width" type="button" onClick={handleAnalyze}>
              分析頁面內容
            </button>
            <p className="analysis-state">{analysisState}</p>
          </div>

          <div className="reference-visual">
            <div>
              <span className="section-index">03</span>
              <h2>欄位格式參考</h2>
            </div>
            <img src="/tracking-template-reference.png" alt="埋點 Excel 範例欄位參考" />
          </div>
        </aside>

        <section className="main-panel" aria-label="埋點事件清單">
          <div className="summary-grid" aria-label="分析摘要">
            {summary.map((item) => (
              <article className="summary-item" key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
                <small>{item.note}</small>
              </article>
            ))}
          </div>

          <div className="table-toolbar">
            <div>
              <p className="eyebrow">Event Plan</p>
              <h2>第一階段埋點建議</h2>
            </div>
            <div className="toolbar-controls">
              <input
                aria-label="搜尋事件"
                placeholder="搜尋事件、頁面或屬性"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <select
                aria-label="事件類型篩選"
                value={filter}
                onChange={(event) => setFilter(event.target.value as EventFilter)}
              >
                {filterOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="event-table-wrap">
            <table className="event-table">
              <thead>
                <tr>
                  <th>編號</th>
                  <th>頁面/區塊</th>
                  <th>事件名稱</th>
                  <th>觸發時機</th>
                  <th>追蹤目的</th>
                  <th>分析意義</th>
                  <th>屬性參數</th>
                  <th>優先級</th>
                </tr>
              </thead>
              <tbody>
                {visibleRows.map((row) => (
                  <tr
                    key={row.id}
                    className={selectedRow.id === row.id ? "selected" : ""}
                    onClick={() => setSelectedId(row.id)}
                  >
                    <td>
                      <button className="row-id" type="button" onClick={() => setSelectedId(row.id)}>
                        {row.id}
                      </button>
                    </td>
                    <td>
                      <strong>{row.page}</strong>
                      <span>{row.area}</span>
                    </td>
                    <td>
                      <code>{row.eventName}</code>
                      <span className={`type-pill type-${row.eventType.toLowerCase()}`}>
                        {typeLabels[row.eventType]}
                      </span>
                    </td>
                    <td>{row.trigger}</td>
                    <td>{row.purpose}</td>
                    <td>{row.analysisValue}</td>
                    <td>{row.properties}</td>
                    <td>
                      <span className={`priority-pill priority-${row.priority.toLowerCase()}`}>
                        {row.priority}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="detail-panel" aria-label="事件詳情">
          <div className="detail-header">
            <span className={`priority-pill priority-${selectedRow.priority.toLowerCase()}`}>
              {selectedRow.priority}
            </span>
            <code>{selectedRow.eventName}</code>
          </div>
          <h2>{selectedRow.area}</h2>
          <dl className="detail-list">
            <div>
              <dt>追蹤目的</dt>
              <dd>{selectedRow.purpose}</dd>
            </div>
            <div>
              <dt>事件定義</dt>
              <dd>{selectedRow.trigger}</dd>
            </div>
            <div>
              <dt>數據分析意義</dt>
              <dd>{selectedRow.analysisValue}</dd>
            </div>
            <div>
              <dt>屬性參數</dt>
              <dd>{selectedRow.properties}</dd>
            </div>
            <div>
              <dt>屬性定義</dt>
              <dd>{selectedRow.propertyDefinitions}</dd>
            </div>
            <div>
              <dt>Sample Values</dt>
              <dd>{selectedRow.sampleValues}</dd>
            </div>
          </dl>
          <div className="privacy-note">
            <strong>資料邊界</strong>
            <p>第一階段建議使用去識別化事件屬性，不把病患姓名、身分證、病歷號或完整聯絡資訊放入事件 payload。</p>
          </div>
        </aside>
      </section>
    </main>
  );
}
