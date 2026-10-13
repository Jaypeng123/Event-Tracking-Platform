// Answers the app's /api/* requests locally so the full flow works offline.
import { DEMO_FILE_NAME, DEMO_PAGES, eventsForPage } from "./mock-data.js";

const realFetch = window.fetch.bind(window);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

window.fetch = async (input, init = {}) => {
  const url = typeof input === "string" ? input : input.url;
  const pathname = url.split("?")[0];
  const body = init.body ? JSON.parse(init.body) : {};

  if (pathname.endsWith("/api/figma/oauth/status")) {
    return json({ configured: true, available: true, connected: true, siteTokenConfigured: true });
  }
  if (pathname.endsWith("/api/figma-pages")) {
    await wait(body.forceRefresh ? 500 : 1100);
    return json({ mode: "file", fileName: DEMO_FILE_NAME, pages: DEMO_PAGES, tokenSource: "oauth" });
  }
  if (pathname.endsWith("/api/analyze")) {
    await wait(2800);
    const pageName = body.source?.nodeName || DEMO_PAGES[0].name;
    return json({ events: eventsForPage(pageName), model: body.ai?.openAIModel || body.ai?.geminiModel, tokenSource: "oauth" });
  }
  return realFetch(input, init);
};
