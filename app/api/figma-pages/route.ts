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

const FIGMA_API_BASE_URL = "https://api.figma.com/v1";

function asString(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function buildFigmaHeaders(token: string) {
  const trimmed = token.trim();

  if (trimmed.toLowerCase().startsWith("bearer ")) {
    return { Authorization: trimmed };
  }

  return { "X-Figma-Token": trimmed };
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
  let requestBody: { fileKey?: string; fileName?: string; nodeId?: string; nodeName?: string };

  try {
    requestBody = (await request.json()) as { fileKey?: string };
  } catch {
    return Response.json({ message: "請提供有效的 JSON request body" }, { status: 400 });
  }

  const fileKey = asString(requestBody.fileKey);
  const nodeId = asString(requestBody.nodeId).replace(/-/g, ":");
  const figmaToken = (process.env.FIGMA_ACCESS_TOKEN || process.env.FIGMA_TOKEN)?.trim();

  if (!fileKey) {
    return Response.json({ message: "缺少 Figma file key" }, { status: 400 });
  }

  if (!figmaToken) {
    return Response.json(
      {
        code: "missing_figma_token",
        message: "尚未設定 FIGMA_ACCESS_TOKEN，因此無法讀取 Figma Page 清單。",
      },
      { status: 503 },
    );
  }

  try {
    let nodeFallbackMessage = "";

    if (nodeId) {
      const { response, payload } = await fetchFigmaPayload(
        `/files/${encodeURIComponent(fileKey)}/nodes?ids=${encodeURIComponent(nodeId)}`,
        figmaToken,
      );

      if (response.ok) {
        const node = payload.nodes?.[nodeId]?.document;

        if (node && node.type !== "CANVAS") {
          const frameName = cleanPageName(
            asString(node.name, asString(requestBody.nodeName, asString(requestBody.fileName, "指定 Frame"))),
            "指定 Frame",
          );

          return Response.json({
            fileName: asString(payload.name, asString(requestBody.fileName, "Figma design file")),
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
          });
        }
      } else {
        nodeFallbackMessage = extractFigmaError(payload, `Figma API 回傳 ${response.status}`);
      }
    }

    const { response, payload } = await fetchFigmaPayload(
      `/files/${encodeURIComponent(fileKey)}?depth=1`,
      figmaToken,
    );

    if (!response.ok) {
      return Response.json(
        {
          code: "figma_pages_failed",
          message: extractFigmaError(payload, nodeFallbackMessage || `Figma API 回傳 ${response.status}`),
        },
        { status: 502 },
      );
    }

    return Response.json({
      fileName: asString(payload.name, "Figma design file"),
      mode: "file",
      nodeId: "",
      nodeName: "",
      pages: getFilePages(payload),
    });
  } catch {
    return Response.json(
      {
        code: "figma_connection_failed",
        message: "Figma API 暫時無法回應，請稍後再匯入一次。",
      },
      { status: 502 },
    );
  }
}
