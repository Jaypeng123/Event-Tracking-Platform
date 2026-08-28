"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type TrackingEvent = {
  id: string;
  page: string;
  area: string;
  eventName: string;
  eventType: "PageView" | "Click" | "SearchFilter" | "FlowComplete" | "CreateEdit" | "ErrorDropoff" | "ExportDownload";
  trigger: string;
  purpose: string;
  analysisValue: string;
  metricCalculation: string;
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
type PriorityFilter = "All" | TrackingEvent["priority"];
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

type OpenAIModelOption = {
  id: string;
  label: string;
  note: string;
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
  { value: "PageView", label: "頁面曝光" },
  { value: "Click", label: "功能點擊" },
  { value: "SearchFilter", label: "篩選／搜尋" },
  { value: "FlowComplete", label: "流程完成" },
  { value: "CreateEdit", label: "編輯／建立" },
  { value: "ErrorDropoff", label: "錯誤／流失" },
  { value: "ExportDownload", label: "匯出／下載" },
];

const priorityOptions: Array<{ value: PriorityFilter; label: string }> = [
  { value: "All", label: "全部" },
  { value: "P0", label: "P0" },
  { value: "P1", label: "P1" },
  { value: "P2", label: "P2" },
];

const priorityDescriptions: Record<TrackingEvent["priority"], string> = {
  P0: "第一階段沒有這支，就無法回答核心產品問題",
  P1: "有助於理解使用情境與功能價值",
  P2: "微互動與細節優化",
};

const openAIModelOptions: OpenAIModelOption[] = [
  { id: "gpt-5.6-luna", label: "GPT-5.6 Luna", note: "低成本，適合大量頁面初步分析" },
  { id: "gpt-5.6-terra", label: "GPT-5.6 Terra", note: "品質與成本平衡" },
  { id: "gpt-5.6-sol", label: "GPT-5.6 Sol", note: "較高品質，適合複雜頁面" },
];

const exportColumns: Array<{ key: keyof TrackingEvent; label: string }> = [
  { key: "id", label: "編號" },
  { key: "page", label: "頁面/區塊" },
  { key: "eventName", label: "事件名稱 (En)" },
  { key: "trigger", label: "觸發時機/事件定義 (Trigger/Event Definition)" },
  { key: "purpose", label: "追蹤目的" },
  { key: "analysisValue", label: "分析的原因" },
  { key: "metricCalculation", label: "指標計算" },
  { key: "properties", label: "屬性參數 (Property)" },
  { key: "propertyDefinitions", label: "屬性定義 (Property Definition)" },
  { key: "dataTypes", label: "Data Type" },
  { key: "sampleValues", label: "Sample Values" },
  { key: "priority", label: "優先級" },
  { key: "status", label: "狀態" },
];

const typeLabels: Record<TrackingEvent["eventType"], string> = {
  PageView: "頁面曝光",
  Click: "功能點擊",
  SearchFilter: "篩選／搜尋",
  FlowComplete: "流程完成",
  CreateEdit: "編輯／建立",
  ErrorDropoff: "錯誤／流失",
  ExportDownload: "匯出／下載",
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

function cleanScopeName(value: string, fallback = "Figma 分析範圍") {
  const layerNoisePattern = /^(Arrow|Vector|Rectangle|ScrollerBar|ScrollBar|Action Button|Icon)\s*\d*$/i;
  const cleaned = value
    .replace(/[（(]\s*\d+(?:\.\d+)?(?:\s*[~～\-–—]\s*\d+(?:\.\d+)?)?\s*[）)]/g, "")
    .replace(/\s+\d+(?:\.\d+)?(?:\s*[~～\-–—]\s*\d+(?:\.\d+)?)?\s*$/g, "")
    .split("/")
    .map((segment) => segment.trim())
    .filter((segment) => segment && !layerNoisePattern.test(segment))
    .join(" / ")
    .replace(/\s{2,}/g, " ")
    .trim();

  return cleaned || fallback;
}

function normalizeFigmaPage(page: FigmaPage): FigmaPage {
  return {
    ...page,
    name: cleanScopeName(page.name, "未命名 Page"),
    relatedEventPages: page.relatedEventPages?.map((name) => cleanScopeName(name, name)),
  };
}

function coerceEventType(value: unknown): TrackingEvent["eventType"] {
  switch (String(value)) {
    case "PageView":
    case "View":
      return "PageView";
    case "SearchFilter":
      return "SearchFilter";
    case "FlowComplete":
    case "Flow":
      return "FlowComplete";
    case "CreateEdit":
      return "CreateEdit";
    case "ErrorDropoff":
    case "Validation":
      return "ErrorDropoff";
    case "ExportDownload":
      return "ExportDownload";
    case "Click":
    case "Feature":
    default:
      return "Click";
  }
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
      nodeName: nodeId ? cleanScopeName(knownFile?.nodes[nodeId] ?? "指定節點", "指定節點") : "",
      pages: knownFile?.pages.map(normalizeFigmaPage) ?? [],
      normalizedUrl,
    };
  } catch {
    return { ...EMPTY_FIGMA_SOURCE, mode: "invalid", normalizedUrl };
  }
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

function normalizeStoredEvent(row: SavedTrackingEvent): SavedTrackingEvent {
  return {
    ...row,
    page: cleanScopeName(row.page, "Figma 分析範圍"),
    area: cleanScopeName(row.area, row.page || "主要區塊"),
    eventType: coerceEventType(row.eventType),
    metricCalculation:
      typeof row.metricCalculation === "string" && row.metricCalculation.trim()
        ? row.metricCalculation.trim()
        : "事件 UV ÷ 平台活躍 UV",
    sourceName: cleanScopeName(row.sourceName, row.sourceName || "Figma 來源"),
  };
}

function readStoredEventLibrary() {
  try {
    const storedLibrary = window.localStorage.getItem(EVENT_LIBRARY_STORAGE_KEY);
    const parsed = storedLibrary ? JSON.parse(storedLibrary) : [];

    return Array.isArray(parsed) ? parsed.filter(isTrackingEventLike).map(normalizeStoredEvent) : [];
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
      <Column ss:Width="220"/>
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
  const [loadedPages, setLoadedPages] = useState<FigmaPage[]>([]);
  const [selectedPageId, setSelectedPageId] = useState("");
  const [isPageMenuOpen, setIsPageMenuOpen] = useState(false);
  const [hasImportedPages, setHasImportedPages] = useState(false);
  const [isLoadingPages, setIsLoadingPages] = useState(false);
  const [pageLoadError, setPageLoadError] = useState("");
  const [filter, setFilter] = useState<EventFilter>("All");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("All");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedOpenAIModel, setSelectedOpenAIModel] = useState(openAIModelOptions[0].id);
  const [analysisRows, setAnalysisRows] = useState<TrackingEvent[]>([]);
  const [analysisError, setAnalysisError] = useState("");
  const [, setAnalysisState] = useState("尚未提供 Figma 連結");
  const [libraryRows, setLibraryRows] = useState<SavedTrackingEvent[]>([]);
  const [hasLoadedLibrary, setHasLoadedLibrary] = useState(false);
  const [isLibraryOpen, setIsLibraryOpen] = useState(false);
  const [libraryQuery, setLibraryQuery] = useState("");
  const [libraryTypeFilter, setLibraryTypeFilter] = useState<EventFilter>("All");
  const [libraryPriorityFilter, setLibraryPriorityFilter] = useState<PriorityFilter>("All");
  const [librarySourceFilter, setLibrarySourceFilter] = useState("All");
  const [isClearLibraryConfirmOpen, setIsClearLibraryConfirmOpen] = useState(false);
  const [editingLibraryId, setEditingLibraryId] = useState("");
  const [libraryDraft, setLibraryDraft] = useState<SavedTrackingEvent | null>(null);
  const analysisRunId = useRef(0);
  const pageSelectRef = useRef<HTMLDivElement | null>(null);

  const draftInfo = useMemo(() => parseFigmaUrl(draftFigmaUrl), [draftFigmaUrl]);
  const figmaInfo = useMemo(() => parseFigmaUrl(appliedFigmaUrl), [appliedFigmaUrl]);
  const hasDraftSource = Boolean(draftFigmaUrl.trim());
  const hasAppliedSource = Boolean(appliedFigmaUrl && figmaInfo.mode !== "invalid" && figmaInfo.mode !== "unsupported");
  const activeInputInfo = hasAppliedSource ? figmaInfo : draftInfo;
  const pageOptions = hasImportedPages ? loadedPages : [];
  const selectedPage = pageOptions.find((page) => page.id === selectedPageId) ?? null;
  const needsPageSelection = hasAppliedSource;
  const canShowPageSelector =
    hasAppliedSource && (needsPageSelection || isLoadingPages || Boolean(pageOptions.length) || Boolean(pageLoadError));
  const canAnalyzeCurrentSource =
    hasAppliedSource && !isLoadingPages && hasImportedPages && Boolean(selectedPage);
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

  useEffect(() => {
    if (!isPageMenuOpen) {
      return;
    }

    function handleOutsidePointerDown(event: PointerEvent) {
      const target = event.target;

      if (target instanceof Node && pageSelectRef.current && !pageSelectRef.current.contains(target)) {
        setIsPageMenuOpen(false);
      }
    }

    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsPageMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", handleOutsidePointerDown);
    document.addEventListener("keydown", handleEscapeKey);

    return () => {
      document.removeEventListener("pointerdown", handleOutsidePointerDown);
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [isPageMenuOpen]);

  const visibleRows = useMemo(() => {
    if (!hasAppliedSource || !hasAnalyzed) {
      return [];
    }

    const normalizedQuery = query.trim().toLowerCase();

    return analysisRows.filter((row) => {
      const typeMatch = filter === "All" || row.eventType === filter;
      const priorityMatch = priorityFilter === "All" || row.priority === priorityFilter;
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
          row.metricCalculation,
          row.properties,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      return typeMatch && priorityMatch && queryMatch;
    });
  }, [analysisRows, filter, hasAnalyzed, hasAppliedSource, priorityFilter, query]);

  const librarySourceOptions = useMemo(
    () => Array.from(new Set(libraryRows.map((row) => cleanScopeName(row.sourceName, "Figma 來源")).filter(Boolean))),
    [libraryRows],
  );
  const effectiveLibrarySourceFilter =
    librarySourceFilter === "All" || librarySourceOptions.includes(librarySourceFilter) ? librarySourceFilter : "All";

  const libraryVisibleRows = useMemo(() => {
    const normalizedQuery = libraryQuery.trim().toLowerCase();

    return libraryRows.filter((row) => {
      const typeMatch = libraryTypeFilter === "All" || row.eventType === libraryTypeFilter;
      const priorityMatch = libraryPriorityFilter === "All" || row.priority === libraryPriorityFilter;
      const sourceMatch =
        effectiveLibrarySourceFilter === "All" ||
        cleanScopeName(row.sourceName, "Figma 來源") === effectiveLibrarySourceFilter;
      const queryMatch =
        !normalizedQuery ||
        [
          row.id,
          row.page,
          row.area,
          row.eventName,
          row.eventType,
          row.trigger,
          row.purpose,
          row.analysisValue,
          row.metricCalculation,
          row.properties,
          row.sourceName,
          row.priority,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      return typeMatch && priorityMatch && sourceMatch && queryMatch;
    });
  }, [effectiveLibrarySourceFilter, libraryPriorityFilter, libraryQuery, libraryRows, libraryTypeFilter]);

  const summary = useMemo(() => {
    const rows = hasAppliedSource && hasAnalyzed ? analysisRows : [];

    return [
      { filter: "All" as const, label: "全部", value: rows.length, note: "目前頁面的埋點候選" },
      {
        filter: "P0" as const,
        label: "P0",
        value: rows.filter((row) => row.priority === "P0").length,
        note: priorityDescriptions.P0,
      },
      {
        filter: "P1" as const,
        label: "P1",
        value: rows.filter((row) => row.priority === "P1").length,
        note: priorityDescriptions.P1,
      },
      {
        filter: "P2" as const,
        label: "P2",
        value: rows.filter((row) => row.priority === "P2").length,
        note: priorityDescriptions.P2,
      },
    ];
  }, [analysisRows, hasAnalyzed, hasAppliedSource]);

  function getLibraryId(row: TrackingEvent) {
    return `evt_${hashText(
      [figmaInfo.fileKey, figmaInfo.nodeId || selectedPageId || "file", row.id, row.page, row.area, row.eventName].join("|"),
    )}`;
  }

  function createLibraryItem(row: TrackingEvent): SavedTrackingEvent {
    return {
      ...row,
      libraryId: getLibraryId(row),
      sourceName: selectedPage
        ? `${cleanScopeName(figmaInfo.fileName, "Figma 來源")} / ${selectedPage.name}`
        : cleanScopeName(figmaInfo.fileName || "Figma 來源", "Figma 來源"),
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

  function handleExportRowsExcel(rows: TrackingEvent[], filename: string) {
    if (!rows.length) {
      return;
    }

    download(filename, toExcelXml(rows), "application/vnd.ms-excel;charset=utf-8");
  }

  function makeSequentialRows(rows: TrackingEvent[]) {
    return rows.map((row, index) => ({
      ...row,
      id: String(index + 1),
      page: cleanScopeName(row.page, "Figma 分析範圍"),
      area: cleanScopeName(row.area, row.page || "主要區塊"),
    }));
  }

  function handleExportLibrary() {
    handleExportRowsExcel(makeSequentialRows(libraryVisibleRows), "追蹤事件庫.xls");
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

  function handleConfirmClearLibrary() {
    setLibraryRows([]);
    setLibraryQuery("");
    setLibraryTypeFilter("All");
    setLibraryPriorityFilter("All");
    setLibrarySourceFilter("All");
    setIsClearLibraryConfirmOpen(false);
    handleCancelLibraryEdit();
  }

  function handleCloseLibrary() {
    setIsLibraryOpen(false);
    setIsClearLibraryConfirmOpen(false);
    handleCancelLibraryEdit();
  }

  function resetAnalysisResult() {
    analysisRunId.current += 1;
    setIsAnalyzing(false);
    setAnalysisRows([]);
    setAnalysisError("");
    setSelectedId("");
    setIsDetailOpen(false);
    setHasAnalyzed(false);
  }

  async function loadFigmaPages(nextInfo: FigmaSourceInfo) {
    if (!nextInfo.fileKey || nextInfo.mode === "empty" || nextInfo.mode === "invalid" || nextInfo.mode === "unsupported") {
      setLoadedPages([]);
      setSelectedPageId("");
      setHasImportedPages(false);
      setPageLoadError("");
      return;
    }

    setIsLoadingPages(true);
    setLoadedPages([]);
    setSelectedPageId("");
    setHasImportedPages(false);
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

      const pages = Array.isArray(result.pages) ? result.pages.map(normalizeFigmaPage) : [];

      setLoadedPages(pages);
      setSelectedPageId("");
      setIsPageMenuOpen(false);
      setHasImportedPages(true);
      setPageLoadError(pages.length ? "" : "這份 Figma 檔案沒有讀到可分析的 Page");
      setAnalysisState("");
    } catch (error) {
      const message = error instanceof Error ? error.message : "無法讀取 Figma Page 清單";

      setLoadedPages([]);
      setSelectedPageId("");
      setIsPageMenuOpen(false);
      setHasImportedPages(false);
      setPageLoadError(message);
      setAnalysisState("");
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
    setLoadedPages([]);
    setSelectedPageId("");
    setIsPageMenuOpen(false);
    setHasImportedPages(false);
    setPageLoadError("");
    resetAnalysisResult();
    setFilter("All");
    setPriorityFilter("All");
    setQuery("");
    setAnalysisState("");

    await loadFigmaPages(nextInfo);
  }

  function handleClearSource() {
    setDraftFigmaUrl("");
    setAppliedFigmaUrl("");
    setLoadedPages([]);
    setSelectedPageId("");
    setIsPageMenuOpen(false);
    setHasImportedPages(false);
    setPageLoadError("");
    setFilter("All");
    setPriorityFilter("All");
    setQuery("");
    resetAnalysisResult();
    setAnalysisState("尚未提供 Figma 連結");
  }

  function handleSelectPage(pageId: string) {
    setSelectedPageId(pageId);
    setIsPageMenuOpen(false);
    resetAnalysisResult();
    setAnalysisState(pageId ? "" : "請先選擇要分析的 Page");
  }

  async function handleAnalyze() {
    if (!canAnalyzeCurrentSource) {
      if (!hasAppliedSource) {
        setAnalysisState("請先匯入 Figma 連結");
        return;
      }

      if (isLoadingPages) {
        setAnalysisState("");
        return;
      }

      if (needsPageSelection && !hasImportedPages) {
        setAnalysisState("請先匯入 Figma Page 清單");
        return;
      }

      if (needsPageSelection && !selectedPage) {
        setAnalysisState("請先選擇要分析的 Page");
        return;
      }

      setAnalysisState("請先選擇要分析的 Page");
      return;
    }

    const runId = analysisRunId.current + 1;

    analysisRunId.current = runId;
    setIsAnalyzing(true);
    setAnalysisRows([]);
    setSelectedId("");
    setIsDetailOpen(false);
    setHasAnalyzed(false);
    setAnalysisError("");
    setAnalysisState("");

    try {
      const sourceForAnalysis = selectedPage
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
          ai: {
            provider: "openai",
            openAIModel: selectedOpenAIModel,
          },
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
      setAnalysisState("");
    } catch (error) {
      if (analysisRunId.current !== runId) {
        return;
      }

      const message = error instanceof Error ? error.message : "AI 分析失敗，請稍後再試";

      setAnalysisError(message);
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

  const isWaitingForPageImport = needsPageSelection && !hasImportedPages && !isLoadingPages && !pageLoadError;
  const isWaitingForPageSelection = needsPageSelection && hasImportedPages && Boolean(pageOptions.length) && !selectedPage;
  const hasNoImportedPages = needsPageSelection && hasImportedPages && !pageOptions.length;
  const selectedRow = isDetailOpen ? visibleRows.find((row) => row.id === selectedId) ?? null : null;
  const workspaceDetailClass = selectedRow ? "detail-open" : "detail-hidden";
  const hasNoAnalysisRows =
    hasAppliedSource &&
    hasAnalyzed &&
    !analysisRows.length &&
    !analysisError &&
    !isWaitingForPageImport &&
    !isWaitingForPageSelection &&
    !hasNoImportedPages;
  const hasNoFilteredRows = hasAppliedSource && hasAnalyzed && Boolean(analysisRows.length) && !visibleRows.length;
  const tableEmptyTitle = isAnalyzing
    ? "AI 正在分析頁面內容"
    : analysisError
      ? "分析未完成"
      : isLoadingPages
        ? "正在讀取 Figma 稿件"
        : isWaitingForPageImport
          ? "請先匯入 Figma Page"
          : pageLoadError
            ? "Page 清單尚未完成"
            : isWaitingForPageSelection
              ? "請選擇要分析的 Page"
              : hasNoImportedPages
                ? "沒有可分析的 Page"
                : hasNoAnalysisRows
                  ? "尚無可追蹤的分析指標"
                  : hasNoFilteredRows
                    ? "沒有符合條件的分析指標"
                    : hasAppliedSource
                      ? "尚未產生埋點建議"
                      : "尚未套用 Figma 來源";
  const tableEmptyDescription = isAnalyzing
    ? "正在讀取Figma稿件"
    : analysisError
      ? analysisError
      : isLoadingPages
        ? "正在讀取Figma稿件"
        : isWaitingForPageImport
          ? "整份檔案需要先匯入 Page 清單，選擇單一 Page 後才會分析。"
          : pageLoadError
            ? pageLoadError
            : isWaitingForPageSelection
              ? "請在左側選一個 Page，再點擊 AI 分析。"
              : hasNoImportedPages
                ? "這份 Figma 檔案沒有讀到可選 Page，請確認檔案權限或改貼指定 Page 連結。"
                : hasNoAnalysisRows
                  ? "模型沒有從目前連結範圍判斷出需要第一階段追蹤的事件。"
                  : hasNoFilteredRows
                    ? "請調整搜尋文字、事件類型或優先級篩選。"
                    : hasAppliedSource
                      ? "按下分析頁面內容後會列出事件。"
                      : "左側套用連結後再開始分析。";
  if (isLibraryOpen) {
    return (
      <main className="app-shell library-shell">
        <header className="topbar library-topbar">
          <div className="library-heading-group">
            <button className="icon-button back-button" type="button" onClick={handleCloseLibrary} aria-label="返回工具">
              ‹
            </button>
            <div>
              <p className="eyebrow">Product Analytics</p>
              <h1>追蹤事件庫</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <button
              className="secondary-button danger-button"
              type="button"
              onClick={() => setIsClearLibraryConfirmOpen(true)}
              disabled={!libraryRows.length}
            >
              清除全部事件
            </button>
            <button
              className="primary-button"
              type="button"
              onClick={handleExportLibrary}
              disabled={!libraryVisibleRows.length}
            >
              匯出 Excel
            </button>
          </div>
        </header>

        <section className="library-page" aria-label="追蹤事件庫表格">
          <div className="library-toolbar">
            <div>
              <p className="eyebrow">Selected Events</p>
              <h2>已儲存 {libraryRows.length} 筆追蹤事件</h2>
            </div>
            <div className="toolbar-controls library-controls">
              <label className="filter-field search-field">
                <span>搜尋</span>
                <input
                  aria-label="搜尋追蹤事件庫"
                  placeholder="搜尋事件、頁面或屬性"
                  value={libraryQuery}
                  onChange={(event) => setLibraryQuery(event.target.value)}
                  disabled={!libraryRows.length}
                />
              </label>
              <label className="filter-field">
                <span>事件類型</span>
                <select
                  aria-label="追蹤事件庫事件類型篩選"
                  value={libraryTypeFilter}
                  onChange={(event) => setLibraryTypeFilter(event.target.value as EventFilter)}
                  disabled={!libraryRows.length}
                >
                  {filterOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="filter-field">
                <span>優先級</span>
                <select
                  aria-label="追蹤事件庫優先級篩選"
                  value={libraryPriorityFilter}
                  onChange={(event) => setLibraryPriorityFilter(event.target.value as PriorityFilter)}
                  disabled={!libraryRows.length}
                >
                  {priorityOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="filter-field source-filter">
                <span>來源</span>
                <select
                  aria-label="追蹤事件庫來源篩選"
                  value={effectiveLibrarySourceFilter}
                  onChange={(event) => setLibrarySourceFilter(event.target.value)}
                  disabled={!libraryRows.length || !librarySourceOptions.length}
                >
                  <option value="All">全部</option>
                  {librarySourceOptions.map((sourceName) => (
                    <option key={sourceName} value={sourceName}>
                      {sourceName}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {libraryVisibleRows.length ? (
            <div className="library-table-wrap">
              <table className="library-table">
                <colgroup>
                  <col className="library-col-id" />
                  <col className="library-col-page" />
                  <col className="library-col-event" />
                  <col className="library-col-purpose" />
                  <col className="library-col-analysis" />
                  <col className="library-col-metric" />
                  <col className="library-col-meta" />
                  <col className="library-col-actions" />
                </colgroup>
                <thead>
                  <tr>
                    <th>編號</th>
                    <th>頁面/區塊</th>
                    <th>事件名稱</th>
                    <th>追蹤目的</th>
                    <th>分析的原因</th>
                    <th>指標計算</th>
                    <th>來源/優先級</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {libraryVisibleRows.map((row, index) => (
                    <tr key={row.libraryId}>
                      <td>{index + 1}</td>
                      <td>
                        <strong>{row.area}</strong>
                        <span>{row.page}</span>
                      </td>
                      <td>
                        <code>{row.eventName}</code>
                        <span>{typeLabels[row.eventType]}</span>
                      </td>
                      <td>{row.purpose}</td>
                      <td>{row.analysisValue}</td>
                      <td>{row.metricCalculation}</td>
                      <td>
                        <span>{row.sourceName}</span>
                        <span className={`priority-pill priority-${row.priority.toLowerCase()}`}>{row.priority}</span>
                      </td>
                      <td>
                        <div className="row-actions">
                          <button className="secondary-button small-button" type="button" onClick={() => handleStartLibraryEdit(row)}>
                            編輯
                          </button>
                          <button
                            className="secondary-button small-button danger-button"
                            type="button"
                            onClick={() => handleDeleteLibraryItem(row.libraryId)}
                          >
                            刪除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="library-page-empty">
              <strong>{libraryRows.length ? "沒有符合條件的追蹤事件" : "尚未選取埋點追蹤事項"}</strong>
              <span>
                {libraryRows.length
                  ? "請調整搜尋文字、事件類型、優先級或來源篩選。"
                  : "回到工具頁，在分析結果表格勾選事件後，會加入這裡並保留到你自行刪除。"}
              </span>
            </div>
          )}
        </section>

        {libraryDraft ? (
          <div className="library-drawer-layer" role="dialog" aria-modal="true" aria-label="編輯追蹤事件">
            <button className="drawer-scrim" type="button" onClick={handleCancelLibraryEdit} aria-label="關閉編輯抽屜" />
            <aside className="library-drawer">
              <div className="library-drawer-header">
                <div>
                  <p className="eyebrow">Edit Event</p>
                  <h2>編輯追蹤事件</h2>
                </div>
                <button className="icon-button" type="button" onClick={handleCancelLibraryEdit} aria-label="關閉編輯">
                  ×
                </button>
              </div>

              <div className="library-edit-grid drawer-edit-grid">
                <label>
                  頁面/區塊
                  <input
                    value={libraryDraft.page}
                    onChange={(event) => handleUpdateLibraryDraft("page", event.target.value)}
                  />
                </label>
                <label>
                  區塊名稱
                  <input
                    value={libraryDraft.area}
                    onChange={(event) => handleUpdateLibraryDraft("area", event.target.value)}
                  />
                </label>
                <label>
                  事件名稱
                  <input
                    value={libraryDraft.eventName}
                    onChange={(event) => handleUpdateLibraryDraft("eventName", event.target.value)}
                  />
                </label>
                <label>
                  屬性參數
                  <input
                    value={libraryDraft.properties}
                    onChange={(event) => handleUpdateLibraryDraft("properties", event.target.value)}
                  />
                </label>
                <label className="wide-field">
                  觸發時機
                  <textarea
                    value={libraryDraft.trigger}
                    onChange={(event) => handleUpdateLibraryDraft("trigger", event.target.value)}
                    rows={3}
                  />
                </label>
                <label className="wide-field">
                  追蹤目的
                  <textarea
                    value={libraryDraft.purpose}
                    onChange={(event) => handleUpdateLibraryDraft("purpose", event.target.value)}
                    rows={3}
                  />
                </label>
                <label className="wide-field">
                  分析的原因
                  <textarea
                    value={libraryDraft.analysisValue}
                    onChange={(event) => handleUpdateLibraryDraft("analysisValue", event.target.value)}
                    rows={4}
                  />
                </label>
                <label className="wide-field">
                  指標計算
                  <textarea
                    value={libraryDraft.metricCalculation}
                    onChange={(event) => handleUpdateLibraryDraft("metricCalculation", event.target.value)}
                    rows={3}
                  />
                </label>
              </div>

              <div className="library-drawer-actions">
                <button className="primary-button" type="button" onClick={handleSaveLibraryEdit}>
                  儲存
                </button>
                <button className="secondary-button" type="button" onClick={handleCancelLibraryEdit}>
                  取消
                </button>
              </div>
            </aside>
          </div>
        ) : null}

        {isClearLibraryConfirmOpen ? (
          <div className="confirm-layer" role="dialog" aria-modal="true" aria-label="清除全部追蹤事件確認">
            <button
              className="drawer-scrim"
              type="button"
              onClick={() => setIsClearLibraryConfirmOpen(false)}
              aria-label="取消清除全部事件"
            />
            <div className="confirm-dialog">
              <p className="eyebrow">Confirm</p>
              <h2>清除全部事件？</h2>
              <p>會清除追蹤事件庫中的 {libraryRows.length} 筆事件，首頁目前的分析結果不會被刪除。</p>
              <div className="confirm-actions">
                <button className="secondary-button" type="button" onClick={() => setIsClearLibraryConfirmOpen(false)}>
                  取消
                </button>
                <button className="primary-button danger-solid-button" type="button" onClick={handleConfirmClearLibrary}>
                  清除全部
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Product Analytics</p>
          <h1>埋點規劃工具</h1>
        </div>
        <div className="topbar-actions" aria-label="匯出工具">
          <button className="secondary-button library-button" type="button" onClick={() => setIsLibraryOpen(true)}>
            追蹤事件庫
            <span>{libraryRows.length}</span>
          </button>
          <button className="primary-button" type="button" onClick={handleExportExcel} disabled={!visibleRows.length}>
            匯出 Excel
          </button>
        </div>
      </header>

      <section className={`workspace ${workspaceDetailClass}`}>
        <aside className="control-panel" aria-label="Figma 分析控制台">
          <div className="panel-section">
            <div className="section-heading">
              <span className="section-index">01</span>
              <h2>Figma 來源</h2>
            </div>

            <div className="source-editor">
              <label className="field-label" htmlFor="figma-url">
                Figma 連結
              </label>
              <textarea
                id="figma-url"
                value={draftFigmaUrl}
                onChange={(event) => setDraftFigmaUrl(event.target.value)}
                placeholder="貼上 Figma design/file 連結"
                rows={3}
                disabled={hasAppliedSource || isLoadingPages}
              />
              {hasAppliedSource ? (
                <div className="source-empty source-locked">
                  <strong>已匯入來源</strong>
                  <span>{cleanScopeName(figmaInfo.fileName, "Figma 來源")}。若要更換連結，請點擊更換 Figma 來源。</span>
                </div>
              ) : activeInputInfo.mode === "empty" ? (
                <div className="source-empty">
                  <strong>尚未匯入來源</strong>
                  <span>貼上 Figma 連結後按下匯入，系統會先讀取可分析的頁面範圍。</span>
                </div>
              ) : (
                <div className={`source-empty source-${activeInputInfo.mode}`}>
                  <strong>
                    {activeInputInfo.mode === "node"
                      ? "將匯入這份 Figma 稿件"
                      : activeInputInfo.mode === "file"
                        ? "將匯入整份檔案"
                        : activeInputInfo.mode === "unsupported"
                          ? "目前不支援這種 Figma 來源"
                          : "這看起來不是有效的 Figma 連結"}
                  </strong>
                  <span>
                    {activeInputInfo.mode === "file" || activeInputInfo.mode === "node"
                      ? "匯入後會列出 Page，請選定一頁再進行 AI 分析。"
                      : "請改貼 Figma design/file 連結。"}
                  </span>
                </div>
              )}
              <div className="source-actions single-action">
                {hasAppliedSource ? (
                  <button className="secondary-button danger-button" type="button" onClick={handleClearSource}>
                    更換 Figma 來源
                  </button>
                ) : (
                  <>
                    <button
                      className="primary-button"
                      type="button"
                      onClick={handleApplySource}
                      disabled={!hasDraftSource || isLoadingPages}
                    >
                      匯入
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {hasAppliedSource ? (
            <div className="panel-section">
            <div className="section-heading">
              <span className="section-index">02</span>
              <h2>AI 分析</h2>
            </div>

            {canShowPageSelector ? (
              <div className={`page-selector ${pageLoadError ? "page-selector-error" : ""}`}>
                <div className="analysis-fields">
                  <div className="analysis-field page-field">
                    <label className="field-label" htmlFor="figma-page">
                      分析 Page
                    </label>
                    {isLoadingPages ? (
                      <div className="source-empty">
                        <strong>正在讀取 Figma 稿件</strong>
                        <span>正在讀取Figma稿件</span>
                      </div>
                    ) : pageOptions.length ? (
                      <div className={`page-select ${isPageMenuOpen ? "open" : ""}`} id="figma-page" ref={pageSelectRef}>
                        <button
                          className="page-select-trigger"
                          type="button"
                          onClick={() => setIsPageMenuOpen((current) => !current)}
                          disabled={!pageOptions.length || isAnalyzing}
                          aria-expanded={isPageMenuOpen}
                          aria-haspopup="listbox"
                        >
                          <span>{selectedPage?.name ?? "請選擇 Page"}</span>
                          <span className="page-select-arrow" aria-hidden="true">
                            ▾
                          </span>
                        </button>
                        {isPageMenuOpen ? (
                          <div className="page-select-menu" role="listbox" aria-label="分析 Page">
                            {pageOptions.map((page) => (
                              <button
                                className={page.id === selectedPageId ? "page-select-option selected" : "page-select-option"}
                                key={page.id}
                                type="button"
                                role="option"
                                aria-selected={page.id === selectedPageId}
                                onClick={() => handleSelectPage(page.id)}
                              >
                                <span>{page.name}</span>
                              </button>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <div className="source-empty">
                        <strong>{hasImportedPages ? "尚未讀到 Page" : "尚未匯入 Page"}</strong>
                        <span>
                          {hasImportedPages
                            ? "請確認 Figma 權限，或改貼指定 Page / 節點連結。"
                            : "匯入 Figma 來源後，會列出這份檔案中的 Page。"}
                        </span>
                      </div>
                    )}
                  </div>

                  <label className="analysis-field compact-model-field">
                    <span>分析模型</span>
                    <select
                      aria-label="分析模型"
                      value={selectedOpenAIModel}
                      onChange={(event) => setSelectedOpenAIModel(event.target.value)}
                      disabled={isAnalyzing}
                    >
                      {openAIModelOptions.map((option) => (
                        <option key={option.id} value={option.id}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                {pageOptions.length && !isLoadingPages ? (
                  <span>已載入 {pageOptions.length} 個 Page；選定 Page 後只會分析該頁，避免一次分析整份檔案。</span>
                ) : null}
                {pageLoadError ? <span className="page-selector-message">{pageLoadError}</span> : null}
              </div>
            ) : null}

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
                "讀取中"
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
              </div>
            ) : null}
            {analysisError ? <p className="analysis-state error-state">{analysisError}</p> : null}
            </div>
          ) : null}
        </aside>

        <section className="main-panel" aria-label="埋點事件清單">
          <div className="summary-grid" aria-label="分析摘要">
            {summary.map((item) => (
              <button
                className={`summary-item ${priorityFilter === item.filter ? "active" : ""}`}
                key={item.label}
                type="button"
                onClick={() => setPriorityFilter(item.filter)}
                disabled={!hasAnalyzed || isAnalyzing || !analysisRows.length}
              >
                <span>{item.label}</span>
                <strong>{item.value}</strong>
                <small>{item.note}</small>
              </button>
            ))}
          </div>

          <div className="table-toolbar">
            <div>
              <p className="eyebrow">Event Plan</p>
              <h2>第一階段埋點建議</h2>
            </div>
            <div className="toolbar-controls">
              <label className="filter-field search-field">
                <span>搜尋</span>
                <input
                  aria-label="搜尋事件"
                  placeholder="搜尋事件、頁面或屬性"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  disabled={!hasAnalyzed || isAnalyzing || !analysisRows.length}
                />
              </label>
              <label className="filter-field">
                <span>事件類型</span>
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
              </label>
              <label className="filter-field">
                <span>優先級</span>
                <select
                  aria-label="優先級篩選"
                  value={priorityFilter}
                  onChange={(event) => setPriorityFilter(event.target.value as PriorityFilter)}
                  disabled={!hasAnalyzed || isAnalyzing || !analysisRows.length}
                >
                  {priorityOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <div className="event-table-wrap">
            <table className="event-table">
              <colgroup>
                <col className="event-col-select" />
                <col className="event-col-id" />
                <col className="event-col-page" />
                <col className="event-col-name" />
                <col className="event-col-trigger" />
                <col className="event-col-purpose" />
                <col className="event-col-analysis" />
                <col className="event-col-metric" />
                <col className="event-col-properties" />
                <col className="event-col-priority" />
              </colgroup>
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
                  <th>分析的原因</th>
                  <th>指標計算</th>
                  <th>屬性參數</th>
                  <th>優先級</th>
                </tr>
              </thead>
              <tbody>
                {visibleRows.length === 0 ? (
                  <tr className="empty-row">
                    <td colSpan={10}>
                      <div className={`table-empty ${isAnalyzing ? "plain-loading" : ""}`}>
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
                      <td>{row.metricCalculation}</td>
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

        {selectedRow ? (
          <aside className="detail-panel expanded" aria-label="事件詳情">
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
                    <dt>分析的原因</dt>
                    <dd>{selectedRow.analysisValue}</dd>
                  </div>
                  <div>
                    <dt>指標計算</dt>
                    <dd>{selectedRow.metricCalculation}</dd>
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
              </>
          </aside>
        ) : null}
      </section>
    </main>
  );
}
