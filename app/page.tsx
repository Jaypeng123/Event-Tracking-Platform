"use client";

import type { PointerEvent as ReactPointerEvent, WheelEvent as ReactWheelEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

type TrackingEvent = {
  id: string;
  page: string;
  area: string;
  metricName: string;
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
  projectId: string;
  sourceName: string;
  sourceKey: string;
  savedAt: string;
};

type EventFilter = "All" | TrackingEvent["eventType"];
type PriorityFilter = "All" | TrackingEvent["priority"];
type FigmaSourceMode = "empty" | "file" | "node" | "unsupported" | "invalid";
type LibraryColumnKey =
  | "index"
  | "priority"
  | "page"
  | "metricName"
  | "purpose"
  | "analysisValue"
  | "trigger"
  | "metricCalculation"
  | "source"
  | "actions";

type StickyTableHeaderState = {
  kind: "analysis" | "library";
  left: number;
  width: number;
  tableWidth: number;
  scrollLeft: number;
};

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

type TrackingProject = {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
};

type ImportedFigmaSource = {
  id: string;
  projectId: string;
  mode: Extract<FigmaSourceMode, "file" | "node">;
  fileKey: string;
  fileName: string;
  nodeId: string;
  nodeName: string;
  normalizedUrl: string;
  pages: FigmaPage[];
  selectedPageId: string;
  importedAt: string;
  updatedAt: string;
  importBehavior?: "auto";
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

type CachedAnalysisResult = {
  rows: TrackingEvent[];
  modelId: string;
  analyzedAt: string;
};

type ModelProvider = "openai" | "gemini";
type AppView = "landing" | "planner";

type AnalysisModelOption = {
  id: string;
  label: string;
  note: string;
  provider: ModelProvider;
  model: string;
};

type FigmaPagesResponse = {
  code?: string;
  fileName?: string;
  mode?: Extract<FigmaSourceMode, "file" | "node">;
  nodeId?: string;
  nodeName?: string;
  pages?: FigmaPage[];
  oauthConfigured?: boolean;
  tokenSource?: "user" | "oauth" | "site";
  message?: string;
};

type FigmaOAuthStatus = {
  configured: boolean;
  available: boolean;
  connected: boolean;
  siteTokenConfigured: boolean;
  unavailableReason: string;
  isLoaded: boolean;
};

type FigmaOAuthStartResponse = {
  code?: string;
  authorizationUrl?: string;
  message?: string;
};

type FigmaPagesLoadResult = {
  pages: FigmaPage[];
  sourceInfo: FigmaSourceInfo;
  authErrorMessage?: string;
  requiresOAuth?: boolean;
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
const PROJECTS_STORAGE_KEY = "tracking-plan-projects-v1";
const ACTIVE_PROJECT_STORAGE_KEY = "tracking-plan-active-project-v1";
const FIGMA_SOURCES_STORAGE_KEY = "tracking-plan-figma-sources-v1";
const PENDING_FIGMA_IMPORT_STORAGE_KEY = "tracking-plan-pending-figma-import-v1";
const ANALYSIS_RESULTS_STORAGE_KEY = "tracking-plan-analysis-results-v1";
const LEGACY_PROJECT_ID = "legacy-project";
const FIGMA_OAUTH_SETUP_REQUIRED_MESSAGE =
  "此站台尚未完成 Figma OAuth 設定。請平台管理者先設定 FIGMA_OAUTH_CLIENT_ID 與 FIGMA_OAUTH_CLIENT_SECRET，使用者才能在這裡授權。";
const FIGMA_OAUTH_UNAVAILABLE_MESSAGE =
  "Figma OAuth app 尚未通過公開審核，外部 Figma 帳號暫時無法授權。平台會先使用站台預設 Figma 權限讀取稿件。";

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

const analysisModelOptions: AnalysisModelOption[] = [
  {
    id: "openai:gpt-5.6-luna",
    label: "GPT-5.6 Luna",
    note: "低成本，適合大量頁面初步分析",
    provider: "openai",
    model: "gpt-5.6-luna",
  },
  {
    id: "openai:gpt-5.6-terra",
    label: "GPT-5.6 Terra",
    note: "品質與成本平衡",
    provider: "openai",
    model: "gpt-5.6-terra",
  },
  {
    id: "openai:gpt-5.6-sol",
    label: "GPT-5.6 Sol",
    note: "較高品質，適合複雜頁面",
    provider: "openai",
    model: "gpt-5.6-sol",
  },
  {
    id: "gemini:gemini-3.7-flash",
    label: "Gemini 3.7 Flash",
    note: "適合快速產出第一版埋點建議",
    provider: "gemini",
    model: "gemini-3.7-flash",
  },
  {
    id: "gemini:gemini-3.6-flash",
    label: "Gemini 3.6 Flash",
    note: "穩定、平衡的 Gemini 分析模型",
    provider: "gemini",
    model: "gemini-3.6-flash",
  },
  {
    id: "gemini:gemini-3.5-flash",
    label: "Gemini 3.5 Flash",
    note: "適合一般頁面的穩定分析",
    provider: "gemini",
    model: "gemini-3.5-flash",
  },
  {
    id: "gemini:gemini-3.5-flash-lite",
    label: "Gemini 3.5 Flash Lite",
    note: "低成本，適合輕量頁面掃描",
    provider: "gemini",
    model: "gemini-3.5-flash-lite",
  },
];

const libraryColumnConfig: Array<{ key: LibraryColumnKey; label: string; width: number; minWidth: number }> = [
  { key: "index", label: "編號", width: 72, minWidth: 56 },
  { key: "priority", label: "優先級", width: 112, minWidth: 92 },
  { key: "page", label: "頁面/區塊", width: 220, minWidth: 150 },
  { key: "metricName", label: "指標名稱", width: 230, minWidth: 160 },
  { key: "purpose", label: "追蹤目的", width: 270, minWidth: 190 },
  { key: "analysisValue", label: "分析原因", width: 320, minWidth: 220 },
  { key: "trigger", label: "埋點事件", width: 300, minWidth: 210 },
  { key: "metricCalculation", label: "指標計算", width: 300, minWidth: 210 },
  { key: "source", label: "來源", width: 220, minWidth: 160 },
  { key: "actions", label: "操作", width: 132, minWidth: 108 },
];

const libraryColumnLookup = Object.fromEntries(
  libraryColumnConfig.map((column) => [column.key, column]),
) as Record<LibraryColumnKey, (typeof libraryColumnConfig)[number]>;

const defaultLibraryColumnWidths = Object.fromEntries(
  libraryColumnConfig.map((column) => [column.key, column.width]),
) as Record<LibraryColumnKey, number>;

const exportColumns: Array<{ key: keyof TrackingEvent; label: string }> = [
  { key: "id", label: "編號" },
  { key: "priority", label: "優先級" },
  { key: "page", label: "頁面/區塊" },
  { key: "metricName", label: "指標名稱" },
  { key: "purpose", label: "追蹤目的" },
  { key: "analysisValue", label: "分析原因" },
  { key: "trigger", label: "埋點事件" },
  { key: "metricCalculation", label: "指標計算" },
  { key: "properties", label: "屬性參數 (Property)" },
  { key: "propertyDefinitions", label: "屬性定義 (Property Definition)" },
  { key: "dataTypes", label: "Data Type" },
  { key: "sampleValues", label: "Sample Values" },
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

function cleanScopeName(value: string, fallback = "Figma 分析範圍", maxLength = 48) {
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

  const result = cleaned || fallback;

  return result.length > maxLength ? `${result.slice(0, maxLength - 1)}…` : result;
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

function deriveMetricName(page: string, area: string, eventType: TrackingEvent["eventType"]) {
  const subject = cleanScopeName(area || page, cleanScopeName(page, "主要功能"), 28);

  switch (eventType) {
    case "PageView":
      return `${cleanScopeName(page, "頁面")}瀏覽率`;
    case "SearchFilter":
      return `${subject}使用率`;
    case "FlowComplete":
      return `${subject}完成率`;
    case "CreateEdit":
      return `${subject}新增完成率`;
    case "ErrorDropoff":
      return `${subject}流失率`;
    case "ExportDownload":
      return `${subject}匯出下載率`;
    case "Click":
    default:
      return `${subject}點擊率`;
  }
}

function toNumberedDisplayList(value: string) {
  const normalized = value.replace(/\r/g, "").replace(/\s*\n+\s*/g, "\n").trim();
  const cleanItem = (item: string) => item.replace(/^[-•]\s*/, "").replace(/^\d+[.)、]\s*/, "").trim();
  const lines = normalized
    .split("\n")
    .map(cleanItem)
    .filter(Boolean);

  if (lines.length > 1) {
    return lines.map((line, index) => `${index + 1}. ${line}`).join("\n");
  }

  const parts = normalized
    .split(/\s*[；;]\s*/)
    .map(cleanItem)
    .filter(Boolean);

  return parts.length > 1 ? parts.map((part, index) => `${index + 1}. ${part}`).join("\n") : normalized;
}

function normalizeMetricCalculationCopy(value: string) {
  return value
    .replace(/\bpage\s*views?\b/gi, "頁面瀏覽次數")
    .replace(/\bunique\s+visitors?\b/gi, "不重複使用者數")
    .replace(/\bactive\s+users?\b/gi, "活躍使用者數")
    .replace(/\busers?\b/gi, "使用者數")
    .replace(/\bvisitors?\b/gi, "訪客數")
    .replace(/\bsessions?\b/gi, "使用階段數")
    .replace(/\bimpressions?\b/gi, "曝光次數")
    .replace(/\bclicks?\b/gi, "點擊次數")
    .replace(/\bconversions?\b/gi, "轉換次數")
    .replace(/\bDAU\b/gi, "日活躍使用者數")
    .replace(/\bWAU\b/gi, "週活躍使用者數")
    .replace(/\bMAU\b/gi, "月活躍使用者數")
    .replace(/\bCTR\b/gi, "點擊率")
    .replace(/\bCVR\b/gi, "轉換率")
    .replace(/\bPV\b/gi, "頁面瀏覽次數")
    .replace(/\bUV\b/gi, "不重複使用者數")
    .replace(/的\s+(不重複使用者數|使用階段數|頁面瀏覽次數|點擊次數|曝光次數|轉換次數)/g, "的$1");
}

function normalizeTrackingEventCopy(value: string) {
  return value
    .replace(/^使用者\s*/, "")
    .replace(/時觸發。?$/g, "")
    .replace(/觸發。?$/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
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

    if (!["design", "file", "proto"].includes(fileType) || !fileKey) {
      return { ...EMPTY_FIGMA_SOURCE, mode: "unsupported", normalizedUrl };
    }

    const knownFile = knownFigmaFiles[fileKey];
    const nodeId = parsed.searchParams.get("node-id")
      ? normalizeNodeId(parsed.searchParams.get("node-id") ?? "")
      : "";
    const fileName = knownFile?.name ?? decodeURIComponent(pathParts[2] ?? "Figma design file");

    return {
      mode: "file",
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

function createLocalFigmaPagesFallback(nextInfo: FigmaSourceInfo): FigmaPagesLoadResult | null {
  if (!nextInfo.fileKey || nextInfo.mode === "empty" || nextInfo.mode === "invalid" || nextInfo.mode === "unsupported") {
    return null;
  }

  const knownPages = nextInfo.pages.map(normalizeFigmaPage);

  if (nextInfo.mode === "node" && nextInfo.nodeId) {
    const relatedEventPages = Array.from(new Set(knownPages.flatMap((page) => page.relatedEventPages ?? [])));
    const nodeName = cleanScopeName(nextInfo.nodeName || knownPages[0]?.name || nextInfo.fileName, "指定 Frame", 72);
    const pages: FigmaPage[] = [
      {
        id: nextInfo.nodeId,
        name: nodeName,
        childCount: 1,
        ...(relatedEventPages.length ? { relatedEventPages } : {}),
      },
    ];

    return {
      pages,
      sourceInfo: {
        ...nextInfo,
        mode: "node",
        fileName: cleanScopeName(nextInfo.fileName, "Figma design file", 72),
        nodeName,
        pages,
      },
    };
  }

  if (knownPages.length > 1) {
    return {
      pages: knownPages,
      sourceInfo: {
        ...nextInfo,
        mode: "file",
        fileName: cleanScopeName(nextInfo.fileName, "Figma design file", 72),
        nodeId: "",
        nodeName: "",
        pages: knownPages,
      },
    };
  }

  return null;
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
  const page = cleanScopeName(row.page, "Figma 分析範圍");
  const area = cleanScopeName(row.area, row.page || "主要區塊");
  const eventType = coerceEventType(row.eventType);

  return {
    ...row,
    projectId:
      typeof row.projectId === "string" && row.projectId.trim() ? row.projectId : LEGACY_PROJECT_ID,
    page,
    area,
    metricName:
      typeof row.metricName === "string" && row.metricName.trim()
        ? cleanScopeName(row.metricName, deriveMetricName(page, area, eventType), 36)
        : deriveMetricName(page, area, eventType),
    eventType,
    trigger:
      typeof row.trigger === "string" && row.trigger.trim()
        ? normalizeTrackingEventCopy(row.trigger)
        : "完成指定埋點行為",
    analysisValue:
      typeof row.analysisValue === "string" && row.analysisValue.trim()
        ? toNumberedDisplayList(row.analysisValue)
        : "判斷此事件是否能回答目前頁面的核心產品問題。",
    metricCalculation:
      typeof row.metricCalculation === "string" && row.metricCalculation.trim()
        ? normalizeMetricCalculationCopy(toNumberedDisplayList(row.metricCalculation))
        : "事件不重複使用者數 ÷ 平台活躍不重複使用者數",
    sourceName: cleanScopeName(row.sourceName, row.sourceName || "Figma 來源"),
  };
}

function isTrackingEventDraftLike(value: unknown): value is TrackingEvent {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.id === "string" &&
    typeof record.page === "string" &&
    typeof record.area === "string" &&
    typeof record.eventName === "string"
  );
}

function normalizeCachedAnalysisEvent(row: TrackingEvent): TrackingEvent {
  const page = cleanScopeName(row.page, "Figma 分析範圍");
  const area = cleanScopeName(row.area, row.page || "主要區塊");
  const eventType = coerceEventType(row.eventType);
  const priority =
    row.priority === "P0" || row.priority === "P1" || row.priority === "P2" ? row.priority : "P1";

  return {
    id: row.id,
    page,
    area,
    metricName:
      typeof row.metricName === "string" && row.metricName.trim()
        ? cleanScopeName(row.metricName, deriveMetricName(page, area, eventType), 36)
        : deriveMetricName(page, area, eventType),
    eventName: row.eventName,
    eventType,
    trigger:
      typeof row.trigger === "string" && row.trigger.trim()
        ? normalizeTrackingEventCopy(row.trigger)
        : "完成指定埋點行為",
    purpose:
      typeof row.purpose === "string" && row.purpose.trim()
        ? row.purpose
        : "了解此事件是否能回答目前頁面的核心產品問題。",
    analysisValue:
      typeof row.analysisValue === "string" && row.analysisValue.trim()
        ? toNumberedDisplayList(row.analysisValue)
        : "判斷此事件是否能回答目前頁面的核心產品問題。",
    metricCalculation:
      typeof row.metricCalculation === "string" && row.metricCalculation.trim()
        ? normalizeMetricCalculationCopy(toNumberedDisplayList(row.metricCalculation))
        : "事件不重複使用者數 ÷ 平台活躍不重複使用者數",
    properties:
      typeof row.properties === "string" && row.properties.trim()
        ? row.properties
        : "page_name; user_role; entry_source",
    propertyDefinitions:
      typeof row.propertyDefinitions === "string" && row.propertyDefinitions.trim()
        ? row.propertyDefinitions
        : "頁面名稱; 使用者角色; 進入來源",
    dataTypes:
      typeof row.dataTypes === "string" && row.dataTypes.trim() ? row.dataTypes : "string; string; string",
    sampleValues:
      typeof row.sampleValues === "string" && row.sampleValues.trim()
        ? row.sampleValues
        : "patient_detail; doctor; sidebar",
    priority,
    status: typeof row.status === "string" && row.status.trim() ? row.status : "AI 產生",
  };
}

function isCachedAnalysisResultLike(value: unknown): value is CachedAnalysisResult {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return Array.isArray(record.rows);
}

function compactAnalysisResults(results: Record<string, CachedAnalysisResult>) {
  return Object.fromEntries(
    Object.entries(results)
      .sort(([, first], [, second]) => Date.parse(second.analyzedAt) - Date.parse(first.analyzedAt))
      .slice(0, 120),
  );
}

function isTrackingProjectLike(value: unknown): value is TrackingProject {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return typeof record.id === "string" && typeof record.name === "string";
}

function normalizeStoredProject(project: TrackingProject): TrackingProject {
  const now = new Date().toISOString();
  const name = cleanScopeName(project.name, "未命名專案", 40);

  return {
    id: project.id || `project_${hashText(name + now)}`,
    name,
    createdAt: typeof project.createdAt === "string" ? project.createdAt : now,
    updatedAt: typeof project.updatedAt === "string" ? project.updatedAt : now,
  };
}

function readStoredProjects() {
  try {
    const storedProjects = window.localStorage.getItem(PROJECTS_STORAGE_KEY);
    const parsed = storedProjects ? JSON.parse(storedProjects) : [];

    return Array.isArray(parsed) ? parsed.filter(isTrackingProjectLike).map(normalizeStoredProject) : [];
  } catch {
    return [];
  }
}

function readStoredActiveProjectId() {
  try {
    return window.localStorage.getItem(ACTIVE_PROJECT_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function isImportedFigmaSourceLike(value: unknown): value is ImportedFigmaSource {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.id === "string" &&
    typeof record.projectId === "string" &&
    typeof record.fileKey === "string" &&
    typeof record.normalizedUrl === "string" &&
    Array.isArray(record.pages)
  );
}

function isLegacyFrameImport(source: ImportedFigmaSource) {
  const parsedSource = parseFigmaUrl(source.normalizedUrl);

  return (
    source.mode === "node" &&
    source.importBehavior !== "auto" &&
    parsedSource.mode === "file" &&
    parsedSource.fileKey === source.fileKey &&
    Boolean(parsedSource.nodeId)
  );
}

function getFigmaSourceId(projectId: string, source: FigmaSourceInfo) {
  return `figma_${hashText([projectId, source.fileKey, source.mode === "node" ? source.nodeId : "file"].join("|"))}`;
}

function getAnalysisResultCacheKey(projectId: string, fileKey: string, sourceNodeId: string, pageId: string) {
  return [
    projectId || LEGACY_PROJECT_ID,
    fileKey || "unknown-file",
    sourceNodeId || "file",
    pageId || "unknown-page",
  ].join("|");
}

function getDefaultSelectedPageId(pages: FigmaPage[], preferredPageId = "") {
  if (preferredPageId && pages.some((page) => page.id === preferredPageId)) {
    return preferredPageId;
  }

  return pages.length === 1 ? pages[0].id : "";
}

function normalizeStoredFigmaSource(source: ImportedFigmaSource): ImportedFigmaSource {
  const now = new Date().toISOString();
  const pages = Array.isArray(source.pages) ? source.pages.map(normalizeFigmaPage) : [];
  const mode = source.mode === "node" ? "node" : "file";

  return {
    ...source,
    id: source.id || `figma_${hashText(source.normalizedUrl || source.fileKey)}`,
    projectId: source.projectId || LEGACY_PROJECT_ID,
    mode,
    fileName: cleanScopeName(source.fileName, "Figma 來源", 48),
    nodeId: mode === "node" ? source.nodeId : "",
    nodeName: mode === "node" && source.nodeName ? cleanScopeName(source.nodeName, "指定節點", 48) : "",
    pages,
    selectedPageId: getDefaultSelectedPageId(pages, source.selectedPageId),
    importedAt: typeof source.importedAt === "string" ? source.importedAt : now,
    updatedAt: typeof source.updatedAt === "string" ? source.updatedAt : now,
    ...(source.importBehavior === "auto" ? { importBehavior: source.importBehavior } : {}),
  };
}

function readStoredFigmaSources() {
  try {
    const storedSources = window.localStorage.getItem(FIGMA_SOURCES_STORAGE_KEY);
    const parsed = storedSources ? JSON.parse(storedSources) : [];

    return Array.isArray(parsed)
      ? parsed
          .filter(isImportedFigmaSourceLike)
          .map(normalizeStoredFigmaSource)
          .filter((source) => !isLegacyFrameImport(source))
      : [];
  } catch {
    return [];
  }
}

function readStoredAnalysisResults() {
  try {
    const storedResults = window.localStorage.getItem(ANALYSIS_RESULTS_STORAGE_KEY);
    const parsed = storedResults ? JSON.parse(storedResults) : {};

    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {};
    }

    const now = new Date().toISOString();
    const normalizedEntries = Object.entries(parsed as Record<string, unknown>).flatMap(([cacheKey, result]) => {
      if (!cacheKey || !isCachedAnalysisResultLike(result)) {
        return [];
      }

      const rows = result.rows
        .filter(isTrackingEventDraftLike)
        .map(normalizeCachedAnalysisEvent);

      if (!rows.length) {
        return [];
      }

      return [
        [
          cacheKey,
          {
            rows,
            modelId: typeof result.modelId === "string" ? result.modelId : "",
            analyzedAt: typeof result.analyzedAt === "string" ? result.analyzedAt : now,
          },
        ],
      ];
    });

    return compactAnalysisResults(Object.fromEntries(normalizedEntries));
  } catch {
    return {};
  }
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

async function readFigmaOAuthStartResponse(response: Response): Promise<FigmaOAuthStartResponse> {
  const contentType = response.headers.get("content-type") ?? "";
  const rawText = await response.text();
  const trimmedText = rawText.trim();
  const looksLikeJson = contentType.includes("application/json") || trimmedText.startsWith("{");

  if (!looksLikeJson) {
    return { message: `Figma 授權 API 回傳非 JSON 內容（HTTP ${response.status}）。` };
  }

  try {
    return JSON.parse(trimmedText) as FigmaOAuthStartResponse;
  } catch {
    return { message: `Figma 授權 API 回傳了無法解析的 JSON（HTTP ${response.status}）。` };
  }
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
      <Column ss:Width="158"/>
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
  const [activeView, setActiveView] = useState<AppView>("landing");
  const [draftFigmaUrl, setDraftFigmaUrl] = useState("");
  const [appliedFigmaUrl, setAppliedFigmaUrl] = useState("");
  const [projects, setProjects] = useState<TrackingProject[]>([]);
  const [activeProjectId, setActiveProjectId] = useState("");
  const [importedSources, setImportedSources] = useState<ImportedFigmaSource[]>([]);
  const [activeSourceId, setActiveSourceId] = useState("");
  const [isAddingSource, setIsAddingSource] = useState(false);
  const [isSourceMenuOpen, setIsSourceMenuOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [hasLoadedWorkspace, setHasLoadedWorkspace] = useState(false);
  const [figmaOAuthStatus, setFigmaOAuthStatus] = useState<FigmaOAuthStatus>({
    configured: false,
    available: false,
    connected: false,
    siteTokenConfigured: false,
    unavailableReason: "",
    isLoaded: false,
  });
  const [pendingFigmaOAuthSource, setPendingFigmaOAuthSource] = useState<FigmaSourceInfo | null>(null);
  const [isStartingFigmaOAuth, setIsStartingFigmaOAuth] = useState(false);
  const [figmaOAuthError, setFigmaOAuthError] = useState("");
  const [shouldResumeFigmaImport, setShouldResumeFigmaImport] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isProjectMenuOpen, setIsProjectMenuOpen] = useState(false);
  const [projectDeleteTarget, setProjectDeleteTarget] = useState<TrackingProject | null>(null);
  const [projectNameDraft, setProjectNameDraft] = useState("");
  const [loadedPages, setLoadedPages] = useState<FigmaPage[]>([]);
  const [selectedPageId, setSelectedPageId] = useState("");
  const [isPageMenuOpen, setIsPageMenuOpen] = useState(false);
  const [hasImportedPages, setHasImportedPages] = useState(false);
  const [isLoadingPages, setIsLoadingPages] = useState(false);
  const [pageLoadError, setPageLoadError] = useState("");
  const [isAnalysisModelMenuOpen, setIsAnalysisModelMenuOpen] = useState(false);
  const [filter, setFilter] = useState<EventFilter>("All");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("All");
  const [query, setQuery] = useState("");
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedAnalysisModelId, setSelectedAnalysisModelId] = useState(analysisModelOptions[0].id);
  const [analysisRows, setAnalysisRows] = useState<TrackingEvent[]>([]);
  const [cachedAnalysisResults, setCachedAnalysisResults] = useState<Record<string, CachedAnalysisResult>>({});
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
  const [libraryColumnWidths, setLibraryColumnWidths] =
    useState<Record<LibraryColumnKey, number>>(defaultLibraryColumnWidths);
  const [resizingLibraryColumn, setResizingLibraryColumn] = useState<LibraryColumnKey | null>(null);
  const [stickyTableHeader, setStickyTableHeader] = useState<StickyTableHeaderState | null>(null);
  const analysisRunId = useRef(0);
  const oauthResumeRef = useRef(false);
  const applyFigmaSourceRef = useRef<((nextInfo: FigmaSourceInfo) => Promise<void>) | null>(null);
  const cachedAnalysisResultsRef = useRef<Record<string, CachedAnalysisResult>>({});
  const analysisTableWrapRef = useRef<HTMLDivElement | null>(null);
  const libraryTableWrapRef = useRef<HTMLDivElement | null>(null);
  const pageSelectRef = useRef<HTMLDivElement | null>(null);
  const projectMenuRef = useRef<HTMLDivElement | null>(null);
  const sourceMenuRef = useRef<HTMLDivElement | null>(null);
  const analysisModelMenuRef = useRef<HTMLDivElement | null>(null);
  const toastTimerRef = useRef<number | null>(null);
  const libraryColumnResizeRef = useRef<{
    key: LibraryColumnKey;
    startX: number;
    startWidth: number;
  } | null>(null);

  const draftInfo = useMemo(() => parseFigmaUrl(draftFigmaUrl), [draftFigmaUrl]);
  const currentProject = projects.find((project) => project.id === activeProjectId) ?? null;
  const currentProjectSources = useMemo(
    () => importedSources.filter((source) => source.projectId === activeProjectId),
    [activeProjectId, importedSources],
  );
  const selectedImportedSource = currentProjectSources.find((source) => source.id === activeSourceId) ?? null;
  const figmaInfo = useMemo(() => {
    if (selectedImportedSource) {
      return {
        mode: selectedImportedSource.mode,
        fileKey: selectedImportedSource.fileKey,
        fileName: selectedImportedSource.fileName,
        nodeId: selectedImportedSource.mode === "node" ? selectedImportedSource.nodeId : "",
        nodeName: selectedImportedSource.mode === "node" ? selectedImportedSource.nodeName : "",
        pages: selectedImportedSource.pages,
        normalizedUrl: selectedImportedSource.normalizedUrl,
      };
    }

    return parseFigmaUrl(appliedFigmaUrl);
  }, [appliedFigmaUrl, selectedImportedSource]);
  const currentProjectLibraryRows = useMemo(
    () =>
      libraryRows.filter((row) =>
        activeProjectId
          ? row.projectId === activeProjectId || (!row.projectId && activeProjectId === LEGACY_PROJECT_ID)
          : false,
      ),
    [activeProjectId, libraryRows],
  );
  const hasDraftSource = Boolean(draftFigmaUrl.trim());
  const hasAppliedSource = Boolean(appliedFigmaUrl && figmaInfo.mode !== "invalid" && figmaInfo.mode !== "unsupported");
  const showImportForm = !currentProjectSources.length || isAddingSource;
  const pageOptions = hasImportedPages ? loadedPages : [];
  const selectedPage = pageOptions.find((page) => page.id === selectedPageId) ?? null;
  const needsPageSelection = hasAppliedSource;
  const canShowPageSelector =
    hasAppliedSource && (needsPageSelection || isLoadingPages || Boolean(pageOptions.length) || Boolean(pageLoadError));
  const canAnalyzeCurrentSource =
    hasAppliedSource && !isLoadingPages && hasImportedPages && Boolean(selectedPage);
  const selectedAnalysisModel =
    analysisModelOptions.find((option) => option.id === selectedAnalysisModelId) ?? analysisModelOptions[0];
  useEffect(() => {
    const timer = window.setTimeout(() => {
      const storedProjects = readStoredProjects();
      const storedSources = readStoredFigmaSources();
      const storedAnalysisResults = readStoredAnalysisResults();
      const storedActiveProjectId = readStoredActiveProjectId();
      const nextActiveProjectId =
        storedProjects.find((project) => project.id === storedActiveProjectId)?.id ?? storedProjects[0]?.id ?? "";
      const nextSource = storedSources.find((source) => source.projectId === nextActiveProjectId) ?? null;

      setProjects(storedProjects);
      setImportedSources(storedSources);
      cachedAnalysisResultsRef.current = storedAnalysisResults;
      setCachedAnalysisResults(storedAnalysisResults);
      setActiveProjectId(nextActiveProjectId);
      setIsProjectModalOpen(false);
      setIsAddingSource(!nextSource);
      if (nextSource) {
        const selectedSourcePageId = getDefaultSelectedPageId(nextSource.pages, nextSource.selectedPageId);
        const cachedResult = storedAnalysisResults[getSourceAnalysisCacheKey(nextSource, selectedSourcePageId)] ?? null;

        setActiveSourceId(nextSource.id);
        setDraftFigmaUrl("");
        setAppliedFigmaUrl(nextSource.normalizedUrl);
        setLoadedPages(nextSource.pages);
        setSelectedPageId(selectedSourcePageId);
        setHasImportedPages(true);
        setPageLoadError(nextSource.pages.length ? "" : "這個來源沒有讀到可分析的 Page");
        setAnalysisRows(cachedResult?.rows ?? []);
        setHasAnalyzed(Boolean(cachedResult));
        setAnalysisState("");
      } else {
        setActiveSourceId("");
        setDraftFigmaUrl("");
        setAppliedFigmaUrl("");
        setLoadedPages([]);
        setSelectedPageId("");
        setHasImportedPages(false);
        setPageLoadError("");
        setAnalysisRows([]);
        setHasAnalyzed(false);
        setAnalysisState("尚未提供 Figma 連結");
      }
      setLibraryRows(readStoredEventLibrary());
      setHasLoadedLibrary(true);
      setHasLoadedWorkspace(true);
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!hasLoadedWorkspace) {
      return;
    }

    window.localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
  }, [hasLoadedWorkspace, projects]);

  useEffect(() => {
    if (!hasLoadedWorkspace) {
      return;
    }

    window.localStorage.setItem(ACTIVE_PROJECT_STORAGE_KEY, activeProjectId);
  }, [activeProjectId, hasLoadedWorkspace]);

  useEffect(() => {
    if (!hasLoadedWorkspace) {
      return;
    }

    window.localStorage.setItem(FIGMA_SOURCES_STORAGE_KEY, JSON.stringify(importedSources));
  }, [hasLoadedWorkspace, importedSources]);

  useEffect(() => {
    if (!hasLoadedWorkspace) {
      return;
    }

    try {
      window.localStorage.setItem(
        ANALYSIS_RESULTS_STORAGE_KEY,
        JSON.stringify(compactAnalysisResults(cachedAnalysisResults)),
      );
    } catch {
      // Ignore localStorage quota failures; the current in-memory result still remains usable.
    }
  }, [cachedAnalysisResults, hasLoadedWorkspace]);

  useEffect(() => {
    if (!hasLoadedLibrary) {
      return;
    }

    window.localStorage.setItem(EVENT_LIBRARY_STORAGE_KEY, JSON.stringify(libraryRows));
  }, [hasLoadedLibrary, libraryRows]);

  useEffect(() => {
    const url = new URL(window.location.href);
    const oauthResult = url.searchParams.get("figma_oauth");

    void refreshFigmaOAuthStatus();

    if (oauthResult === "connected") {
      window.setTimeout(() => {
        setActiveView("planner");
        setShouldResumeFigmaImport(true);
        showToast("Figma 授權完成，正在繼續匯入");
      }, 0);
    } else if (oauthResult === "failed") {
      window.setTimeout(() => {
        setActiveView("planner");
        setFigmaOAuthError("Figma 授權未完成，請重新匯入並授權。");
        showToast("Figma 授權未完成");
      }, 0);
    }

    if (oauthResult) {
      url.searchParams.delete("figma_oauth");
      window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    }
  }, []);

  useEffect(() => {
    if (!hasLoadedWorkspace || !figmaOAuthStatus.connected || !shouldResumeFigmaImport || oauthResumeRef.current) {
      return;
    }

    let pendingUrl = "";

    try {
      pendingUrl = window.localStorage.getItem(PENDING_FIGMA_IMPORT_STORAGE_KEY) ?? "";
      window.localStorage.removeItem(PENDING_FIGMA_IMPORT_STORAGE_KEY);
    } catch {
      pendingUrl = "";
    }

    if (!pendingUrl) {
      window.setTimeout(() => setShouldResumeFigmaImport(false), 0);
      return;
    }

    const nextInfo = parseFigmaUrl(pendingUrl);

    if (nextInfo.mode === "file" || nextInfo.mode === "node") {
      const applyPendingFigmaSource = applyFigmaSourceRef.current;

      if (!applyPendingFigmaSource) {
        window.setTimeout(() => setShouldResumeFigmaImport(false), 0);
        return;
      }

      oauthResumeRef.current = true;
      window.setTimeout(() => {
        setDraftFigmaUrl(pendingUrl);
        void applyPendingFigmaSource(nextInfo).finally(() => {
          setShouldResumeFigmaImport(false);
        });
      }, 0);
    } else {
      window.setTimeout(() => setShouldResumeFigmaImport(false), 0);
    }
  }, [figmaOAuthStatus.connected, hasLoadedWorkspace, shouldResumeFigmaImport]);

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

  useEffect(() => {
    if (!isProjectMenuOpen) {
      return;
    }

    function handleOutsidePointerDown(event: PointerEvent) {
      const target = event.target;

      if (target instanceof Node && projectMenuRef.current && !projectMenuRef.current.contains(target)) {
        setIsProjectMenuOpen(false);
      }
    }

    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsProjectMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", handleOutsidePointerDown);
    document.addEventListener("keydown", handleEscapeKey);

    return () => {
      document.removeEventListener("pointerdown", handleOutsidePointerDown);
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [isProjectMenuOpen]);

  useEffect(() => {
    if (!isSourceMenuOpen) {
      return;
    }

    function handleOutsidePointerDown(event: PointerEvent) {
      const target = event.target;

      if (target instanceof Node && sourceMenuRef.current && !sourceMenuRef.current.contains(target)) {
        setIsSourceMenuOpen(false);
      }
    }

    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsSourceMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", handleOutsidePointerDown);
    document.addEventListener("keydown", handleEscapeKey);

    return () => {
      document.removeEventListener("pointerdown", handleOutsidePointerDown);
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [isSourceMenuOpen]);

  useEffect(() => {
    if (!isAnalysisModelMenuOpen) {
      return;
    }

    function handleOutsidePointerDown(event: PointerEvent) {
      const target = event.target;

      if (
        target instanceof Node &&
        analysisModelMenuRef.current &&
        !analysisModelMenuRef.current.contains(target)
      ) {
        setIsAnalysisModelMenuOpen(false);
      }
    }

    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsAnalysisModelMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", handleOutsidePointerDown);
    document.addEventListener("keydown", handleEscapeKey);

    return () => {
      document.removeEventListener("pointerdown", handleOutsidePointerDown);
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [isAnalysisModelMenuOpen]);

  useEffect(
    () => () => {
      if (toastTimerRef.current) {
        window.clearTimeout(toastTimerRef.current);
      }
    },
    [],
  );

  useEffect(() => {
    if (!resizingLibraryColumn) {
      return;
    }

    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    function handlePointerMove(event: PointerEvent) {
      const activeResize = libraryColumnResizeRef.current;

      if (!activeResize) {
        return;
      }

      const minimumWidth = libraryColumnLookup[activeResize.key].minWidth;
      const nextWidth = Math.max(minimumWidth, activeResize.startWidth + event.clientX - activeResize.startX);

      setLibraryColumnWidths((currentWidths) => ({
        ...currentWidths,
        [activeResize.key]: nextWidth,
      }));
    }

    function handlePointerUp() {
      libraryColumnResizeRef.current = null;
      setResizingLibraryColumn(null);
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);

    return () => {
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, [resizingLibraryColumn]);

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
          row.metricName,
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
    () =>
      Array.from(new Set(currentProjectLibraryRows.map((row) => cleanScopeName(row.sourceName, "Figma 來源")).filter(Boolean))),
    [currentProjectLibraryRows],
  );
  const effectiveLibrarySourceFilter =
    librarySourceFilter === "All" || librarySourceOptions.includes(librarySourceFilter) ? librarySourceFilter : "All";

  const libraryVisibleRows = useMemo(() => {
    const normalizedQuery = libraryQuery.trim().toLowerCase();

    return currentProjectLibraryRows.filter((row) => {
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
          row.metricName,
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
  }, [currentProjectLibraryRows, effectiveLibrarySourceFilter, libraryPriorityFilter, libraryQuery, libraryTypeFilter]);

  useEffect(() => {
    let animationFrame = 0;

    function updateStickyTableHeader() {
      animationFrame = 0;

      const kind = isLibraryOpen ? "library" : "analysis";
      const tableWrap = isLibraryOpen ? libraryTableWrapRef.current : analysisTableWrapRef.current;
      const hasRows = isLibraryOpen ? libraryVisibleRows.length > 0 : visibleRows.length > 0;
      const table = tableWrap?.querySelector("table");
      const tableHead = table?.querySelector("thead");

      if (!tableWrap || !table || !tableHead || !hasRows) {
        setStickyTableHeader((currentHeader) => (currentHeader ? null : currentHeader));
        return;
      }

      const wrapRect = tableWrap.getBoundingClientRect();
      const tableHeadRect = tableHead.getBoundingClientRect();
      const shouldStick = wrapRect.top <= 0 && wrapRect.bottom > tableHeadRect.height;

      if (!shouldStick) {
        setStickyTableHeader((currentHeader) => (currentHeader ? null : currentHeader));
        return;
      }

      const left = Math.max(wrapRect.left, 0);
      const right = Math.min(wrapRect.right, window.innerWidth);
      const nextHeader: StickyTableHeaderState = {
        kind,
        left,
        width: Math.max(0, right - left),
        tableWidth: table.scrollWidth || table.getBoundingClientRect().width,
        scrollLeft: tableWrap.scrollLeft,
      };

      setStickyTableHeader((currentHeader) => {
        if (
          currentHeader &&
          currentHeader.kind === nextHeader.kind &&
          Math.abs(currentHeader.left - nextHeader.left) < 0.5 &&
          Math.abs(currentHeader.width - nextHeader.width) < 0.5 &&
          Math.abs(currentHeader.tableWidth - nextHeader.tableWidth) < 0.5 &&
          Math.abs(currentHeader.scrollLeft - nextHeader.scrollLeft) < 0.5
        ) {
          return currentHeader;
        }

        return nextHeader;
      });
    }

    function scheduleStickyTableHeaderUpdate() {
      if (animationFrame) {
        return;
      }

      animationFrame = window.requestAnimationFrame(updateStickyTableHeader);
    }

    const activeTableWrap = isLibraryOpen ? libraryTableWrapRef.current : analysisTableWrapRef.current;

    scheduleStickyTableHeaderUpdate();
    window.addEventListener("scroll", scheduleStickyTableHeaderUpdate, { passive: true });
    window.addEventListener("resize", scheduleStickyTableHeaderUpdate);
    activeTableWrap?.addEventListener("scroll", scheduleStickyTableHeaderUpdate, { passive: true });

    return () => {
      if (animationFrame) {
        window.cancelAnimationFrame(animationFrame);
      }

      window.removeEventListener("scroll", scheduleStickyTableHeaderUpdate);
      window.removeEventListener("resize", scheduleStickyTableHeaderUpdate);
      activeTableWrap?.removeEventListener("scroll", scheduleStickyTableHeaderUpdate);
    };
  }, [isLibraryOpen, libraryColumnWidths, libraryVisibleRows.length, visibleRows.length]);

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

  function getCurrentAnalysisCacheKey(pageId = selectedPageId) {
    return getAnalysisResultCacheKey(
      activeProjectId || LEGACY_PROJECT_ID,
      figmaInfo.fileKey,
      figmaInfo.nodeId,
      pageId,
    );
  }

  function getSourceAnalysisCacheKey(source: ImportedFigmaSource, pageId: string) {
    return getAnalysisResultCacheKey(
      source.projectId || LEGACY_PROJECT_ID,
      source.fileKey,
      source.mode === "node" ? source.nodeId : "",
      pageId,
    );
  }

  function updateAnalysisResultCache(updater: (currentResults: Record<string, CachedAnalysisResult>) => Record<string, CachedAnalysisResult>) {
    setCachedAnalysisResults((currentResults) => {
      const nextResults = updater(currentResults);

      cachedAnalysisResultsRef.current = nextResults;
      return nextResults;
    });
  }

  function restoreCachedAnalysisResult(cacheKey: string, emptyStateMessage = "") {
    analysisRunId.current += 1;

    const cachedResult = cachedAnalysisResultsRef.current[cacheKey] ?? cachedAnalysisResults[cacheKey] ?? null;

    setIsAnalyzing(false);
    setAnalysisError("");
    setIsAnalysisModelMenuOpen(false);

    if (cachedResult) {
      setAnalysisRows(cachedResult.rows);
      setHasAnalyzed(true);
      setAnalysisState("");
      return;
    }

    setAnalysisRows([]);
    setHasAnalyzed(false);
    setAnalysisState(emptyStateMessage);
  }

  function restoreCachedAnalysisResultForSource(source: ImportedFigmaSource, pageId: string) {
    restoreCachedAnalysisResult(
      getSourceAnalysisCacheKey(source, pageId),
      pageId ? "" : "請先選擇要分析的 Page",
    );
  }

  function applyImportedSourceToState(source: ImportedFigmaSource | null) {
    if (!source) {
      setActiveSourceId("");
      setDraftFigmaUrl("");
      setAppliedFigmaUrl("");
      setLoadedPages([]);
      setSelectedPageId("");
      setIsPageMenuOpen(false);
      setHasImportedPages(false);
      setPageLoadError("");
      resetAnalysisResult();
      setFilter("All");
      setPriorityFilter("All");
      setQuery("");
      setAnalysisState("尚未提供 Figma 連結");
      return;
    }

    const selectedSourcePageId = getDefaultSelectedPageId(source.pages, source.selectedPageId);

    setActiveSourceId(source.id);
    setDraftFigmaUrl("");
    setAppliedFigmaUrl(source.normalizedUrl);
    setLoadedPages(source.pages);
    setSelectedPageId(selectedSourcePageId);
    setIsPageMenuOpen(false);
    setHasImportedPages(true);
    setPageLoadError(source.pages.length ? "" : "這個來源沒有讀到可分析的 Page");
    setIsAddingSource(false);
    restoreCachedAnalysisResultForSource(source, selectedSourcePageId);
    setFilter("All");
    setPriorityFilter("All");
    setQuery("");
  }

  function createImportedSource(nextInfo: FigmaSourceInfo, pages: FigmaPage[]): ImportedFigmaSource {
    const existingSource = importedSources.find(
      (source) => source.id === getFigmaSourceId(activeProjectId || LEGACY_PROJECT_ID, nextInfo),
    );
    const selectedSourcePageId = getDefaultSelectedPageId(pages, existingSource?.selectedPageId);
    const now = new Date().toISOString();
    const sourceDisplayName =
      nextInfo.mode === "node"
        ? cleanScopeName(pages[0]?.name || nextInfo.nodeName || nextInfo.fileName, "指定 Frame", 48)
        : cleanScopeName(nextInfo.fileName, "Figma 來源", 48);

    return {
      id: getFigmaSourceId(activeProjectId || LEGACY_PROJECT_ID, nextInfo),
      projectId: activeProjectId || LEGACY_PROJECT_ID,
      mode: nextInfo.mode === "node" ? "node" : "file",
      fileKey: nextInfo.fileKey,
      fileName: sourceDisplayName,
      nodeId: nextInfo.mode === "node" ? nextInfo.nodeId : "",
      nodeName: nextInfo.mode === "node" ? sourceDisplayName : "",
      normalizedUrl: nextInfo.normalizedUrl,
      pages,
      selectedPageId: selectedSourcePageId,
      importedAt: existingSource?.importedAt ?? now,
      updatedAt: now,
      importBehavior: "auto",
    };
  }

  function saveImportedSource(nextInfo: FigmaSourceInfo, pages: FigmaPage[]) {
    const source = createImportedSource(nextInfo, pages);

    setImportedSources((currentSources) => {
      const nextSources = currentSources.filter((currentSource) => currentSource.id !== source.id);

      return [source, ...nextSources];
    });
    applyImportedSourceToState(source);
  }

  function handleEnterPlanner() {
    setActiveView("planner");
    setIsLibraryOpen(false);
    setIsProjectModalOpen(false);
    setProjectDeleteTarget(null);
    setIsAnalysisModelMenuOpen(false);
  }

  function handleReturnHome() {
    setActiveView("landing");
    setIsLibraryOpen(false);
    setIsProjectModalOpen(false);
    setProjectDeleteTarget(null);
    setIsProjectMenuOpen(false);
    setIsSourceMenuOpen(false);
    setIsPageMenuOpen(false);
    setIsAnalysisModelMenuOpen(false);
  }

  function handleSwitchProject(projectId: string) {
    const nextProject = projects.find((project) => project.id === projectId);

    if (!nextProject) {
      return;
    }

    const nextSource = importedSources.find((source) => source.projectId === projectId) ?? null;

    setActiveProjectId(projectId);
    setLibraryQuery("");
    setLibraryTypeFilter("All");
    setLibraryPriorityFilter("All");
    setLibrarySourceFilter("All");
    setIsAddingSource(!nextSource);
    applyImportedSourceToState(nextSource);
    setIsProjectMenuOpen(false);
    setIsSourceMenuOpen(false);
    setIsAnalysisModelMenuOpen(false);
  }

  function handleOpenProjectModal() {
    if (!projects.length) {
      setActiveView("planner");
      setIsProjectModalOpen(false);
      return;
    }

    setProjectNameDraft("");
    setIsProjectMenuOpen(false);
    setIsSourceMenuOpen(false);
    setIsProjectModalOpen(true);
  }

  function handleSaveProject() {
    const projectName = projectNameDraft.trim();

    if (!projectName) {
      return;
    }

    const now = new Date().toISOString();
    const isFirstProject = projects.length === 0;
    const project: TrackingProject = {
      id: `project_${hashText(`${projectName}|${now}`)}`,
      name: cleanScopeName(projectName, "未命名專案", 40),
      createdAt: now,
      updatedAt: now,
    };

    setProjects((currentProjects) => [project, ...currentProjects]);
    setActiveProjectId(project.id);
    setProjectNameDraft("");
    setIsProjectModalOpen(false);
    setIsAddingSource(true);
    setLibraryQuery("");
    setLibraryTypeFilter("All");
    setLibraryPriorityFilter("All");
    setLibrarySourceFilter("All");
    if (isFirstProject) {
      setLibraryRows((currentRows) =>
        currentRows.map((row) => (row.projectId === LEGACY_PROJECT_ID ? { ...row, projectId: project.id } : row)),
      );
    }
    applyImportedSourceToState(null);
  }

  function handleRequestDeleteProject(project: TrackingProject) {
    setProjectDeleteTarget(project);
    setIsProjectMenuOpen(false);
  }

  function handleConfirmDeleteProject() {
    if (!projectDeleteTarget) {
      return;
    }

    const deleteProjectId = projectDeleteTarget.id;
    const remainingProjects = projects.filter((project) => project.id !== deleteProjectId);
    const remainingSources = importedSources.filter((source) => source.projectId !== deleteProjectId);
    const isDeletingActiveProject = activeProjectId === deleteProjectId;
    const nextProject = isDeletingActiveProject ? (remainingProjects[0] ?? null) : currentProject;
    const nextSource = nextProject
      ? remainingSources.find((source) => source.projectId === nextProject.id) ?? null
      : null;

    setProjects(remainingProjects);
    setImportedSources(remainingSources);
    setLibraryRows((currentRows) => currentRows.filter((row) => row.projectId !== deleteProjectId));
    setProjectDeleteTarget(null);
    setProjectNameDraft("");
    setLibraryQuery("");
    setLibraryTypeFilter("All");
    setLibraryPriorityFilter("All");
    setLibrarySourceFilter("All");
    handleCancelLibraryEdit();

    if (isDeletingActiveProject) {
      setActiveProjectId(nextProject?.id ?? "");
      setIsAddingSource(!nextSource);
      applyImportedSourceToState(nextSource);
    }

    if (!remainingProjects.length) {
      setIsLibraryOpen(false);
      setIsProjectModalOpen(false);
      setActiveView("planner");
    }
  }

  function handleStartAddSource() {
    setDraftFigmaUrl("");
    setIsAddingSource(true);
    setIsSourceMenuOpen(false);
    setAnalysisState("");
  }

  function handleCancelAddSource() {
    setDraftFigmaUrl("");
    setIsSourceMenuOpen(false);

    if (!currentProjectSources.length) {
      setIsAddingSource(true);
      applyImportedSourceToState(null);
      return;
    }

    setIsAddingSource(false);
    setAnalysisState("");
  }

  function handleSelectImportedSource(sourceId: string) {
    const source = currentProjectSources.find((currentSource) => currentSource.id === sourceId);

    if (source) {
      applyImportedSourceToState(source);
      setIsSourceMenuOpen(false);
    }
  }

  function handleDeleteImportedSource(sourceId: string) {
    const remainingProjectSources = currentProjectSources.filter((source) => source.id !== sourceId);
    const nextSource = remainingProjectSources[0] ?? null;

    setImportedSources((currentSources) => currentSources.filter((source) => source.id !== sourceId));
    setIsSourceMenuOpen(false);

    if (sourceId === activeSourceId || !nextSource) {
      setIsAddingSource(!nextSource);
      applyImportedSourceToState(nextSource);
    }
  }

  function getLibraryId(row: TrackingEvent) {
    return `evt_${hashText(
      [
        activeProjectId || LEGACY_PROJECT_ID,
        figmaInfo.fileKey,
        figmaInfo.nodeId || selectedPageId || "file",
        row.id,
        row.page,
        row.area,
        row.eventName,
      ].join("|"),
    )}`;
  }

  function createLibraryItem(row: TrackingEvent): SavedTrackingEvent {
    return {
      ...row,
      libraryId: getLibraryId(row),
      projectId: activeProjectId || LEGACY_PROJECT_ID,
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
    handleExportRowsExcel(makeSequentialRows(libraryVisibleRows), "埋點事件庫.xls");
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
    setLibraryRows((currentRows) => currentRows.filter((row) => row.projectId !== activeProjectId));
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

  function handleLibraryColumnResizeStart(key: LibraryColumnKey, event: ReactPointerEvent<HTMLSpanElement>) {
    event.preventDefault();
    event.stopPropagation();
    libraryColumnResizeRef.current = {
      key,
      startX: event.clientX,
      startWidth: libraryColumnWidths[key] ?? libraryColumnLookup[key].width,
    };
    setResizingLibraryColumn(key);
  }

  function renderLibraryHeader(column: (typeof libraryColumnConfig)[number]) {
    return (
      <th
        className={`resizable-header ${resizingLibraryColumn === column.key ? "resizing" : ""}`}
        key={column.key}
        scope="col"
      >
        <span className="resizable-header-content">
          <span>{column.label}</span>
          <span
            aria-label={`調整${column.label}欄寬`}
            className="column-resize-handle"
            onPointerDown={(event) => handleLibraryColumnResizeStart(column.key, event)}
            role="separator"
          />
        </span>
      </th>
    );
  }

  function handleTableWheel(event: ReactWheelEvent<HTMLDivElement>) {
    if (event.shiftKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) {
      return;
    }

    const deltaY =
      event.deltaMode === 1
        ? event.deltaY * 16
        : event.deltaMode === 2
          ? event.deltaY * window.innerHeight
          : event.deltaY;

    if (!deltaY) {
      return;
    }

    const maxScrollTop = document.documentElement.scrollHeight - window.innerHeight;
    const nextScrollTop = Math.max(0, Math.min(window.scrollY + deltaY, maxScrollTop));

    if (Math.abs(nextScrollTop - window.scrollY) < 0.5) {
      return;
    }

    event.preventDefault();
    window.scrollTo({ top: nextScrollTop, behavior: "auto" });
  }

  function renderAnalysisColgroup() {
    return (
      <colgroup>
        <col className="event-col-select" />
        <col className="event-col-id" />
        <col className="event-col-priority" />
        <col className="event-col-page" />
        <col className="event-col-metric-name" />
        <col className="event-col-purpose" />
        <col className="event-col-analysis" />
        <col className="event-col-trigger" />
        <col className="event-col-metric" />
        <col className="event-col-properties" />
      </colgroup>
    );
  }

  function renderAnalysisHeaderRow() {
    return (
      <tr>
        <th className="select-column">
          <span className="sr-only">選取</span>
        </th>
        <th>編號</th>
        <th>優先級</th>
        <th>頁面/區塊</th>
        <th>指標名稱</th>
        <th>追蹤目的</th>
        <th>分析原因</th>
        <th>埋點事件</th>
        <th>指標計算</th>
        <th>屬性參數</th>
      </tr>
    );
  }

  function renderStickyTableHeader() {
    if (!stickyTableHeader) {
      return null;
    }

    const stickyStyle = {
      left: `${stickyTableHeader.left}px`,
      width: `${stickyTableHeader.width}px`,
    };
    const scrollStyle = {
      transform: `translateX(-${stickyTableHeader.scrollLeft}px)`,
      width: `${stickyTableHeader.tableWidth}px`,
    };

    if (stickyTableHeader.kind === "library") {
      const actionWidth = libraryColumnWidths.actions ?? libraryColumnLookup.actions.width;
      const scrollableWidth = Math.max(0, stickyTableHeader.tableWidth - actionWidth);
      const visibleActionLeft = stickyTableHeader.width - actionWidth;

      return (
        <div className="sticky-table-header sticky-library-header" style={stickyStyle} aria-hidden="true">
          <div className="sticky-table-header-scroll" style={{ ...scrollStyle, width: `${scrollableWidth}px` }}>
            <table className="library-table sticky-table-clone" style={{ minWidth: `${scrollableWidth}px`, width: `${scrollableWidth}px` }}>
              <colgroup>
                {libraryColumnConfig
                  .filter((column) => column.key !== "actions")
                  .map((column) => (
                    <col key={column.key} style={{ width: `${libraryColumnWidths[column.key]}px` }} />
                  ))}
              </colgroup>
              <thead>
                <tr>
                  {libraryColumnConfig
                    .filter((column) => column.key !== "actions")
                    .map((column) => (
                      <th key={column.key} scope="col">
                        {column.label}
                      </th>
                    ))}
                </tr>
              </thead>
            </table>
          </div>
          <table
            className="library-table sticky-table-clone sticky-library-action-head"
            style={{ left: `${Math.max(0, visibleActionLeft)}px`, width: `${actionWidth}px` }}
          >
            <thead>
              <tr>
                <th scope="col">操作</th>
              </tr>
            </thead>
          </table>
        </div>
      );
    }

    return (
      <div className="sticky-table-header" style={stickyStyle} aria-hidden="true">
        <div className="sticky-table-header-scroll" style={scrollStyle}>
          <table className="event-table sticky-table-clone" style={{ minWidth: `${stickyTableHeader.tableWidth}px`, width: `${stickyTableHeader.tableWidth}px` }}>
            {renderAnalysisColgroup()}
            <thead>{renderAnalysisHeaderRow()}</thead>
          </table>
        </div>
      </div>
    );
  }

  function resetAnalysisResult() {
    analysisRunId.current += 1;
    setIsAnalyzing(false);
    setAnalysisRows([]);
    setAnalysisError("");
    setHasAnalyzed(false);
    setIsAnalysisModelMenuOpen(false);
  }

  function handleSelectAnalysisModel(modelId: string) {
    setSelectedAnalysisModelId(modelId);
    setIsAnalysisModelMenuOpen(false);
  }

  function showToast(message: string) {
    if (toastTimerRef.current) {
      window.clearTimeout(toastTimerRef.current);
    }

    setToastMessage(message);
    toastTimerRef.current = window.setTimeout(() => {
      setToastMessage("");
      toastTimerRef.current = null;
    }, 2000);
  }

  async function refreshFigmaOAuthStatus(): Promise<FigmaOAuthStatus> {
    try {
      const response = await fetch("/api/figma/oauth/status", {
        headers: {
          Accept: "application/json",
        },
        cache: "no-store",
        credentials: "include",
      });
      const result = (await response.json()) as Partial<FigmaOAuthStatus>;
      const nextStatus = {
        configured: Boolean(result.configured),
        available: Boolean(result.available),
        connected: Boolean(result.connected),
        siteTokenConfigured: Boolean(result.siteTokenConfigured),
        unavailableReason: typeof result.unavailableReason === "string" ? result.unavailableReason : "",
        isLoaded: true,
      };

      setFigmaOAuthStatus(nextStatus);
      return nextStatus;
    } catch {
      const nextStatus = {
        configured: false,
        available: false,
        connected: false,
        siteTokenConfigured: false,
        unavailableReason: "",
        isLoaded: true,
      };

      setFigmaOAuthStatus(nextStatus);
      return nextStatus;
    }
  }

  function openFigmaOAuthPrompt(nextInfo: FigmaSourceInfo, initialError = "") {
    setPendingFigmaOAuthSource(nextInfo);
    setFigmaOAuthError(initialError);
    setIsStartingFigmaOAuth(false);
    setIsSourceMenuOpen(false);
    setIsPageMenuOpen(false);
    setIsAnalysisModelMenuOpen(false);

    try {
      window.localStorage.setItem(PENDING_FIGMA_IMPORT_STORAGE_KEY, nextInfo.normalizedUrl);
    } catch {
      // The OAuth flow can still continue; the user can re-import after returning.
    }
  }

  function handleCancelFigmaOAuth() {
    setPendingFigmaOAuthSource(null);
    setFigmaOAuthError("");
    setIsStartingFigmaOAuth(false);

    try {
      window.localStorage.removeItem(PENDING_FIGMA_IMPORT_STORAGE_KEY);
    } catch {
      // Ignore localStorage failures; the modal is still closed.
    }
  }

  async function handleStartFigmaOAuth() {
    if (!pendingFigmaOAuthSource) {
      return;
    }

    setIsStartingFigmaOAuth(true);
    setFigmaOAuthError("");

    try {
      const currentOAuthStatus = figmaOAuthStatus.isLoaded ? figmaOAuthStatus : await refreshFigmaOAuthStatus();

      if (!currentOAuthStatus.configured) {
        throw new Error(FIGMA_OAUTH_SETUP_REQUIRED_MESSAGE);
      }

      if (!currentOAuthStatus.available) {
        throw new Error(currentOAuthStatus.unavailableReason || FIGMA_OAUTH_UNAVAILABLE_MESSAGE);
      }

      window.localStorage.setItem(PENDING_FIGMA_IMPORT_STORAGE_KEY, pendingFigmaOAuthSource.normalizedUrl);
      const response = await fetch("/api/figma/oauth/start", {
        method: "POST",
        headers: {
          Accept: "application/json",
        },
        cache: "no-store",
        credentials: "include",
      });
      const result = await readFigmaOAuthStartResponse(response);

      if (!response.ok || !result.authorizationUrl) {
        throw new Error(result.message || "無法開始 Figma 授權流程");
      }

      window.location.assign(result.authorizationUrl);
    } catch (error) {
      setFigmaOAuthError(error instanceof Error ? error.message : "無法開始 Figma 授權流程");
      setIsStartingFigmaOAuth(false);
    }
  }

  async function loadFigmaPages(nextInfo: FigmaSourceInfo): Promise<FigmaPagesLoadResult> {
    const emptyResult = { pages: [], sourceInfo: nextInfo };

    if (!nextInfo.fileKey || nextInfo.mode === "empty" || nextInfo.mode === "invalid" || nextInfo.mode === "unsupported") {
      setLoadedPages([]);
      setSelectedPageId("");
      setHasImportedPages(false);
      setPageLoadError("");
      return emptyResult;
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
        body: JSON.stringify({
          fileKey: nextInfo.fileKey,
          fileName: nextInfo.fileName,
          nodeId: nextInfo.nodeId,
          nodeName: nextInfo.nodeName,
        }),
        cache: "no-store",
        credentials: "include",
      });
      const result = await readFigmaPagesResponse(response);

      if (!response.ok) {
        const error = new Error(result.message || "無法讀取 Figma Page 清單") as Error & {
          code?: string;
          oauthConfigured?: boolean;
          tokenSource?: FigmaPagesResponse["tokenSource"];
        };

        error.code = result.code;
        error.oauthConfigured = result.oauthConfigured;
        error.tokenSource = result.tokenSource;
        throw error;
      }

      const pages = Array.isArray(result.pages) ? result.pages.map(normalizeFigmaPage) : [];
      const resolvedMode = result.mode === "file" || result.mode === "node" ? result.mode : nextInfo.mode;
      const sourceInfo: FigmaSourceInfo = {
        ...nextInfo,
        mode: resolvedMode,
        fileName: cleanScopeName(result.fileName ?? nextInfo.fileName, "Figma design file", 72),
        nodeId: resolvedMode === "node" ? result.nodeId ?? nextInfo.nodeId : "",
        nodeName:
          resolvedMode === "node"
            ? cleanScopeName(result.nodeName ?? pages[0]?.name ?? nextInfo.nodeName, "指定節點", 72)
            : "",
        pages,
      };
      const nextSelectedPageId = getDefaultSelectedPageId(pages);

      setLoadedPages(pages);
      setSelectedPageId(nextSelectedPageId);
      setIsPageMenuOpen(false);
      setHasImportedPages(true);
      setPageLoadError(pages.length ? "" : "這份 Figma 檔案沒有讀到可分析的 Page");
      setAnalysisState("");
      return { pages, sourceInfo };
    } catch (error) {
      const message = error instanceof Error ? error.message : "無法讀取 Figma Page 清單";
      const figmaError = error as Error & {
        code?: string;
        oauthConfigured?: boolean;
        tokenSource?: FigmaPagesResponse["tokenSource"];
      };
      const shouldOfferOAuth = Boolean(
        !figmaOAuthStatus.connected &&
          (figmaError.oauthConfigured ?? figmaOAuthStatus.available) &&
          (figmaError.code === "missing_figma_token" ||
            (figmaError.code === "invalid_figma_token" && figmaError.tokenSource === "site")),
      );
      const fallbackResult = createLocalFigmaPagesFallback(nextInfo);

      if (fallbackResult) {
        const fallbackPages = fallbackResult.pages;

        setLoadedPages(fallbackPages);
        setSelectedPageId(getDefaultSelectedPageId(fallbackPages));
        setIsPageMenuOpen(false);
        setHasImportedPages(true);
        setPageLoadError("");
        setAnalysisState("");
        showToast(
          /token|權杖|授權|權限/i.test(message)
            ? shouldOfferOAuth
              ? "已先匯入連結；完成 Figma 授權後可讀取完整內容"
              : "已先匯入連結；目前尚未取得完整 Figma 讀取權限"
            : "已先使用連結資訊匯入",
        );
        return { ...fallbackResult, authErrorMessage: message, requiresOAuth: shouldOfferOAuth };
      }

      setLoadedPages([]);
      setSelectedPageId("");
      setIsPageMenuOpen(false);
      setHasImportedPages(false);
      setPageLoadError(message);
      setAnalysisState("");
      return { ...emptyResult, authErrorMessage: message, requiresOAuth: shouldOfferOAuth };
    } finally {
      setIsLoadingPages(false);
    }
  }

  async function applyFigmaSource(nextInfo: FigmaSourceInfo) {
    const nextSourceId = getFigmaSourceId(activeProjectId || LEGACY_PROJECT_ID, nextInfo);
    const duplicatedSource = currentProjectSources.find((source) => source.id === nextSourceId);

    if (duplicatedSource) {
      applyImportedSourceToState(duplicatedSource);
      showToast("已切換到這個 Figma 來源");
      return;
    }

    setAppliedFigmaUrl(nextInfo.normalizedUrl);
    setActiveSourceId("");
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

    const { pages, sourceInfo, authErrorMessage, requiresOAuth } = await loadFigmaPages(nextInfo);

    if (pages.length) {
      const resolvedSourceId = getFigmaSourceId(activeProjectId || LEGACY_PROJECT_ID, sourceInfo);
      const duplicatedResolvedSource = currentProjectSources.find((source) => source.id === resolvedSourceId);

      if (resolvedSourceId !== nextSourceId && duplicatedResolvedSource) {
        showToast("這個 Figma 連結已經匯入過了");
        applyImportedSourceToState(duplicatedResolvedSource);
        return;
      }

      saveImportedSource(sourceInfo, pages);
      if (requiresOAuth) {
        openFigmaOAuthPrompt(sourceInfo, authErrorMessage || "");
      }
      return;
    }

    if (requiresOAuth) {
      openFigmaOAuthPrompt(nextInfo, authErrorMessage || "");
    }
  }

  applyFigmaSourceRef.current = applyFigmaSource;

  async function handleApplySource() {
    if (!activeProjectId) {
      handleOpenProjectModal();
      return;
    }

    const nextInfo = parseFigmaUrl(draftFigmaUrl);

    if (nextInfo.mode === "empty") {
      showToast("請先貼上 Figma design/file 連結");
      return;
    }

    if (nextInfo.mode === "invalid") {
      showToast("這看起來不是有效的 Figma 連結");
      return;
    }

    if (nextInfo.mode === "unsupported") {
      showToast("目前請改貼 Figma design/file/prototype 連結");
      return;
    }

    const nextSourceId = getFigmaSourceId(activeProjectId || LEGACY_PROJECT_ID, nextInfo);
    const duplicatedSource = currentProjectSources.find((source) => source.id === nextSourceId);

    if (duplicatedSource) {
      applyImportedSourceToState(duplicatedSource);
      showToast("已切換到這個 Figma 來源");
      return;
    }

    await applyFigmaSource(nextInfo);
  }

  function handleSelectPage(pageId: string) {
    const isSwitchingPage = pageId !== selectedPageId;

    setSelectedPageId(pageId);
    setImportedSources((currentSources) =>
      currentSources.map((source) =>
        source.id === activeSourceId
          ? {
              ...source,
              selectedPageId: pageId,
              updatedAt: new Date().toISOString(),
            }
          : source,
      ),
    );
    setIsPageMenuOpen(false);
    if (isSwitchingPage) {
      setFilter("All");
      setPriorityFilter("All");
      setQuery("");
    }
    restoreCachedAnalysisResult(getCurrentAnalysisCacheKey(pageId), pageId ? "" : "請先選擇要分析的 Page");
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
    const cacheKey = getCurrentAnalysisCacheKey();

    analysisRunId.current = runId;
    setIsAnalyzing(true);
    setAnalysisRows([]);
    setHasAnalyzed(false);
    setAnalysisError("");
    setAnalysisState("");
    setIsAnalysisModelMenuOpen(false);
    updateAnalysisResultCache((currentResults) => {
      if (!cacheKey || !currentResults[cacheKey]) {
        return currentResults;
      }

      const nextResults = { ...currentResults };
      delete nextResults[cacheKey];
      return nextResults;
    });

    try {
      const sourceForAnalysis = selectedPage
        ? {
            ...figmaInfo,
            mode: "node",
            nodeId: selectedPage.id,
            nodeName: selectedPage.name,
            pages: pageOptions.length ? pageOptions : figmaInfo.pages,
          }
        : {
            ...figmaInfo,
            pages: pageOptions.length ? pageOptions : figmaInfo.pages,
          };
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
            provider: selectedAnalysisModel.provider,
            openAIModel: selectedAnalysisModel.provider === "openai" ? selectedAnalysisModel.model : undefined,
            geminiModel: selectedAnalysisModel.provider === "gemini" ? selectedAnalysisModel.model : undefined,
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
      setHasAnalyzed(true);
      setAnalysisState("");
      updateAnalysisResultCache((currentResults) =>
        compactAnalysisResults({
          ...currentResults,
          [cacheKey]: {
            rows,
            modelId: selectedAnalysisModel.id,
            analyzedAt: new Date().toISOString(),
          },
        }),
      );
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
                      : "尚未套用 Figma 連結";
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

  function renderPlannerNav() {
    return (
      <nav className="planner-nav" aria-label="頁面導覽">
        <button className="planner-back-icon" type="button" onClick={handleReturnHome} aria-label="返回首頁">
          <span aria-hidden="true">‹</span>
        </button>
      </nav>
    );
  }

  function renderAnalysisModelMenu() {
    const openAIModels = analysisModelOptions.filter((option) => option.provider === "openai");
    const geminiModels = analysisModelOptions.filter((option) => option.provider === "gemini");

    return (
      <div className={`model-menu ${isAnalysisModelMenuOpen ? "open" : ""}`} ref={analysisModelMenuRef}>
        <button
          className="model-menu-trigger"
          type="button"
          onClick={() => {
            setIsProjectMenuOpen(false);
            setIsSourceMenuOpen(false);
            setIsPageMenuOpen(false);
            setIsAnalysisModelMenuOpen((current) => !current);
          }}
          disabled={isAnalyzing}
          aria-label="切換分析模型"
          aria-expanded={isAnalysisModelMenuOpen}
          aria-haspopup="menu"
        >
          <span>{selectedAnalysisModel.label}</span>
          <span className="page-select-arrow" aria-hidden="true">
            ▾
          </span>
        </button>
        {isAnalysisModelMenuOpen ? (
          <div className="model-menu-list" role="menu" aria-label="分析模型清單">
            <div className="model-menu-group-label" aria-hidden="true">
              OPEN AI<span>（會燒子傑錢呀🔥）</span>
            </div>
            {openAIModels.map((option) => (
              <button
                className={option.id === selectedAnalysisModelId ? "model-menu-choice selected" : "model-menu-choice"}
                key={option.id}
                type="button"
                role="menuitem"
                onClick={() => handleSelectAnalysisModel(option.id)}
              >
                <strong>{option.label}</strong>
                <span>{option.note}</span>
              </button>
            ))}
            <div className="model-menu-group-label" aria-hidden="true">
              Gemini
            </div>
            {geminiModels.map((option) => (
              <button
                className={option.id === selectedAnalysisModelId ? "model-menu-choice selected" : "model-menu-choice"}
                key={option.id}
                type="button"
                role="menuitem"
                onClick={() => handleSelectAnalysisModel(option.id)}
              >
                <strong>{option.label}</strong>
                <span>{option.note}</span>
              </button>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  function renderFigmaOAuthPrompt() {
    if (!pendingFigmaOAuthSource) {
      return null;
    }

    const oauthUnavailableMessage = !figmaOAuthStatus.configured
      ? FIGMA_OAUTH_SETUP_REQUIRED_MESSAGE
      : !figmaOAuthStatus.available
        ? figmaOAuthStatus.unavailableReason || FIGMA_OAUTH_UNAVAILABLE_MESSAGE
        : "";
    const oauthIntro = figmaOAuthStatus.available
      ? "為了讀取你剛貼上的 Figma 檔案，平台會前往 Figma 官方授權頁。你確認允許讀取檔案內容後，會回到這裡繼續匯入。"
      : "目前此站台的 Figma OAuth 還不能讓外部 Figma 帳號授權。平台會先使用站台預設 Figma 權限讀取稿件。";

    return (
      <div className="confirm-layer project-modal-layer" role="dialog" aria-modal="true" aria-labelledby="figma-oauth-title">
        <button
          className="drawer-scrim"
          type="button"
          onClick={handleCancelFigmaOAuth}
          aria-label="取消 Figma 授權"
        />
        <div className="confirm-dialog figma-oauth-dialog">
          <p className="eyebrow">Figma OAuth</p>
          <h2 id="figma-oauth-title">授權讀取 Figma 檔案</h2>
          <p>{oauthIntro}</p>
          {figmaOAuthStatus.available ? (
            <ul className="oauth-permission-list">
              <li>只要求讀取檔案內容的權限。</li>
              <li>授權範圍仍受你的 Figma 帳號可存取檔案限制。</li>
              <li>平台會透過 Figma 官方授權讀取檔案。</li>
            </ul>
          ) : (
            <ul className="oauth-permission-list">
              <li>Figma OAuth app 通過公開審核後，外部帳號才能自行授權。</li>
              <li>審核通過前，平台會使用站台預設 Figma 權限讀取檔案。</li>
              <li>若讀取失敗，請確認 Figma 分享設定已開放「知道連結的人可以檢視」。</li>
            </ul>
          )}
          {figmaOAuthError || oauthUnavailableMessage ? (
            <p className="oauth-error">{figmaOAuthError || oauthUnavailableMessage}</p>
          ) : null}
          <div className="confirm-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={handleCancelFigmaOAuth}
              disabled={isStartingFigmaOAuth}
            >
              取消
            </button>
            <button
              className="primary-button"
              type="button"
              onClick={handleStartFigmaOAuth}
              disabled={isStartingFigmaOAuth || !figmaOAuthStatus.available}
            >
              {!figmaOAuthStatus.configured
                ? "等待站台設定"
                : !figmaOAuthStatus.available
                  ? "等待 Figma 審核"
                  : isStartingFigmaOAuth
                    ? "前往中"
                    : "前往 Figma 授權"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  function renderAppToast() {
    return toastMessage ? (
      <div className="app-toast" role="status" aria-live="polite">
        {toastMessage}
      </div>
    ) : null;
  }

  function renderProjectForm({
    autoFocus = false,
    onCancel,
    submitLabel = "建立專案",
  }: {
    autoFocus?: boolean;
    onCancel?: () => void;
    submitLabel?: string;
  } = {}) {
    return (
      <form
        className="project-dialog"
        onSubmit={(event) => {
          event.preventDefault();
          handleSaveProject();
        }}
      >
        <p className="eyebrow">Project</p>
        <h2>{projects.length ? "新增專案" : "建立第一個專案"}</h2>
        <p>每個專案會有自己的 Figma 連結與埋點事件庫，方便不同產品或版本分開管理。</p>
        <label className="project-name-field">
          專案名稱
          <input
            autoFocus={autoFocus}
            value={projectNameDraft}
            onChange={(event) => setProjectNameDraft(event.target.value)}
            placeholder="請輸入專案名稱"
          />
        </label>
        <div className={onCancel ? "confirm-actions" : "confirm-actions single-action"}>
          {onCancel ? (
            <button className="secondary-button" type="button" onClick={onCancel}>
              取消
            </button>
          ) : null}
          <button className="primary-button" type="submit" disabled={!projectNameDraft.trim()}>
            {submitLabel}
          </button>
        </div>
      </form>
    );
  }

  function renderProjectSetupPage() {
    return (
      <main className="app-shell planner-shell">
        {renderPlannerNav()}
        <section className="project-setup-page" aria-label="建立專案">
          <div className="project-setup-copy">
            <p className="eyebrow">Project</p>
            <h1>先建立專案</h1>
            <p>專案會把 Figma 來源、AI 分析結果與埋點事件庫分開保存，適合同時管理不同產品、版本或團隊需求。</p>
          </div>
          <div className="project-setup-card">{renderProjectForm({ autoFocus: true })}</div>
        </section>
        {renderFigmaOAuthPrompt()}
        {renderAppToast()}
      </main>
    );
  }

  function renderPlannerLoadingPage() {
    return (
      <main className="app-shell planner-shell">
        {renderPlannerNav()}
        <section className="project-setup-page" aria-label="載入專案">
          <div className="project-setup-copy">
            <p className="eyebrow">Project</p>
            <h1>正在載入專案</h1>
            <p>正在讀取目前瀏覽器中的專案、Figma 來源與埋點事件庫。</p>
          </div>
          <div className="project-setup-card loading-card" role="status" aria-live="polite">
            <span className="loading-spinner" aria-hidden="true" />
            <strong>載入中</strong>
          </div>
        </section>
      </main>
    );
  }

  function renderProjectModal() {
    const canCloseProjectModal = projects.length > 0;

    return isProjectModalOpen && projects.length ? (
      <div className="confirm-layer project-modal-layer" role="dialog" aria-modal="true" aria-label="新增專案">
        {canCloseProjectModal ? (
          <button
            className="drawer-scrim"
            type="button"
            onClick={() => setIsProjectModalOpen(false)}
            aria-label="關閉新增專案"
          />
        ) : (
          <span className="drawer-scrim" aria-hidden="true" />
        )}
        <div className="confirm-dialog">
          {renderProjectForm({
            autoFocus: true,
            onCancel: () => {
              setIsProjectModalOpen(false);
            },
          })}
        </div>
      </div>
    ) : null;
  }

  function renderProjectDeleteConfirm() {
    return projectDeleteTarget ? (
      <div className="confirm-layer project-modal-layer" role="dialog" aria-modal="true" aria-label="刪除專案確認">
        <button
          className="drawer-scrim"
          type="button"
          onClick={() => setProjectDeleteTarget(null)}
          aria-label="取消刪除專案"
        />
        <div className="confirm-dialog">
          <p className="eyebrow">Confirm</p>
          <h2>刪除專案？</h2>
          <p>請確認是否要刪除「{projectDeleteTarget.name}」，刪除後資料不會留存。</p>
          <div className="confirm-actions">
            <button className="secondary-button" type="button" onClick={() => setProjectDeleteTarget(null)}>
              取消
            </button>
            <button className="primary-button danger-solid-button" type="button" onClick={handleConfirmDeleteProject}>
              刪除專案
            </button>
          </div>
        </div>
      </div>
    ) : null;
  }

  if (activeView === "landing") {
    return (
      <main className="landing-shell">
        <section className="landing-hero" aria-label="埋點規劃工具入口">
          <div className="landing-copy">
            <p className="landing-eyebrow"><span aria-hidden="true" />Product Analytics</p>
            <h1>埋點規劃工具</h1>
            <p>以專案管理 Figma 來源、Page 分析與埋點事件庫，讓團隊先回答真正影響產品決策的追蹤問題。</p>
            <button className="primary-button landing-cta" type="button" onClick={handleEnterPlanner}>
              <span>前往埋點規劃</span>
              <span aria-hidden="true">→</span>
            </button>
            <div className="landing-feature-grid" aria-label="首頁功能亮點">
              <div className="landing-feature">
                <span className="feature-icon feature-icon-figma" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false">
                    <path d="M5 5.5h14v13H5z" />
                    <path d="m8 16 3.2-4 2.4 2.8 1.5-1.8L18 16" />
                    <path d="M8 9h3" />
                  </svg>
                </span>
                <strong>Figma 整合</strong>
                <small>自動解析 Page 與元件</small>
              </div>
              <div className="landing-feature">
                <span className="feature-icon feature-icon-library" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false">
                    <path d="M7 7h4v4H7z" />
                    <path d="M13 13h4v4h-4z" />
                    <path d="M11 9h3.5a2.5 2.5 0 0 1 2.5 2.5V13" />
                    <path d="M13 15H9.5A2.5 2.5 0 0 1 7 12.5V11" />
                  </svg>
                </span>
                <strong>事件庫</strong>
                <small>管理標準事件與屬性</small>
              </div>
              <div className="landing-feature">
                <span className="feature-icon feature-icon-data" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false">
                    <path d="M6 6h12v12H6z" />
                    <path d="M10 6v12" />
                    <path d="M14 6v12" />
                    <path d="M6 10h12" />
                    <path d="M6 14h12" />
                  </svg>
                </span>
                <strong>數據驅動</strong>
                <small>用數據驗證產品假設</small>
              </div>
              <div className="landing-feature">
                <span className="feature-icon feature-icon-export" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false">
                    <path d="M12 16V6" />
                    <path d="m8.5 9.5 3.5-3.5 3.5 3.5" />
                    <path d="M6 14v4h12v-4" />
                  </svg>
                </span>
                <strong>匯出分享</strong>
                <small>一鍵匯出 Excel 協作</small>
              </div>
            </div>
          </div>
          <div className="landing-visual" aria-hidden="true">
            <span className="landing-orbit orbit-a" />
            <span className="landing-orbit orbit-b" />
            <div className="floating-cube figma-cube">
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className="dashboard-preview">
              <div className="dashboard-header">
                <strong>埋點規劃</strong>
                <span>⌘</span>
              </div>
              <div className="dashboard-metrics">
                <div>
                  <small>追蹤 Page 數</small>
                  <strong>42</strong>
                  <span>↑ 12%</span>
                </div>
                <div>
                  <small>埋點事件數</small>
                  <strong>128</strong>
                  <span>↑ 18%</span>
                </div>
                <div>
                  <small>關鍵事件數</small>
                  <strong>26</strong>
                  <span>↑ 8%</span>
                </div>
                <div>
                  <small>資料品質</small>
                  <strong>96%</strong>
                  <span>良好</span>
                </div>
              </div>
              <div className="dashboard-grid">
                <div className="flow-card">
                  <div className="card-title">Page 流程地圖</div>
                  <div className="flow-map">
                    <span className="flow-ring ring-one" />
                    <span className="flow-ring ring-two" />
                    <span className="flow-line line-one" />
                    <span className="flow-line line-two" />
                    <span className="flow-line line-three" />
                    <div className="flow-node flow-p0"><span>P0</span><strong>核心入口</strong><small>35 事件</small></div>
                    <div className="flow-node flow-p1"><span>P1</span><strong>功能價值</strong><small>28 事件</small></div>
                    <div className="flow-node flow-p2"><span>P2</span><strong>微互動</strong><small>16 事件</small></div>
                    <div className="flow-node flow-p3"><span>P3</span><strong>結果頁</strong><small>22 事件</small></div>
                  </div>
                  <div className="flow-legend">
                    <span><i />高流量</span>
                    <span><i />中流量</span>
                    <span><i />低流量</span>
                  </div>
                </div>
                <div className="trend-card">
                  <div className="card-title">
                    事件趨勢
                    <span>近 30 天</span>
                  </div>
                  <div className="trend-chart">
                    <span className="chart-grid-line chart-line-one" />
                    <span className="chart-grid-line chart-line-two" />
                    <span className="trend-fill" />
                    <span className="trend-stroke" />
                    <span className="trend-dot" />
                    <div className="trend-tooltip"><strong>05/22</strong><small>事件數 162</small></div>
                  </div>
                </div>
                <div className="hot-card">
                  <div className="card-title">
                    熱門事件
                    <span>查看全部</span>
                  </div>
                  <div className="hot-row"><strong>按鈕點擊</strong><span><i style={{ width: "72%" }} /></span><em>1,245</em></div>
                  <div className="hot-row"><strong>頁面瀏覽</strong><span><i style={{ width: "52%" }} /></span><em>980</em></div>
                  <div className="hot-row"><strong>表單提交</strong><span><i style={{ width: "32%" }} /></span><em>562</em></div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    );
  }

  if (!hasLoadedWorkspace) {
    return renderPlannerLoadingPage();
  }

  if (!currentProject) {
    return renderProjectSetupPage();
  }

  if (isLibraryOpen) {
    return (
      <main className="app-shell planner-shell library-shell">
        <header className="topbar library-topbar">
          <div className="library-heading-group">
            <button className="icon-button back-button" type="button" onClick={handleCloseLibrary} aria-label="返回工具">
              ‹
            </button>
            <div>
              <p className="eyebrow">Product Analytics</p>
              <h1>埋點事件庫</h1>
            </div>
            {currentProject ? <span className="project-chip">{currentProject.name}</span> : null}
          </div>
          <div className="topbar-actions">
            <button
              className="secondary-button danger-button"
              type="button"
              onClick={() => setIsClearLibraryConfirmOpen(true)}
              disabled={!currentProjectLibraryRows.length}
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

        <section className="library-page" aria-label="埋點事件庫表格">
          <div className="library-toolbar">
            <div>
              <p className="eyebrow">Selected Events</p>
              <h2>已儲存 {currentProjectLibraryRows.length} 筆埋點事件</h2>
            </div>
            <div className="toolbar-controls library-controls">
              <label className="filter-field search-field">
                <span>搜尋</span>
                <input
                  aria-label="搜尋埋點事件庫"
                  placeholder="搜尋事件、頁面或屬性"
                  value={libraryQuery}
                  onChange={(event) => setLibraryQuery(event.target.value)}
                  disabled={!currentProjectLibraryRows.length}
                />
              </label>
              <label className="filter-field">
                <span>事件類型</span>
                <select
                  aria-label="埋點事件庫事件類型篩選"
                  value={libraryTypeFilter}
                  onChange={(event) => setLibraryTypeFilter(event.target.value as EventFilter)}
                  disabled={!currentProjectLibraryRows.length}
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
                  aria-label="埋點事件庫優先級篩選"
                  value={libraryPriorityFilter}
                  onChange={(event) => setLibraryPriorityFilter(event.target.value as PriorityFilter)}
                  disabled={!currentProjectLibraryRows.length}
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
                  aria-label="埋點事件庫來源篩選"
                  value={effectiveLibrarySourceFilter}
                  onChange={(event) => setLibrarySourceFilter(event.target.value)}
                  disabled={!currentProjectLibraryRows.length || !librarySourceOptions.length}
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
            <div className="library-table-wrap" ref={libraryTableWrapRef} onWheel={handleTableWheel}>
              <table className={`library-table ${resizingLibraryColumn ? "is-resizing" : ""}`}>
                <colgroup>
                  {libraryColumnConfig.map((column) => (
                    <col key={column.key} style={{ width: `${libraryColumnWidths[column.key]}px` }} />
                  ))}
                </colgroup>
                <thead>
                  <tr>{libraryColumnConfig.map((column) => renderLibraryHeader(column))}</tr>
                </thead>
                <tbody>
                  {libraryVisibleRows.map((row, index) => (
                    <tr key={row.libraryId}>
                      <td>{index + 1}</td>
                      <td>
                        <span className={`priority-pill priority-${row.priority.toLowerCase()}`}>{row.priority}</span>
                      </td>
                      <td>
                        <strong>{row.area}</strong>
                        <span>{row.page}</span>
                      </td>
                      <td>
                        <strong>{row.metricName}</strong>
                        <span className={`type-pill type-${row.eventType.toLowerCase()}`}>
                          {typeLabels[row.eventType]}
                        </span>
                      </td>
                      <td>{row.purpose}</td>
                      <td>{row.analysisValue}</td>
                      <td>{row.trigger}</td>
                      <td>{row.metricCalculation}</td>
                      <td>
                        <span>{row.sourceName}</span>
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
              <strong>{currentProjectLibraryRows.length ? "沒有符合條件的埋點事件" : "尚未選取埋點追蹤事項"}</strong>
              <span>
                {currentProjectLibraryRows.length
                  ? "請調整搜尋文字、事件類型、優先級或來源篩選。"
                  : "回到工具頁，在分析結果表格勾選事件後，會加入這裡並保留到你自行刪除。"}
              </span>
            </div>
          )}
        </section>

        {renderStickyTableHeader()}
        {libraryDraft ? (
          <div className="library-drawer-layer" role="dialog" aria-modal="true" aria-label="編輯埋點事件">
            <button className="drawer-scrim" type="button" onClick={handleCancelLibraryEdit} aria-label="關閉編輯抽屜" />
            <aside className="library-drawer">
              <div className="library-drawer-header">
                <div>
                  <p className="eyebrow">Edit Event</p>
                  <h2>編輯埋點事件</h2>
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
                  指標名稱
                  <input
                    value={libraryDraft.metricName}
                    onChange={(event) => handleUpdateLibraryDraft("metricName", event.target.value)}
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
                  埋點事件
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
                  分析原因
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
          <div className="confirm-layer" role="dialog" aria-modal="true" aria-label="清除全部埋點事件確認">
            <button
              className="drawer-scrim"
              type="button"
              onClick={() => setIsClearLibraryConfirmOpen(false)}
              aria-label="取消清除全部事件"
            />
            <div className="confirm-dialog">
              <p className="eyebrow">Confirm</p>
              <h2>清除全部事件？</h2>
              <p>會清除目前專案「{currentProject?.name ?? "未命名專案"}」中的 {currentProjectLibraryRows.length} 筆事件，首頁目前的分析結果不會被刪除。</p>
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

        {renderProjectModal()}
        {renderProjectDeleteConfirm()}
      </main>
    );
  }

  return (
    <main className="app-shell planner-shell planner-workspace-shell">
      <header className="topbar">
        <div className="topbar-title">
          <button className="planner-back-icon topbar-back-icon" type="button" onClick={handleReturnHome} aria-label="返回首頁">
            <span aria-hidden="true">‹</span>
          </button>
          <div className="project-heading">
            <p className="eyebrow">Project</p>
            <h1>專案</h1>
          </div>
          <div className={`project-switcher ${isProjectMenuOpen ? "open" : ""}`} ref={projectMenuRef}>
            <button
              className="project-menu-trigger"
              type="button"
              onClick={() => {
                setIsSourceMenuOpen(false);
                setIsPageMenuOpen(false);
                setIsAnalysisModelMenuOpen(false);
                setIsProjectMenuOpen((current) => !current);
              }}
              disabled={!projects.length}
              aria-label="切換專案"
              aria-expanded={isProjectMenuOpen}
              aria-haspopup="menu"
            >
              <span>{currentProject?.name ?? "尚未建立專案"}</span>
              <span className="page-select-arrow" aria-hidden="true">
                ▾
              </span>
            </button>
            {isProjectMenuOpen ? (
              <div className="project-menu-list" role="menu" aria-label="專案清單">
                {projects.map((project) => (
                  <div className={`project-menu-item ${project.id === activeProjectId ? "selected" : ""}`} key={project.id}>
                    <button className="project-menu-choice" type="button" onClick={() => handleSwitchProject(project.id)}>
                      <strong>{project.name}</strong>
                      {project.id === activeProjectId ? <span>目前專案</span> : null}
                    </button>
                    <button
                      className="project-delete-button"
                      type="button"
                      onClick={() => handleRequestDeleteProject(project)}
                      aria-label={`刪除專案：${project.name}`}
                    >
                      刪除
                    </button>
                  </div>
                ))}
                <button className="project-menu-add" type="button" onClick={handleOpenProjectModal}>
                  新增專案
                </button>
              </div>
            ) : null}
          </div>
        </div>
        <div className="topbar-actions" aria-label="匯出工具">
          <button className="secondary-button library-button" type="button" onClick={() => setIsLibraryOpen(true)}>
            埋點事件庫
            <span>{currentProjectLibraryRows.length}</span>
          </button>
          <button className="primary-button" type="button" onClick={handleExportExcel} disabled={!visibleRows.length}>
            匯出 Excel
          </button>
        </div>
      </header>

      <section className="workspace">
        <aside className="control-panel" aria-label="Figma 分析控制台">
          <div className="panel-section">
            <div className="section-heading">
              <span className="section-index">01</span>
              <h2>Figma 連結</h2>
            </div>

            <div className="source-editor">
              {!currentProject ? (
                <div className="source-empty">
                  <strong>請先建立專案</strong>
                  <span>建立專案後，就能匯入 Figma 連結並產出埋點建議。</span>
                </div>
              ) : (
                <>
                  {currentProjectSources.length && !isAddingSource ? (
                    <>
                      <label className="field-label" htmlFor="imported-source">
                        Figma 連結
                      </label>
                      <div
                        className={`source-menu ${isSourceMenuOpen ? "open" : ""}`}
                        id="imported-source"
                        ref={sourceMenuRef}
                      >
                        <button
                          className="source-menu-trigger"
                          type="button"
                          onClick={() => {
                            setIsProjectMenuOpen(false);
                            setIsPageMenuOpen(false);
                            setIsAnalysisModelMenuOpen(false);
                            setIsSourceMenuOpen((current) => !current);
                          }}
                          disabled={isLoadingPages || isAnalyzing}
                          aria-expanded={isSourceMenuOpen}
                          aria-haspopup="menu"
                        >
                          <span>{selectedImportedSource?.fileName ?? "請選擇 Figma 來源"}</span>
                          <span className="page-select-arrow" aria-hidden="true">
                            ▾
                          </span>
                        </button>
                        {isSourceMenuOpen ? (
                          <div className="source-menu-list" role="menu" aria-label="已匯入 Figma 來源">
                            {currentProjectSources.map((source) => (
                              <div
                                className={source.id === activeSourceId ? "source-menu-item selected" : "source-menu-item"}
                                key={source.id}
                                role="none"
                              >
                                <button
                                  className="source-menu-choice"
                                  type="button"
                                  role="menuitem"
                                  onClick={() => handleSelectImportedSource(source.id)}
                                >
                                  <strong>{source.fileName}</strong>
                                  <span>{source.mode === "node" ? "指定 Frame" : `${source.pages.length} 個 Page`}</span>
                                </button>
                                <button
                                  className="source-delete-button"
                                  type="button"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    handleDeleteImportedSource(source.id);
                                  }}
                                  disabled={isLoadingPages || isAnalyzing}
                                  aria-label={`刪除來源：${source.fileName}`}
                                >
                                  刪除
                                </button>
                              </div>
                            ))}
                            {!isAddingSource ? (
                              <button
                                className="source-menu-add"
                                type="button"
                                role="menuitem"
                                onClick={handleStartAddSource}
                                disabled={isLoadingPages || isAnalyzing}
                              >
                                新增 Figma 連結
                              </button>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                      <p className="source-hint">
                        已載入 {selectedImportedSource?.pages.length ?? pageOptions.length} 個 Page。可切換已匯入連結或新增其他 Figma 連結。
                      </p>
                    </>
                  ) : null}
                  {showImportForm ? (
                    <div className={currentProjectSources.length ? "source-add-panel" : ""}>
                      <label className="field-label" htmlFor="figma-url">
                        {currentProjectSources.length ? "新增 Figma 連結" : "Figma 連結"}
                      </label>
                      <textarea
                        id="figma-url"
                        value={draftFigmaUrl}
                        onChange={(event) => setDraftFigmaUrl(event.target.value)}
                        placeholder="貼上 Figma design/file/prototype 連結"
                        rows={3}
                        disabled={isLoadingPages}
                      />
                      {draftInfo.mode === "empty" ? (
                        <div className="source-empty">
                          <strong>{currentProjectSources.length ? "等待新增來源" : "尚未匯入來源"}</strong>
                          <span>貼上 Figma 連結後按下匯入，系統會先讀取可分析的 Page。</span>
                        </div>
                      ) : (
                        <div className={`source-empty source-${draftInfo.mode}`}>
                          <strong>
                            {draftInfo.mode === "node"
                              ? "將匯入這個 Figma Frame"
                              : draftInfo.mode === "file"
                                ? "將匯入整份檔案"
                                : draftInfo.mode === "unsupported"
                                  ? "目前不支援這種 Figma 連結"
                                  : "這看起來不是有效的 Figma 連結"}
                          </strong>
                          <span>
                            {draftInfo.mode === "file"
                              ? "匯入後會列出 Page，請選定一頁再進行 AI 分析。"
                              : draftInfo.mode === "node"
                                ? "匯入後 Page 選單只會顯示這個 Frame。"
                                : "請改貼 Figma design/file/prototype 連結。"}
                          </span>
                        </div>
                      )}
                      <div className={currentProjectSources.length ? "source-actions" : "source-actions single-action"}>
                        <button
                          className="primary-button"
                          type="button"
                          onClick={handleApplySource}
                          disabled={!hasDraftSource || isLoadingPages}
                        >
                          {isLoadingPages ? "讀取中" : "匯入"}
                        </button>
                        {currentProjectSources.length ? (
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={handleCancelAddSource}
                            disabled={isLoadingPages}
                          >
                            取消
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </>
              )}
            </div>
          </div>

          {hasAppliedSource && !isAddingSource ? (
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
                          onClick={() => {
                            setIsProjectMenuOpen(false);
                            setIsSourceMenuOpen(false);
                            setIsAnalysisModelMenuOpen(false);
                            setIsPageMenuOpen((current) => !current);
                          }}
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
                            {pageOptions.map((page) => {
                              const hasCachedResult = Boolean(cachedAnalysisResults[getCurrentAnalysisCacheKey(page.id)]);

                              return (
                                <button
                                  className={page.id === selectedPageId ? "page-select-option selected" : "page-select-option"}
                                  key={page.id}
                                  type="button"
                                  role="option"
                                  aria-selected={page.id === selectedPageId}
                                  onClick={() => handleSelectPage(page.id)}
                                >
                                  <span>{page.name}</span>
                                  {hasCachedResult ? <small>已分析</small> : null}
                                </button>
                              );
                            })}
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <div className="source-empty">
                        <strong>{hasImportedPages ? "尚未讀到 Page" : "尚未匯入 Page"}</strong>
                        <span>
                          {hasImportedPages
                            ? "請確認 Figma 權限，或改貼指定 Page / 節點連結。"
                            : "匯入 Figma 連結後，會列出這份檔案中的 Page。"}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="analysis-field compact-model-field">
                    <span className="field-label">分析模型</span>
                    {renderAnalysisModelMenu()}
                  </div>
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

          <div className="event-table-wrap" ref={analysisTableWrapRef} onWheel={handleTableWheel}>
            <table className="event-table">
              {renderAnalysisColgroup()}
              <thead>
                {renderAnalysisHeaderRow()}
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
                    <tr key={row.id}>
                      <td className="select-column">
                        <input
                          aria-label={`加入埋點事件庫：${row.metricName}`}
                          checked={rowInLibrary}
                          type="checkbox"
                          onChange={(event) => handleToggleLibraryRow(row, event.target.checked)}
                        />
                      </td>
                      <td>
                        <span className="row-id">{row.id}</span>
                      </td>
                      <td>
                        <span className={`priority-pill priority-${row.priority.toLowerCase()}`}>
                          {row.priority}
                        </span>
                      </td>
                      <td>
                        <strong>{row.page}</strong>
                        <span>{row.area}</span>
                      </td>
                      <td>
                        {row.metricName}
                        <span className={`type-pill type-${row.eventType.toLowerCase()}`}>
                          {typeLabels[row.eventType]}
                        </span>
                      </td>
                      <td>{row.purpose}</td>
                      <td>{row.analysisValue}</td>
                      <td>{row.trigger}</td>
                      <td>{row.metricCalculation}</td>
                      <td>{row.properties}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {renderStickyTableHeader()}
        {renderProjectModal()}
        {renderProjectDeleteConfirm()}
        {renderFigmaOAuthPrompt()}
      </section>
      {renderAppToast()}
    </main>
  );
}
