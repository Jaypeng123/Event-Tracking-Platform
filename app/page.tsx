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
type FigmaSourceMode = "empty" | "file" | "node" | "unsupported" | "invalid";

type FigmaPage = {
  id: string;
  name: string;
  relatedEventPages: string[];
};

type FigmaSourceInfo = {
  mode: FigmaSourceMode;
  fileKey: string;
  fileName: string;
  nodeId: string;
  nodeName: string;
  pages: FigmaPage[];
  normalizedUrl: string;
};

const events = trackingEvents as TrackingEvent[];

const EMPTY_FIGMA_SOURCE: FigmaSourceInfo = {
  mode: "empty",
  fileKey: "",
  fileName: "",
  nodeId: "",
  nodeName: "",
  pages: [],
  normalizedUrl: "",
};

const knownFigmaFiles: Record<string, { name: string; pages: FigmaPage[]; nodes: Record<string, string> }> = {
  YxOzcNURPPgfDq9qiXj1uk: {
    name: "台灣 慢病 醫療人員 UX V7.9.0",
    pages: [
      {
        id: "0:1",
        name: "專案封面",
        relatedEventPages: ["個案詳情", "健康計畫", "CoDoctor Watch：血壓"],
      },
    ],
    nodes: {
      "11575:278819": "慢病管理-個案詳情",
    },
  },
};

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

function normalizeUrl(rawUrl: string) {
  const trimmed = rawUrl.trim();

  if (!trimmed) {
    return "";
  }

  return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
}

function normalizeNodeId(value: string) {
  return decodeURIComponent(value).replace(/-/g, ":");
}

function parseFigmaUrl(rawUrl: string): FigmaSourceInfo {
  const normalizedUrl = normalizeUrl(rawUrl);

  if (!normalizedUrl) {
    return EMPTY_FIGMA_SOURCE;
  }

  try {
    const parsed = new URL(normalizedUrl);
    const pathParts = parsed.pathname.split("/").filter(Boolean);
    const fileType = pathParts[0];
    const fileKey = pathParts[1] ?? "";

    if (parsed.hostname !== "www.figma.com" && parsed.hostname !== "figma.com") {
      return { ...EMPTY_FIGMA_SOURCE, mode: "invalid", normalizedUrl };
    }

    if (!["design", "file"].includes(fileType) || !fileKey) {
      return { ...EMPTY_FIGMA_SOURCE, mode: "unsupported", normalizedUrl };
    }

    const knownFile = knownFigmaFiles[fileKey];
    const nodeId = parsed.searchParams.get("node-id")
      ? normalizeNodeId(parsed.searchParams.get("node-id") ?? "")
      : "";
    const fileName = knownFile?.name ?? decodeURIComponent(pathParts[2] ?? "Figma design file");

    return {
      mode: nodeId ? "node" : "file",
      fileKey,
      fileName,
      nodeId,
      nodeName: nodeId ? knownFile?.nodes[nodeId] ?? "指定節點" : "",
      pages: knownFile?.pages ?? [],
      normalizedUrl,
    };
  } catch {
    return { ...EMPTY_FIGMA_SOURCE, mode: "invalid", normalizedUrl };
  }
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
  const [draftFigmaUrl, setDraftFigmaUrl] = useState("");
  const [appliedFigmaUrl, setAppliedFigmaUrl] = useState("");
  const [isEditingSource, setIsEditingSource] = useState(true);
  const [scope, setScope] = useState<Scope>("file");
  const [selectedPageId, setSelectedPageId] = useState("");
  const [filter, setFilter] = useState<EventFilter>("All");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(events[0].id);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [analysisState, setAnalysisState] = useState("尚未提供 Figma 連結");

  const draftInfo = useMemo(() => parseFigmaUrl(draftFigmaUrl), [draftFigmaUrl]);
  const figmaInfo = useMemo(() => parseFigmaUrl(appliedFigmaUrl), [appliedFigmaUrl]);
  const activeInputInfo = isEditingSource ? draftInfo : figmaInfo;
  const hasAppliedSource = Boolean(appliedFigmaUrl && figmaInfo.mode !== "invalid" && figmaInfo.mode !== "unsupported");
  const hasPageSwitcher = figmaInfo.mode === "file" && figmaInfo.pages.length > 1;
  const selectedPage = figmaInfo.pages.find((page) => page.id === selectedPageId) ?? figmaInfo.pages[0];

  const visibleRows = useMemo(() => {
    if (!hasAppliedSource || !hasAnalyzed) {
      return [];
    }

    const normalizedQuery = query.trim().toLowerCase();
    const allowedEventPages =
      scope === "page" && selectedPage?.relatedEventPages.length ? selectedPage.relatedEventPages : null;

    return events.filter((row) => {
      const scopeMatch =
        scope === "file" ||
        (scope === "page" && (allowedEventPages ? allowedEventPages.includes(row.page) : row.page !== "全站")) ||
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
  }, [filter, hasAnalyzed, hasAppliedSource, query, scope, selectedPage]);

  const selectedRow = visibleRows.find((row) => row.id === selectedId) ?? visibleRows[0];

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

  function getScopeLabel() {
    if (scope === "node") {
      return figmaInfo.nodeName || "指定節點";
    }

    if (scope === "page") {
      return selectedPage?.name ?? "指定 Page";
    }

    return "整份檔案";
  }

  function handleApplySource() {
    const nextInfo = parseFigmaUrl(draftFigmaUrl);

    if (nextInfo.mode === "empty") {
      setAnalysisState("請先貼上 Figma 設計檔連結");
      return;
    }

    if (nextInfo.mode === "invalid") {
      setAnalysisState("這看起來不是有效的 Figma 連結");
      return;
    }

    if (nextInfo.mode === "unsupported") {
      setAnalysisState("目前請提供 Figma design/file 連結；簡報 deck 可作欄位參考，但不作頁面分析");
      return;
    }

    setAppliedFigmaUrl(nextInfo.normalizedUrl);
    setDraftFigmaUrl(nextInfo.normalizedUrl);
    setIsEditingSource(false);
    setHasAnalyzed(false);
    setScope(nextInfo.mode === "node" ? "node" : "file");
    setSelectedPageId(nextInfo.pages[0]?.id ?? "");
    setFilter("All");
    setQuery("");
    setSelectedId(events[0].id);
    setAnalysisState(
      nextInfo.mode === "node"
        ? "已套用指定節點，Page 選擇已隱藏"
        : nextInfo.pages.length > 1
          ? "已套用整份檔案，可切換 Page 或分析整份檔案"
          : "已套用整份檔案，未偵測到多個可切換 Page",
    );
  }

  function handleReplaceSource() {
    setDraftFigmaUrl(appliedFigmaUrl);
    setIsEditingSource(true);
    setAnalysisState("正在替換 Figma 來源，套用後會重置分析結果");
  }

  function handleClearSource() {
    setDraftFigmaUrl("");
    setAppliedFigmaUrl("");
    setIsEditingSource(true);
    setScope("file");
    setSelectedPageId("");
    setFilter("All");
    setQuery("");
    setSelectedId(events[0].id);
    setHasAnalyzed(false);
    setAnalysisState("尚未提供 Figma 連結");
  }

  function handleAnalyze() {
    if (!hasAppliedSource) {
      setAnalysisState("請先套用 Figma 連結");
      return;
    }

    setHasAnalyzed(true);
    setAnalysisState(
      `已產生「${getScopeLabel()}」的第一階段埋點建議`,
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

            {isEditingSource ? (
              <div className="source-editor">
                <label className="field-label" htmlFor="figma-url">
                  Figma 連結
                </label>
                <textarea
                  id="figma-url"
                  value={draftFigmaUrl}
                  onChange={(event) => setDraftFigmaUrl(event.target.value)}
                  placeholder="貼上 Figma design/file 連結"
                  rows={5}
                />
                {activeInputInfo.mode === "empty" ? (
                  <div className="source-empty">
                    <strong>尚未套用來源</strong>
                    <span>貼上連結後會解析 file key、node-id 與可切換範圍。</span>
                  </div>
                ) : (
                  <div className={`figma-meta source-${activeInputInfo.mode}`}>
                    <span>File key</span>
                    <strong>{activeInputInfo.fileKey || "未解析"}</strong>
                    <span>類型</span>
                    <strong>
                      {activeInputInfo.mode === "node"
                        ? "指定節點"
                        : activeInputInfo.mode === "file"
                          ? "整份檔案"
                          : activeInputInfo.mode === "unsupported"
                            ? "不支援"
                            : "格式錯誤"}
                    </strong>
                    {activeInputInfo.nodeId ? (
                      <>
                        <span>Node</span>
                        <strong>{activeInputInfo.nodeId}</strong>
                      </>
                    ) : null}
                  </div>
                )}
                <div className="source-actions">
                  <button className="primary-button" type="button" onClick={handleApplySource}>
                    套用連結
                  </button>
                  <button className="secondary-button" type="button" onClick={handleClearSource}>
                    清空
                  </button>
                </div>
              </div>
            ) : (
              <div className="source-card">
                <div>
                  <span>已套用來源</span>
                  <strong>{figmaInfo.fileName}</strong>
                  <code>{figmaInfo.normalizedUrl}</code>
                </div>
                <div className="figma-meta compact">
                  <span>File key</span>
                  <strong>{figmaInfo.fileKey}</strong>
                  {figmaInfo.nodeId ? (
                    <>
                      <span>Node</span>
                      <strong>{figmaInfo.nodeId}</strong>
                    </>
                  ) : (
                    <>
                      <span>Pages</span>
                      <strong>{figmaInfo.pages.length > 1 ? `${figmaInfo.pages.length} pages` : "無需切換"}</strong>
                    </>
                  )}
                </div>
                <div className="source-actions">
                  <button className="secondary-button" type="button" onClick={handleReplaceSource}>
                    替換連結
                  </button>
                  <button className="secondary-button danger-button" type="button" onClick={handleClearSource}>
                    清空
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="panel-section">
            <div className="section-heading">
              <span className="section-index">02</span>
              <h2>分析範圍</h2>
            </div>
            {!hasAppliedSource ? (
              <div className="scope-empty">
                <strong>等待來源</strong>
                <span>套用 Figma 連結後才會顯示可分析範圍。</span>
              </div>
            ) : (
              <div className="scope-list" role="radiogroup" aria-label="分析範圍">
                {figmaInfo.mode === "file" ? (
                  <button
                    className={scope === "file" ? "scope-option active" : "scope-option"}
                    type="button"
                    onClick={() => {
                      setScope("file");
                      setHasAnalyzed(false);
                      setAnalysisState("已切換為整份檔案，請重新分析頁面內容");
                    }}
                    aria-pressed={scope === "file"}
                  >
                    <span>整份檔案</span>
                    <small>第一層功能使用率</small>
                  </button>
                ) : null}

                {hasPageSwitcher ? (
                  <button
                    className={scope === "page" ? "scope-option active" : "scope-option"}
                    type="button"
                    onClick={() => {
                      setScope("page");
                      setHasAnalyzed(false);
                      setAnalysisState("已切換為指定 Page，請重新分析頁面內容");
                    }}
                    aria-pressed={scope === "page"}
                  >
                    <span>指定 Page</span>
                    <small>{selectedPage?.name ?? "請選擇 Page"}</small>
                  </button>
                ) : null}

                {figmaInfo.mode === "node" ? (
                  <button className="scope-option active" type="button" aria-pressed="true">
                    <span>指定節點</span>
                    <small>{figmaInfo.nodeName || figmaInfo.nodeId}</small>
                  </button>
                ) : null}
              </div>
            )}

            {hasPageSwitcher ? (
              <label className={scope === "page" ? "page-picker active" : "page-picker"}>
                <span>Page</span>
                <select
                  value={selectedPageId}
                  onChange={(event) => {
                    setSelectedPageId(event.target.value);
                    setScope("page");
                    setHasAnalyzed(false);
                    setAnalysisState("已切換 Page，請重新分析頁面內容");
                  }}
                >
                  {figmaInfo.pages.map((page) => (
                    <option key={page.id} value={page.id}>
                      {page.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <button
              className="primary-button full-width"
              type="button"
              onClick={handleAnalyze}
              disabled={!hasAppliedSource}
            >
              分析頁面內容
            </button>
            <p className={hasAppliedSource ? "analysis-state" : "analysis-state muted-state"}>{analysisState}</p>
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
                disabled={!hasAnalyzed}
              />
              <select
                aria-label="事件類型篩選"
                value={filter}
                onChange={(event) => setFilter(event.target.value as EventFilter)}
                disabled={!hasAnalyzed}
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
                {visibleRows.length === 0 ? (
                  <tr>
                    <td colSpan={8}>
                      <div className="table-empty">
                        <strong>{hasAppliedSource ? "尚未產生埋點建議" : "尚未套用 Figma 來源"}</strong>
                        <span>{hasAppliedSource ? "按下分析頁面內容後會列出事件。" : "左側套用連結後再開始分析。"}</span>
                      </div>
                    </td>
                  </tr>
                ) : null}
                {visibleRows.map((row) => (
                  <tr
                    key={row.id}
                    className={selectedRow?.id === row.id ? "selected" : ""}
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
          {selectedRow ? (
            <>
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
            </>
          ) : (
            <div className="detail-empty">
              <strong>尚未選取事件</strong>
              <span>分析完成後，點擊表格中的事件即可查看屬性與追蹤目的。</span>
            </div>
          )}
          <div className="privacy-note">
            <strong>資料邊界</strong>
            <p>第一階段建議使用去識別化事件屬性，不把病患姓名、身分證、病歷號或完整聯絡資訊放入事件 payload。</p>
          </div>
        </aside>
      </section>
    </main>
  );
}
