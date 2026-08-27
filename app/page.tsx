"use client";

import { useEffect, useMemo, useRef, useState } from "react";

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

type SavedTrackingEvent = TrackingEvent & {
  libraryId: string;
  sourceName: string;
  sourceKey: string;
  savedAt: string;
};

type EventFilter = "All" | TrackingEvent["eventType"];
type FigmaSourceMode = "empty" | "file" | "node" | "unsupported" | "invalid";

type FigmaPage = {
  id: string;
  name: string;
  relatedEventPages?: string[];
  childCount?: number;
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

type AnalyzeResponse = {
  events?: TrackingEvent[];
  analysisProcess?: string[];
  model?: string;
  figma?: {
    fileName?: string;
    targetName?: string;
    targetType?: string;
    pages?: string[];
    nodeCount?: number;
    textCount?: number;
  };
  message?: string;
};

type FigmaPagesResponse = {
  fileName?: string;
  pages?: FigmaPage[];
  message?: string;
};

const EMPTY_FIGMA_SOURCE: FigmaSourceInfo = {
  mode: "empty",
  fileKey: "",
  fileName: "",
  nodeId: "",
  nodeName: "",
  pages: [],
  normalizedUrl: "",
};

const EVENT_LIBRARY_STORAGE_KEY = "tracking-plan-event-library-v1";

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

function hashText(value: string) {
  let hash = 0;

  for (let index = 0; index < value.length; index += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(index);
    hash |= 0;
  }

  return Math.abs(hash).toString(36);
}

function isTrackingEventLike(value: unknown): value is SavedTrackingEvent {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.libraryId === "string" &&
    typeof record.id === "string" &&
    typeof record.page === "string" &&
    typeof record.area === "string" &&
    typeof record.eventName === "string"
  );
}

function readStoredEventLibrary() {
  try {
    const storedLibrary = window.localStorage.getItem(EVENT_LIBRARY_STORAGE_KEY);
    const parsed = storedLibrary ? JSON.parse(storedLibrary) : [];

    return Array.isArray(parsed) ? parsed.filter(isTrackingEventLike) : [];
  } catch {
    return [];
  }
}

async function readAnalyzeResponse(response: Response): Promise<AnalyzeResponse> {
  const contentType = response.headers.get("content-type") ?? "";
  const rawText = await response.text();
  const trimmedText = rawText.trim();
  const looksLikeJson = contentType.includes("application/json") || trimmedText.startsWith("{") || trimmedText.startsWith("[");

  if (looksLikeJson) {
    try {
      return JSON.parse(trimmedText) as AnalyzeResponse;
    } catch {
      return {
        message: `分析 API 回傳了無法解析的 JSON（HTTP ${response.status}），請稍後再試。`,
      };
    }
  }

  if (response.status === 401) {
    return {
      message:
        "分析 API 需要 ChatGPT 登入授權。目前站台是私有權限，請重新整理並完成登入，或將站台改成公開權限後再分析。",
    };
  }

  const readableSnippet = trimmedText
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .slice(0, 120);

  return {
    message: `分析 API 回傳非 JSON 內容（HTTP ${response.status}）。${readableSnippet || "請重新整理後再試。"}`,
  };
}

async function readFigmaPagesResponse(response: Response): Promise<FigmaPagesResponse> {
  const contentType = response.headers.get("content-type") ?? "";
  const rawText = await response.text();
  const trimmedText = rawText.trim();
  const looksLikeJson = contentType.includes("application/json") || trimmedText.startsWith("{") || trimmedText.startsWith("[");

  if (looksLikeJson) {
    try {
      return JSON.parse(trimmedText) as FigmaPagesResponse;
    } catch {
      return { message: `Page 清單 API 回傳了無法解析的 JSON（HTTP ${response.status}）。` };
    }
  }

  if (response.status === 401) {
    return {
      message: "讀取 Page 清單需要 ChatGPT 登入授權。請重新整理並完成登入後再套用連結。",
    };
  }

  return {
    message: `Page 清單 API 回傳非 JSON 內容（HTTP ${response.status}）。請重新整理後再試。`,
  };
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
  const [loadedPages, setLoadedPages] = useState<FigmaPage[]>([]);
  const [selectedPageId, setSelectedPageId] = useState("");
  const [isLoadingPages, setIsLoadingPages] = useState(false);
  const [pageLoadError, setPageLoadError] = useState("");
  const [filter, setFilter] = useState<EventFilter>("All");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisRows, setAnalysisRows] = useState<TrackingEvent[]>([]);
  const [analysisProcess, setAnalysisProcess] = useState<string[]>([]);
  const [analysisError, setAnalysisError] = useState("");
  const [analysisMeta, setAnalysisMeta] = useState<AnalyzeResponse["figma"] | null>(null);
  const [analysisState, setAnalysisState] = useState("尚未提供 Figma 連結");
  const [libraryRows, setLibraryRows] = useState<SavedTrackingEvent[]>([]);
  const [hasLoadedLibrary, setHasLoadedLibrary] = useState(false);
  const [isLibraryOpen, setIsLibraryOpen] = useState(false);
  const [editingLibraryId, setEditingLibraryId] = useState("");
  const [libraryDraft, setLibraryDraft] = useState<SavedTrackingEvent | null>(null);
  const analysisRunId = useRef(0);

  const draftInfo = useMemo(() => parseFigmaUrl(draftFigmaUrl), [draftFigmaUrl]);
  const figmaInfo = useMemo(() => parseFigmaUrl(appliedFigmaUrl), [appliedFigmaUrl]);
  const activeInputInfo = isEditingSource ? draftInfo : figmaInfo;
  const hasAppliedSource = Boolean(appliedFigmaUrl && figmaInfo.mode !== "invalid" && figmaInfo.mode !== "unsupported");
  const pageOptions = loadedPages.length ? loadedPages : figmaInfo.pages;
  const selectedPage = pageOptions.find((page) => page.id === selectedPageId) ?? null;
  const needsPageSelection = hasAppliedSource && figmaInfo.mode === "file";
  const canAnalyzeCurrentSource = hasAppliedSource && !isLoadingPages && (!needsPageSelection || Boolean(selectedPage));

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLibraryRows(readStoredEventLibrary());
      setHasLoadedLibrary(true);
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!hasLoadedLibrary) {
      return;
    }

    window.localStorage.setItem(EVENT_LIBRARY_STORAGE_KEY, JSON.stringify(libraryRows));
  }, [hasLoadedLibrary, libraryRows]);

  const visibleRows = useMemo(() => {
    if (!hasAppliedSource || !hasAnalyzed) {
      return [];
    }

    const normalizedQuery = query.trim().toLowerCase();

    return analysisRows.filter((row) => {
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

      return typeMatch && queryMatch;
    });
  }, [analysisRows, filter, hasAnalyzed, hasAppliedSource, query]);

  const selectedRow = isDetailOpen ? visibleRows.find((row) => row.id === selectedId) ?? null : null;

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

  function getLibraryId(row: TrackingEvent) {
    return `evt_${hashText(
      [figmaInfo.fileKey, figmaInfo.nodeId || selectedPageId || "file", row.id, row.page, row.area, row.eventName].join("|"),
    )}`;
  }

  function createLibraryItem(row: TrackingEvent): SavedTrackingEvent {
    return {
      ...row,
      libraryId: getLibraryId(row),
      sourceName: selectedPage ? `${figmaInfo.fileName} / ${selectedPage.name}` : figmaInfo.fileName || "Figma 來源",
      sourceKey: [figmaInfo.fileKey, figmaInfo.nodeId || selectedPageId || "file"].filter(Boolean).join(" / "),
      savedAt: new Date().toISOString(),
    };
  }

  function isRowInLibrary(row: TrackingEvent) {
    const libraryId = getLibraryId(row);

    return libraryRows.some((item) => item.libraryId === libraryId);
  }

  function handleToggleLibraryRow(row: TrackingEvent, checked: boolean) {
    const libraryId = getLibraryId(row);

    setLibraryRows((currentRows) => {
      if (checked) {
        return currentRows.some((item) => item.libraryId === libraryId)
          ? currentRows
          : [createLibraryItem(row), ...currentRows];
      }

      return currentRows.filter((item) => item.libraryId !== libraryId);
    });
  }

  function handleRowActivate(rowId: string) {
    if (selectedId === rowId && isDetailOpen) {
      setSelectedId("");
      setIsDetailOpen(false);
      return;
    }

    setSelectedId(rowId);
    setIsDetailOpen(true);
  }

  function handleExportRowsCsv(rows: TrackingEvent[], filename: string) {
    if (!rows.length) {
      return;
    }

    download(filename, toCsv(rows), "text/csv;charset=utf-8");
  }

  function handleExportRowsExcel(rows: TrackingEvent[], filename: string) {
    if (!rows.length) {
      return;
    }

    download(filename, toExcelXml(rows), "application/vnd.ms-excel;charset=utf-8");
  }

  function handleStartLibraryEdit(row: SavedTrackingEvent) {
    setEditingLibraryId(row.libraryId);
    setLibraryDraft({ ...row });
  }

  function handleCancelLibraryEdit() {
    setEditingLibraryId("");
    setLibraryDraft(null);
  }

  function handleUpdateLibraryDraft(field: keyof TrackingEvent, value: string) {
    setLibraryDraft((currentDraft) => (currentDraft ? { ...currentDraft, [field]: value } : currentDraft));
  }

  function handleSaveLibraryEdit() {
    if (!libraryDraft) {
      return;
    }

    setLibraryRows((currentRows) =>
      currentRows.map((row) => (row.libraryId === libraryDraft.libraryId ? { ...libraryDraft } : row)),
    );
    handleCancelLibraryEdit();
  }

  function handleDeleteLibraryItem(libraryId: string) {
    setLibraryRows((currentRows) => currentRows.filter((row) => row.libraryId !== libraryId));

    if (editingLibraryId === libraryId) {
      handleCancelLibraryEdit();
    }
  }

  function resetAnalysisResult() {
    analysisRunId.current += 1;
    setIsAnalyzing(false);
    setAnalysisRows([]);
    setAnalysisProcess([]);
    setAnalysisError("");
    setAnalysisMeta(null);
    setSelectedId("");
    setIsDetailOpen(false);
    setHasAnalyzed(false);
  }

  async function loadFigmaPages(nextInfo: FigmaSourceInfo) {
    if (nextInfo.mode !== "file") {
      setLoadedPages([]);
      setSelectedPageId("");
      setPageLoadError("");
      return;
    }

    setIsLoadingPages(true);
    setLoadedPages([]);
    setSelectedPageId("");
    setPageLoadError("");

    try {
      const response = await fetch("/api/figma-pages", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fileKey: nextInfo.fileKey }),
        cache: "no-store",
        credentials: "include",
      });
      const result = await readFigmaPagesResponse(response);

      if (!response.ok) {
        throw new Error(result.message || "無法讀取 Figma Page 清單");
      }

      const pages = Array.isArray(result.pages) ? result.pages : [];

      setLoadedPages(pages);
      setSelectedPageId(pages[0]?.id ?? "");
      setPageLoadError(pages.length ? "" : "這份 Figma 檔案沒有讀到可分析的 Page");
      setAnalysisState(pages.length ? "已匯入 Page 清單，可切換後分析目前選取的 Page" : "這份 Figma 檔案沒有讀到可分析的 Page");
    } catch (error) {
      const message = error instanceof Error ? error.message : "無法讀取 Figma Page 清單";

      setLoadedPages(nextInfo.pages);
      setSelectedPageId(nextInfo.pages[0]?.id ?? "");
      setPageLoadError(message);
      setAnalysisState(message);
    } finally {
      setIsLoadingPages(false);
    }
  }

  async function handleApplySource() {
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
    setLoadedPages(nextInfo.pages);
    setSelectedPageId(nextInfo.mode === "file" ? nextInfo.pages[0]?.id ?? "" : "");
    setPageLoadError("");
    resetAnalysisResult();
    setFilter("All");
    setQuery("");
    setAnalysisState(nextInfo.mode === "file" ? "正在讀取 Figma Page 清單" : "");

    await loadFigmaPages(nextInfo);
  }

  function handleReplaceSource() {
    setDraftFigmaUrl(appliedFigmaUrl);
    setIsEditingSource(true);
    setLoadedPages([]);
    setSelectedPageId("");
    setPageLoadError("");
    resetAnalysisResult();
    setAnalysisState("正在替換 Figma 來源，套用後會重置分析結果");
  }

  function handleClearSource() {
    setDraftFigmaUrl("");
    setAppliedFigmaUrl("");
    setIsEditingSource(true);
    setLoadedPages([]);
    setSelectedPageId("");
    setPageLoadError("");
    setFilter("All");
    setQuery("");
    resetAnalysisResult();
    setAnalysisState("尚未提供 Figma 連結");
  }

  function handleSelectPage(pageId: string) {
    setSelectedPageId(pageId);
    resetAnalysisResult();
    setAnalysisState(pageId ? "" : "請先選擇要分析的 Page");
  }

  async function handleAnalyze() {
    if (!canAnalyzeCurrentSource) {
      if (needsPageSelection && !selectedPage) {
        setAnalysisState(isLoadingPages ? "正在讀取 Figma Page 清單" : "請先選擇要分析的 Page");
        return;
      }

      setAnalysisState("請先套用 Figma 連結");
      return;
    }

    const runId = analysisRunId.current + 1;
    const nextProcess = ["解析 Figma 連結", "讀取 Figma 檔案節點", "呼叫模型判斷追蹤點", "整理成 Excel 欄位格式"];

    analysisRunId.current = runId;
    setIsAnalyzing(true);
    setAnalysisRows([]);
    setSelectedId("");
    setIsDetailOpen(false);
    setHasAnalyzed(false);
    setAnalysisError("");
    setAnalysisMeta(null);
    setAnalysisProcess(nextProcess);
    setAnalysisState("");

    try {
      const sourceForAnalysis =
        figmaInfo.mode === "file" && selectedPage
          ? {
              ...figmaInfo,
              mode: "node",
              nodeId: selectedPage.id,
              nodeName: selectedPage.name,
            }
          : figmaInfo;
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source: sourceForAnalysis,
          scope: sourceForAnalysis.nodeId ? "node" : "file",
        }),
        cache: "no-store",
        credentials: "include",
      });
      const result = await readAnalyzeResponse(response);

      if (analysisRunId.current !== runId) {
        return;
      }

      if (!response.ok) {
        throw new Error(result.message || "AI 分析失敗，請確認環境變數與 Figma 權限");
      }

      const rows = Array.isArray(result.events) ? result.events : [];

      setAnalysisRows(rows);
      setSelectedId("");
      setIsDetailOpen(false);
      setHasAnalyzed(true);
      setAnalysisProcess(
        result.analysisProcess?.length
          ? result.analysisProcess
          : ["讀取 Figma 節點結構", "整理頁面與功能區塊", "判斷第一階段追蹤事件", "輸出 Excel 欄位格式"],
      );
      setAnalysisMeta(result.figma ?? null);
      setAnalysisState("");
    } catch (error) {
      if (analysisRunId.current !== runId) {
        return;
      }

      const message = error instanceof Error ? error.message : "AI 分析失敗，請稍後再試";

      setAnalysisError(message);
      setAnalysisProcess([]);
      setAnalysisState(message);
    } finally {
      if (analysisRunId.current === runId) {
        setIsAnalyzing(false);
      }
    }
  }

  function handleExportExcel() {
    handleExportRowsExcel(visibleRows, "慢病醫療人員_UX_第一階段埋點計畫.xls");
  }

  function handleExportCsv() {
    handleExportRowsCsv(visibleRows, "慢病醫療人員_UX_第一階段埋點計畫.csv");
  }

  const hasNoAnalysisRows = hasAppliedSource && hasAnalyzed && !analysisRows.length && !analysisError;
  const hasNoFilteredRows = hasAppliedSource && hasAnalyzed && Boolean(analysisRows.length) && !visibleRows.length;
  const tableEmptyTitle = isAnalyzing
    ? "AI 正在分析頁面內容"
    : analysisError
      ? "分析未完成"
      : hasNoAnalysisRows
        ? "尚無可追蹤的分析指標"
        : hasNoFilteredRows
          ? "沒有符合條件的分析指標"
          : hasAppliedSource
            ? "尚未產生埋點建議"
            : "尚未套用 Figma 來源";
  const tableEmptyDescription = isAnalyzing
    ? "正在讀取 Figma 結構並呼叫模型。"
    : analysisError
      ? analysisError
      : hasNoAnalysisRows
        ? "模型沒有從目前連結範圍判斷出需要第一階段追蹤的事件。"
        : hasNoFilteredRows
          ? "請調整搜尋文字或事件類型篩選。"
          : hasAppliedSource
            ? "按下分析頁面內容後會列出事件。"
            : "左側套用連結後再開始分析。";
  const detailEmptyTitle = isAnalyzing
    ? "AI 分析中"
    : analysisError
      ? "尚未完成分析"
      : hasNoAnalysisRows
        ? "尚無分析指標"
        : "尚未選取事件";
  const detailEmptyDescription = isAnalyzing
    ? "完成後會自動選取第一筆建議事件。"
    : analysisError
      ? "請修正環境變數或權限後重新分析。"
      : hasNoAnalysisRows
        ? "目前沒有可顯示的事件詳情。"
        : "分析完成後，點擊表格中的事件即可查看屬性與追蹤目的。";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Healthcare Analytics</p>
          <h1>埋點分析建立工具</h1>
        </div>
        <div className="topbar-actions" aria-label="匯出工具">
          <button className="secondary-button" type="button" onClick={handleExportCsv} disabled={!visibleRows.length}>
            CSV
          </button>
          <button className="secondary-button library-button" type="button" onClick={() => setIsLibraryOpen(true)}>
            追蹤事件庫
            <span>{libraryRows.length}</span>
          </button>
          <button className="primary-button" type="button" onClick={handleExportExcel} disabled={!visibleRows.length}>
            匯出 Excel
          </button>
        </div>
      </header>

      {isLibraryOpen ? (
        <div className="library-overlay" role="dialog" aria-modal="true" aria-label="追蹤事件庫">
          <section className="library-panel">
            <div className="library-panel-header">
              <div>
                <p className="eyebrow">Selected Events</p>
                <h2>追蹤事件庫</h2>
              </div>
              <button className="icon-button" type="button" onClick={() => setIsLibraryOpen(false)} aria-label="關閉事件庫">
                ×
              </button>
            </div>

            <div className="library-panel-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={() => handleExportRowsCsv(libraryRows, "追蹤事件庫.csv")}
                disabled={!libraryRows.length}
              >
                匯出 CSV
              </button>
              <button
                className="primary-button"
                type="button"
                onClick={() => handleExportRowsExcel(libraryRows, "追蹤事件庫.xls")}
                disabled={!libraryRows.length}
              >
                匯出 Excel
              </button>
            </div>

            {libraryRows.length ? (
              <div className="library-list">
                {libraryRows.map((row) => {
                  const draft = editingLibraryId === row.libraryId ? libraryDraft : null;

                  return (
                    <article className="library-item" key={row.libraryId}>
                      {draft ? (
                        <>
                          <div className="library-edit-grid">
                            <label>
                              頁面/區塊
                              <input
                                value={draft.page}
                                onChange={(event) => handleUpdateLibraryDraft("page", event.target.value)}
                              />
                            </label>
                            <label>
                              區塊名稱
                              <input
                                value={draft.area}
                                onChange={(event) => handleUpdateLibraryDraft("area", event.target.value)}
                              />
                            </label>
                            <label>
                              事件名稱
                              <input
                                value={draft.eventName}
                                onChange={(event) => handleUpdateLibraryDraft("eventName", event.target.value)}
                              />
                            </label>
                            <label>
                              屬性參數
                              <input
                                value={draft.properties}
                                onChange={(event) => handleUpdateLibraryDraft("properties", event.target.value)}
                              />
                            </label>
                            <label className="wide-field">
                              觸發時機
                              <textarea
                                value={draft.trigger}
                                onChange={(event) => handleUpdateLibraryDraft("trigger", event.target.value)}
                                rows={3}
                              />
                            </label>
                            <label className="wide-field">
                              追蹤目的
                              <textarea
                                value={draft.purpose}
                                onChange={(event) => handleUpdateLibraryDraft("purpose", event.target.value)}
                                rows={3}
                              />
                            </label>
                            <label className="wide-field">
                              分析意義
                              <textarea
                                value={draft.analysisValue}
                                onChange={(event) => handleUpdateLibraryDraft("analysisValue", event.target.value)}
                                rows={3}
                              />
                            </label>
                          </div>
                          <div className="library-item-actions">
                            <button className="primary-button" type="button" onClick={handleSaveLibraryEdit}>
                              儲存
                            </button>
                            <button className="secondary-button" type="button" onClick={handleCancelLibraryEdit}>
                              取消
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="library-item-header">
                            <div>
                              <strong>{row.area}</strong>
                              <span>{row.page}</span>
                            </div>
                            <code>{row.eventName}</code>
                          </div>
                          <p>{row.purpose}</p>
                          <div className="library-item-meta">
                            <span>{row.sourceName}</span>
                            <span>{row.priority}</span>
                            <span>{typeLabels[row.eventType]}</span>
                          </div>
                          <div className="library-item-actions">
                            <button className="secondary-button" type="button" onClick={() => handleStartLibraryEdit(row)}>
                              編輯
                            </button>
                            <button
                              className="secondary-button danger-button"
                              type="button"
                              onClick={() => handleDeleteLibraryItem(row.libraryId)}
                            >
                              刪除
                            </button>
                          </div>
                        </>
                      )}
                    </article>
                  );
                })}
              </div>
            ) : (
              <div className="library-empty">
                <strong>尚未選取埋點追蹤事項</strong>
                <span>在分析結果表格勾選事件後，會加入這裡並保留到你自行刪除。</span>
              </div>
            )}
          </section>
        </div>
      ) : null}

      <section className={`workspace ${isDetailOpen ? "detail-open" : "detail-collapsed"}`}>
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
                    <span>貼上連結後會解析 file key 與 node-id，分析時會依連結本身讀取內容。</span>
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
                      <span>類型</span>
                      <strong>整份檔案</strong>
                    </>
                  )}
                </div>
                {figmaInfo.mode === "file" ? (
                  <div className={`page-selector ${pageLoadError ? "page-selector-error" : ""}`}>
                    <label className="field-label" htmlFor="figma-page">
                      分析 Page
                    </label>
                    {isLoadingPages ? (
                      <div className="source-empty">
                        <strong>正在讀取 Page 清單</strong>
                        <span>這一步只讀 Figma 檔案結構，不會呼叫模型。</span>
                      </div>
                    ) : pageOptions.length ? (
                      <>
                        <select
                          id="figma-page"
                          value={selectedPageId}
                          onChange={(event) => handleSelectPage(event.target.value)}
                        >
                          {pageOptions.map((page) => (
                            <option key={page.id} value={page.id}>
                              {page.name}
                            </option>
                          ))}
                        </select>
                        <span>
                          已載入 {pageOptions.length} 個 Page；分析時只會送出目前選取的 Page，避免一次分析整份檔案。
                        </span>
                      </>
                    ) : (
                      <div className="source-empty">
                        <strong>尚未讀到 Page</strong>
                        <span>請確認 Figma 權限，或改貼指定 Page / 節點連結。</span>
                      </div>
                    )}
                    {pageLoadError ? <span className="page-selector-message">{pageLoadError}</span> : null}
                  </div>
                ) : null}
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
              <h2>AI 分析</h2>
            </div>

            <button
              className="primary-button full-width"
              type="button"
              onClick={handleAnalyze}
              disabled={!canAnalyzeCurrentSource || isAnalyzing}
            >
              {isAnalyzing ? (
                <span className="button-content">
                  <span className="loading-spinner tiny" aria-hidden="true" />
                  分析中
                </span>
              ) : isLoadingPages ? (
                "讀取 Page 中"
              ) : needsPageSelection && !selectedPage ? (
                "請先選擇 Page"
              ) : (
                "分析頁面內容"
              )}
            </button>
            {isAnalyzing ? (
              <div className="analysis-loading" role="status" aria-live="polite">
                <div className="loading-header">
                  <span className="loading-spinner" aria-hidden="true" />
                  <div>
                    <strong>模型分析中</strong>
                    <span>正在讀取 Figma 結構並產出追蹤建議</span>
                  </div>
                </div>
                <ol>
                  {analysisProcess.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </div>
            ) : null}
            {analysisState ? (
              <p
                className={[
                  "analysis-state",
                  !hasAppliedSource ? "muted-state" : "",
                  analysisError ? "error-state" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {analysisState}
              </p>
            ) : null}
            {!isAnalyzing && hasAnalyzed && analysisProcess.length ? (
              <div className="analysis-process">
                <strong>分析流程</strong>
                <ol>
                  {analysisProcess.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
                {analysisMeta ? (
                  <span>
                    已讀取 {analysisMeta.targetName ?? "Figma 節點"}，節點 {analysisMeta.nodeCount ?? 0} 個，文字{" "}
                    {analysisMeta.textCount ?? 0} 筆
                  </span>
                ) : null}
              </div>
            ) : null}
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
                disabled={!hasAnalyzed || isAnalyzing || !analysisRows.length}
              />
              <select
                aria-label="事件類型篩選"
                value={filter}
                onChange={(event) => setFilter(event.target.value as EventFilter)}
                disabled={!hasAnalyzed || isAnalyzing || !analysisRows.length}
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
                  <th className="select-column">
                    <span className="sr-only">選取</span>
                  </th>
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
                    <td colSpan={9}>
                      <div className="table-empty">
                        {isAnalyzing ? <span className="loading-spinner" aria-hidden="true" /> : null}
                        <strong>{tableEmptyTitle}</strong>
                        <span>{tableEmptyDescription}</span>
                      </div>
                    </td>
                  </tr>
                ) : null}
                {visibleRows.map((row) => {
                  const rowInLibrary = isRowInLibrary(row);

                  return (
                    <tr
                      key={row.id}
                      className={selectedRow?.id === row.id ? "selected" : ""}
                      onClick={() => handleRowActivate(row.id)}
                    >
                      <td className="select-column">
                        <input
                          aria-label={`加入追蹤事件庫：${row.eventName}`}
                          checked={rowInLibrary}
                          type="checkbox"
                          onChange={(event) => handleToggleLibraryRow(row, event.target.checked)}
                          onClick={(event) => event.stopPropagation()}
                        />
                      </td>
                      <td>
                        <button
                          className="row-id"
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            handleRowActivate(row.id);
                          }}
                        >
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
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <aside className={`detail-panel ${isDetailOpen ? "expanded" : "collapsed"}`} aria-label="事件詳情">
          {isDetailOpen ? (
            <>
              {selectedRow ? (
                <>
                  <div className="detail-header">
                    <span className={`priority-pill priority-${selectedRow.priority.toLowerCase()}`}>
                      {selectedRow.priority}
                    </span>
                    <code>{selectedRow.eventName}</code>
                    <button
                      className="icon-button detail-toggle"
                      type="button"
                      onClick={() => setIsDetailOpen(false)}
                      aria-label="收合事件詳情"
                    >
                      ›
                    </button>
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
                  {isAnalyzing ? <span className="loading-spinner" aria-hidden="true" /> : null}
                  <strong>{detailEmptyTitle}</strong>
                  <span>{detailEmptyDescription}</span>
                  <button
                    className="icon-button detail-toggle"
                    type="button"
                    onClick={() => setIsDetailOpen(false)}
                    aria-label="收合事件詳情"
                  >
                    ›
                  </button>
                </div>
              )}
              <div className="privacy-note">
                <strong>資料邊界</strong>
                <p>第一階段建議使用去識別化事件屬性，不把病患姓名、身分證、病歷號或完整聯絡資訊放入事件 payload。</p>
              </div>
            </>
          ) : (
            <button
              className="detail-expand-button"
              type="button"
              onClick={() => setIsDetailOpen(true)}
              aria-label="展開事件詳情"
            >
              ‹
            </button>
          )}
        </aside>
      </section>
    </main>
  );
}
