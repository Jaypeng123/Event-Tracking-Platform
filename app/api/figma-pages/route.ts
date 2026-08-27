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
  return asString(payload.message, asString(payload.err, fallback));
}

export async function POST(request: Request) {
  let requestBody: { fileKey?: string };

  try {
    requestBody = (await request.json()) as { fileKey?: string };
  } catch {
    return Response.json({ message: "請提供有效的 JSON request body" }, { status: 400 });
  }

  const fileKey = asString(requestBody.fileKey);
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

  const response = await fetch(`${FIGMA_API_BASE_URL}/files/${encodeURIComponent(fileKey)}?depth=1`, {
    headers: buildFigmaHeaders(figmaToken),
    cache: "no-store",
  });
  const payload = (await readJsonResponse(response)) as FigmaApiResponse & Record<string, unknown>;

  if (!response.ok) {
    return Response.json(
      {
        code: "figma_pages_failed",
        message: extractFigmaError(payload, `Figma API 回傳 ${response.status}`),
      },
      { status: 502 },
    );
  }

  const pages =
    payload.document?.children
      ?.filter((node) => node.type === "CANVAS" && node.id)
      .map((node) => ({
        id: asString(node.id),
        name: asString(node.name, "Untitled page"),
        childCount: node.children?.length ?? 0,
      })) ?? [];

  return Response.json({
    fileName: asString(payload.name, "Figma design file"),
    pages,
  });
}
