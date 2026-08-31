export const dynamic = "force-dynamic";

type OpenAIModel = {
  id?: string;
};

type OpenAIModelsPayload = {
  data?: OpenAIModel[];
  error?: {
    message?: string;
  };
  raw?: string;
};

const OPENAI_MODELS_URL = "https://api.openai.com/v1/models";

const openAIModelOptions = [
  { id: "gpt-5.6-luna", label: "GPT-5.6 Luna", note: "低成本，適合大量頁面初步分析" },
  { id: "gpt-5.6-terra", label: "GPT-5.6 Terra", note: "品質與成本平衡" },
  { id: "gpt-5.6-sol", label: "GPT-5.6 Sol", note: "較高品質，適合複雜頁面" },
];

function asString(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

async function readJsonResponse(response: Response): Promise<OpenAIModelsPayload> {
  const text = await response.text();

  try {
    return JSON.parse(text) as OpenAIModelsPayload;
  } catch {
    return { raw: text };
  }
}

function extractOpenAIError(payload: OpenAIModelsPayload, fallback: string) {
  return asString(payload.error?.message, asString(payload.raw, fallback));
}

export async function GET() {
  const openAIKey = process.env.OPENAI_API_KEY?.trim();

  if (!openAIKey) {
    return Response.json(
      {
        models: openAIModelOptions,
        availableModelIds: [],
        defaultModel: openAIModelOptions[0].id,
        message: "平台尚未啟用 OpenAI 模型清單，暫時無法使用 OpenAI 分析。",
      },
      { status: 503 },
    );
  }

  const response = await fetch(OPENAI_MODELS_URL, {
    headers: {
      Authorization: `Bearer ${openAIKey}`,
    },
    cache: "no-store",
  });
  const payload = await readJsonResponse(response);

  if (!response.ok) {
    return Response.json(
      {
        models: openAIModelOptions,
        availableModelIds: [],
        defaultModel: openAIModelOptions[0].id,
        message: extractOpenAIError(payload, `OpenAI Models API 回傳 ${response.status}`),
      },
      { status: 502 },
    );
  }

  const modelIds = new Set((payload.data ?? []).map((model) => asString(model.id)).filter(Boolean));
  const availableModelIds = openAIModelOptions.map((option) => option.id).filter((modelId) => modelIds.has(modelId));

  return Response.json({
    models: openAIModelOptions,
    availableModelIds,
    defaultModel: availableModelIds[0] ?? openAIModelOptions[0].id,
    message: availableModelIds.length
      ? `這組 API key 可使用：${availableModelIds.join("、")}`
      : "這組 API key 目前沒有回傳平台支援的 OpenAI 模型；請到 OpenAI 專案模型權限確認。",
  });
}
