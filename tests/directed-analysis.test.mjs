import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const root = path.resolve(import.meta.dirname, "..");
const requirement = "幫我將逆向流程篩選出來";
const cancellationEvent = {
  page: "訂單詳情",
  area: "取消訂單",
  metricName: "訂單取消率",
  eventName: "click_cancel_order",
  eventType: "Click",
  trigger: "點擊「取消訂單」並確認取消",
  purpose: "了解使用者取消訂單的頻率。",
  analysisValue: "判斷訂單確認後是否仍有大量取消需求。",
  metricCalculation: "取消訂單的不重複使用者數 ÷ 查看訂單的不重複使用者數",
  properties: "page_name",
  propertyDefinitions: "頁面名稱",
  dataTypes: "string",
  sampleValues: "order_detail",
  priority: "P1",
  status: "AI 產生",
};

function fixture(labels = ["商品", "購物車", "結帳", "取消訂單"]) {
  return {
    name: "Fixture file",
    nodes: {
      "1:1": {
        document: {
          id: "1:1",
          name: "訂單詳情",
          type: "CANVAS",
          children: labels.map((label, index) => ({
            id: `2:${index}`,
            name: label,
            type: "TEXT",
            characters: label,
          })),
        },
      },
    },
  };
}

function createRuntime(options = {}) {
  const calls = [];
  const env = {
    FIGMA_ACCESS_TOKEN: "fixture-figma-credential",
    OPENAI_API_KEY: "fixture-ai-credential",
    ...options.env,
  };
  const state = { figma: fixture(), events: [cancellationEvent], ...options };
  const compiledRoute = new Map();

  function loadModule(filename) {
    if (compiledRoute.has(filename)) return compiledRoute.get(filename);
    const runtimeModule = { exports: {} };
    compiledRoute.set(filename, runtimeModule.exports);
    const compiled = ts.transpileModule(readFileSync(filename, "utf8"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    });
    vm.runInNewContext(compiled.outputText, {
      module: runtimeModule,
      exports: runtimeModule.exports,
      require(specifier) {
        if (specifier === "../figma/oauth/shared") {
          return {
            getFigmaOAuthConfig: () => ({ available: false }),
            readFigmaOAuthSessionState: async () => null,
          };
        }
        return loadModule(path.resolve(path.dirname(filename), `${specifier}.ts`));
      },
      process: { env },
      Error, Request, Response, Headers, URL, AbortController,
      setTimeout, clearTimeout,
      async fetch(url, init) {
        calls.push({ url: String(url), init });
        if (String(url).startsWith("https://api.figma.com/")) {
          return Response.json(state.figma);
        }
        if (state.aiError) {
          return Response.json({ error: { message: "Fixture provider unavailable" } }, { status: 503 });
        }
        const output = state.rawOutput ?? JSON.stringify({
          analysisProcess: ["讀取最新稿件", "理解需求", "篩選流程", "整理埋點"],
          events: state.events,
        });
        return String(url).includes("googleapis.com")
          ? Response.json({ candidates: [{ content: { parts: [{ text: output }] } }] })
          : Response.json({ output_text: output });
      },
    }, { filename });
    return runtimeModule.exports;
  }

  const { POST } = loadModule(path.join(root, "app/api/analyze/route.ts"));

  return {
    calls, state,
    async analyze(overrides = {}) {
      const response = await POST(new Request("http://localhost/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: { fileKey: "fixture-file", nodeId: "1:1", forceRefresh: true },
          currentUserPrompt: requirement,
          ai: { provider: "openai" },
          ...overrides,
        }),
      }));
      return { response, data: await response.json() };
    },
  };
}

function aiInputs(runtime) {
  return runtime.calls.filter((call) => !call.url.startsWith("https://api.figma.com/"))
    .map((call) => JSON.parse(call.init.body));
}

test("Phase 1 still analyzes the whole page when the requirement is blank", async () => {
  const runtime = createRuntime({ events: [] });
  const { response, data } = await runtime.analyze({ currentUserPrompt: "  " });
  assert.equal(response.status, 200);
  assert.ok(data.events.length > 0);
  assert.equal(JSON.parse(aiInputs(runtime)[0].input).requestContext.currentUserPrompt, "");
  assert.match(aiInputs(runtime)[0].instructions, /第一階段不要為它建立埋點/);
});

test("directed analysis forwards the requirement and keeps cancellation without padding", async () => {
  const runtime = createRuntime();
  const { response, data } = await runtime.analyze({
    currentUserPrompt: `  ${requirement}  `,
    previousAnalysisResult: "OLD_RESULT_SENTINEL",
    conversationHistory: ["OTHER_PROJECT_SENTINEL"],
  });
  assert.equal(response.status, 200);
  assert.equal(data.events.length, 1);
  assert.equal(data.events[0].eventName, "click_cancel_order");
  const ai = aiInputs(runtime)[0];
  const input = JSON.parse(ai.input);
  assert.equal(input.requestContext.currentUserPrompt, requirement);
  assert.equal(input.eventQuantityGuidance.suggestedLowerBound, 0);
  assert.equal(ai.store, false);
  assert.equal(ai.previous_response_id, undefined);
  assert.doesNotMatch(ai.input, /OLD_RESULT_SENTINEL|OTHER_PROJECT_SENTINEL/);
  assert.doesNotMatch(ai.instructions, /第一階段不要為它建立埋點/);
  assert.match(response.headers.get("cache-control"), /no-store/);
});

test("zero matching events remain zero instead of receiving fallback events", async () => {
  const runtime = createRuntime({ events: [] });
  const { response, data } = await runtime.analyze();
  assert.equal(response.status, 200);
  assert.equal(data.events.length, 0);
});

test("provider failure returns an actionable error instead of a whole-page plan", async () => {
  const runtime = createRuntime({ aiError: true });
  const { response, data } = await runtime.analyze();
  assert.equal(response.status, 503);
  assert.equal(data.code, "directed_analysis_failed");
  assert.equal(data.events, undefined);
});

test("malformed provider output is not mistaken for zero matching events", async () => {
  for (const rawOutput of ["", "not JSON", '{"events": null}', '{"events": [{}]}']) {
    const runtime = createRuntime({ rawOutput });
    const { response, data } = await runtime.analyze();
    assert.equal(response.status, 503);
    assert.equal(data.code, "directed_analysis_failed");
  }
});

test("directed analysis refuses inferred page-name content when Figma nodes cannot be fetched", async () => {
  const runtime = createRuntime({ figma: { nodes: {} } });
  const { response, data } = await runtime.analyze();
  assert.equal(response.status, 502);
  assert.equal(data.code, "figma_content_unavailable");
  assert.equal(aiInputs(runtime).length, 0);
});

test("a missing selected node cannot be replaced by a different node with the same name", async () => {
  const runtime = createRuntime({ figma: {
    document: { id: "0:0", type: "DOCUMENT", children: [
      { id: "9:9", type: "CANVAS", name: "訂單詳情", children: [
        { id: "9:10", type: "TEXT", characters: "取消訂單" },
      ] },
    ] },
  } });
  const { response, data } = await runtime.analyze({ source: {
    fileKey: "fixture-file", nodeId: "1:1", nodeName: "訂單詳情",
  } });
  assert.equal(response.status, 502);
  assert.equal(data.code, "figma_content_unavailable");
  assert.equal(aiInputs(runtime).length, 0);
});

test("missing AI configuration cannot silently produce structural fallback results", async () => {
  const runtime = createRuntime({ env: { OPENAI_API_KEY: "" } });
  const { response, data } = await runtime.analyze();
  assert.equal(response.status, 503);
  assert.equal(data.code, "ai_not_configured");
  assert.equal(data.events, undefined);
});

test("each repeated analysis fetches the latest Figma and uses only the current requirement", async () => {
  const runtime = createRuntime();
  for (const label of ["Button A", "Button B", "Button C"]) {
    runtime.state.figma = fixture([label]);
    await runtime.analyze({ currentUserPrompt: `只分析 ${label}` });
  }
  const figmaCalls = runtime.calls.filter((call) => call.url.startsWith("https://api.figma.com/"));
  assert.equal(figmaCalls.length, 3);
  assert.ok(figmaCalls.every((call) => call.init.cache === "no-store"));
  const inputs = aiInputs(runtime).map((input) => JSON.parse(input.input));
  for (const [index, label] of ["Button A", "Button B", "Button C"].entries()) {
    assert.equal(inputs[index].requestContext.currentUserPrompt, `只分析 ${label}`);
    assert.ok(inputs[index].figmaInspection.nodes.some((node) => node.includes(label)));
    assert.doesNotMatch(JSON.stringify(inputs[index].figmaInspection), new RegExp(index === 0 ? "Button B|Button C" : index === 1 ? "Button A|Button C" : "Button A|Button B"));
  }
});

test("a subsequent commerce project has no medical context and filters medical output", async () => {
  const runtime = createRuntime({ figma: fixture(["病患", "生命徵象", "護理師"]) });
  await runtime.analyze({ source: { fileKey: "medical-file", nodeId: "1:1" } });
  runtime.state.figma = fixture();
  runtime.state.events = [cancellationEvent, { ...cancellationEvent, area: "病患資料", trigger: "開啟病患資料" }];
  const { data } = await runtime.analyze({ source: { fileKey: "commerce-file", nodeId: "1:1" } });
  const input = JSON.parse(aiInputs(runtime)[1].input);
  assert.equal(input.requestContext.currentFigmaFileKey, "commerce-file");
  assert.equal(input.pageClassification.healthcareDomain, false);
  assert.doesNotMatch(JSON.stringify(input.figmaInspection), /病患|生命徵象|護理師|醫療|照護/);
  assert.doesNotMatch(JSON.stringify(data.events), /病患|生命徵象|護理師|醫療|照護/);
});

test("Gemini also receives the requirement and retains the directed event subset", async () => {
  const runtime = createRuntime({ env: { GEMINI_API_KEY: "fixture-gemini-credential" } });
  const { response, data } = await runtime.analyze({ ai: { provider: "gemini" } });
  assert.equal(response.status, 200);
  assert.equal(data.events.length, 1);
  const input = aiInputs(runtime)[0];
  assert.ok(input.contents[0].parts[0].text.includes(requirement));
  assert.match(input.systemInstruction.parts[0].text, /本次為指定需求分析/);
});

test("invalid or excessively long requirements are rejected before external requests", async () => {
  for (const currentUserPrompt of [null, {}, "x".repeat(2001)]) {
    const runtime = createRuntime();
    const { response, data } = await runtime.analyze({ currentUserPrompt });
    assert.equal(response.status, 400);
    assert.equal(data.code, "invalid_analysis_requirement");
    assert.equal(runtime.calls.length, 0);
  }
});
