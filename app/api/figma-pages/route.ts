import { getFigmaOAuthConfig, readFigmaOAuthSessionState } from "../figma/oauth/shared";

export const dynamic = "force-dynamic";

type FigmaNode = {
  id?: string;
  name?: string;
  type?: string;
  children?: FigmaNode[];
};

type FigmaApiResponse = {
  name?: string;
  document?: FigmaNode;
  nodes?: Record<string, { document?: FigmaNode } | null>;
  message?: string;
  err?: string;
};

type FigmaTokenSource = "oauth" | "site";

type FigmaPagesRequest = {
  fileKey?: string;
  fileName?: string;
  nodeId?: string;
  nodeName?: string;
};

type ResolvedFigmaToken = {
  rawToken: string;
  tokenValue: string;
  tokenSource: FigmaTokenSource;
  oauthAvailable: boolean;
  oauthReconnectRequired: boolean;
  oauthReconnectReason: string;
  oauthCookie?: string;
};

const FIGMA_API_BASE_URL = "https://api.figma.com/v1";

function asString(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function normalizeFigmaToken(rawToken: string) {
  const withoutHeaderName = rawToken
    .trim()
    .replace(/^["']|["']$/g, "")
    .replace(/^authorization\s*:\s*/i, "")
    .replace(/^x-figma-token\s*:\s*/i, "")
    .trim();
  const bearerMatch = withoutHeaderName.match(/^bearer\s+(.+)$/i);
  const tokenValue = (bearerMatch?.[1] ?? withoutHeaderName).trim().replace(/^["']|["']$/g, "");
  const isOAuthToken = Boolean(bearerMatch) && !/^figd_/i.test(tokenValue);

  return { tokenValue, isOAuthToken };
}

function buildFigmaHeaders(token: string) {
  const { tokenValue, isOAuthToken } = normalizeFigmaToken(token);

  if (isOAuthToken) {
    return { Authorization: `Bearer ${tokenValue}` };
  }

  return { "X-Figma-Token": tokenValue };
}

async function readJsonResponse(response: Response) {
  const text = await response.text();

  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { raw: text };
  }
}

function extractFigmaError(payload: Record<string, unknown>, fallback: string) {
  const rawSnippet =
    typeof payload.raw === "string"
      ? payload.raw
          .replace(/<script[\s\S]*?<\/script>/gi, " ")
          .replace(/<style[\s\S]*?<\/style>/gi, " ")
          .replace(/<[^>]+>/g, " ")
          .replace(/\s+/g, " ")
          .trim()
          .slice(0, 160)
      : "";

  return asString(payload.message, asString(payload.err, rawSnippet || fallback));
}

function isFigmaAuthError(response: Response, payload: Record<string, unknown>) {
  const message = extractFigmaError(payload, "");

  return (
    response.status === 401 ||
    response.status === 403 ||
    (response.status === 404 && /not found|file not found|missing file/i.test(message)) ||
    /invalid token|invalid access token|unauthorized|forbidden|not found|file not found/i.test(message)
  );
}

function getFigmaAuthErrorMessage(tokenSource: FigmaTokenSource) {
  if (tokenSource === "oauth") {
    return "你的 Figma 授權無法讀取這份檔案。請確認授權的 Figma 帳號能開啟此檔案，或重新授權後再試一次。";
  }

  return "站台預設 Figma 權限無法讀取這份檔案。請確認 Figma 分享設定已開放「知道連結的人可以檢視」，或檔案已分享給產生站台權限的 Figma 帳號，調整後重新匯入。";
}

function jsonWithOAuthCookie(data: unknown, init: ResponseInit = {}, oauthCookie = "") {
  const headers = new Headers(init.headers);

  if (oauthCookie) {
    headers.append("Set-Cookie", oauthCookie);
  }

  return Response.json(data, {
    ...init,
    headers,
  });
}

async function resolveFigmaToken(request: Request): Promise<ResolvedFigmaToken> {
  const oauthConfig = getFigmaOAuthConfig(request);
  const oauthSessionState = oauthConfig.available ? await readFigmaOAuthSessionState(request) : null;
  const oauthCookie = oauthSessionState?.refreshedCookie || oauthSessionState?.clearCookie || "";

  if (oauthSessionState?.session?.accessToken) {
    const rawToken = `Bearer ${oauthSessionState.session.accessToken}`;

    return {
      rawToken,
      tokenValue: normalizeFigmaToken(rawToken).tokenValue,
      tokenSource: "oauth" as const,
      oauthAvailable: true,
      oauthReconnectRequired: false,
      oauthReconnectReason: "",
      oauthCookie,
    };
  }

  const rawToken = process.env.FIGMA_ACCESS_TOKEN || process.env.FIGMA_TOKEN || "";

  return {
    rawToken,
    tokenValue: normalizeFigmaToken(rawToken).tokenValue,
    tokenSource: "site" as const,
    oauthAvailable: oauthConfig.available,
    oauthReconnectRequired: Boolean(oauthSessionState?.reconnectRequired),
    oauthReconnectReason: oauthSessionState?.reconnectReason ?? "",
    oauthCookie,
  };
}

function cleanPageName(value: string, fallback = "Untitled page") {
  const cleaned = value
    .replace(/[（(]\s*\d+(?:\.\d+)?(?:\s*[~～\-–—]\s*\d+(?:\.\d+)?)?\s*[）)]/g, "")
    .replace(/\s+\d+(?:\.\d+)?(?:\s*[~～\-–—]\s*\d+(?:\.\d+)?)?\s*$/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();

  return cleaned || fallback;
}

async function fetchFigmaPayload(path: string, figmaToken: string) {
  const response = await fetch(`${FIGMA_API_BASE_URL}${path}`, {
    headers: buildFigmaHeaders(figmaToken),
    cache: "no-store",
  });
  const payload = (await readJsonResponse(response)) as FigmaApiResponse & Record<string, unknown>;

  return { response, payload };
}

function getFilePages(payload: FigmaApiResponse) {
  return (
    payload.document?.children
      ?.filter((node) => node.type === "CANVAS" && node.id)
      .map((node) => ({
        id: asString(node.id),
        name: cleanPageName(asString(node.name, "Untitled page")),
        childCount: node.children?.length ?? 0,
      })) ?? []
  );
}

export async function POST(request: Request) {
  let requestBody: FigmaPagesRequest;

  try {
    requestBody = (await request.json()) as FigmaPagesRequest;
  } catch {
    return Response.json({ message: "請提供有效的 JSON request body" }, { status: 400 });
  }

  const fileKey = asString(requestBody.fileKey);
  const nodeId = asString(requestBody.nodeId).replace(/-/g, ":");
  const {
    rawToken: rawFigmaToken,
    tokenValue: figmaToken,
    tokenSource,
    oauthAvailable,
    oauthReconnectRequired,
    oauthCookie,
  } = await resolveFigmaToken(request);

  if (!fileKey) {
    return Response.json({ message: "缺少 Figma file key" }, { status: 400 });
  }

  if (!figmaToken && oauthAvailable) {
    return jsonWithOAuthCookie(
      {
        code: oauthReconnectRequired ? "figma_oauth_reconnect_required" : "figma_oauth_required",
        message: oauthReconnectRequired ? "Figma 授權已失效，請重新連結 Figma。" : "尚未連結 Figma，請先連結 Figma 後再匯入。",
        oauthConfigured: oauthAvailable,
        reconnectRequired: oauthReconnectRequired,
        tokenSource,
      },
      { status: 401 },
      oauthCookie,
    );
  }

  if (!figmaToken) {
    return jsonWithOAuthCookie(
      {
        code: "missing_figma_token",
        message: "尚未設定 Figma OAuth 或站台預設 Figma 權限，因此無法讀取 Figma Page 清單。",
        oauthConfigured: false,
        reconnectRequired: false,
        tokenSource,
      },
      { status: 503 },
      oauthCookie,
    );
  }

  try {
    const { response, payload } = await fetchFigmaPayload(
      `/files/${encodeURIComponent(fileKey)}?depth=1`,
      rawFigmaToken,
    );

    if (!response.ok) {
      if (isFigmaAuthError(response, payload)) {
        const shouldReconnect = tokenSource === "oauth";

        return jsonWithOAuthCookie(
          {
            code: shouldReconnect ? "figma_oauth_reconnect_required" : "figma_oauth_required",
            message: shouldReconnect
              ? "Figma 授權已失效、權限不足，或這份檔案沒有分享給目前連結的帳號。請重新連結 Figma。"
              : getFigmaAuthErrorMessage(tokenSource),
            oauthConfigured: oauthAvailable,
            reconnectRequired: shouldReconnect,
            tokenSource,
          },
          { status: 401 },
          oauthCookie,
        );
      }

      return jsonWithOAuthCookie(
        {
          code: "figma_pages_failed",
          message: extractFigmaError(payload, `Figma API 回傳 ${response.status}`),
        },
        { status: 502 },
        oauthCookie,
      );
    }

    const pages = getFilePages(payload);
    const filePageResult = {
      fileName: asString(payload.name, "Figma design file"),
      mode: "file" as const,
      nodeId: "",
      nodeName: "",
      pages,
    };

    if (!nodeId || pages.length !== 1) {
      return jsonWithOAuthCookie(filePageResult, {}, oauthCookie);
    }

    const nodeResult = await fetchFigmaPayload(
      `/files/${encodeURIComponent(fileKey)}/nodes?ids=${encodeURIComponent(nodeId)}&depth=1`,
      rawFigmaToken,
    );

    if (!nodeResult.response.ok) {
      return jsonWithOAuthCookie(filePageResult, {}, oauthCookie);
    }

    const node = nodeResult.payload.nodes?.[nodeId]?.document;

    if (!node || node.type === "CANVAS") {
      return jsonWithOAuthCookie(filePageResult, {}, oauthCookie);
    }

    const frameName = cleanPageName(
      asString(node.name, asString(requestBody.nodeName, asString(requestBody.fileName, "指定 Frame"))),
      "指定 Frame",
    );

    return jsonWithOAuthCookie(
      {
        fileName: asString(nodeResult.payload.name, asString(requestBody.fileName, "Figma design file")),
        mode: "node",
        nodeId,
        nodeName: frameName,
        pages: [
          {
            id: nodeId,
            name: frameName,
            childCount: node.children?.length ?? 1,
          },
        ],
      },
      {},
      oauthCookie,
    );
  } catch {
    return jsonWithOAuthCookie(
      {
        code: "figma_connection_failed",
        message: "Figma API 暫時無法回應，請稍後再匯入一次。",
      },
      { status: 502 },
      oauthCookie,
    );
  }
}
