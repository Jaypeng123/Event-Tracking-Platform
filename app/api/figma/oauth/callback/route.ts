import {
  FIGMA_OAUTH_STATE_COOKIE,
  clearStateCookie,
  createSessionCookie,
  exchangeFigmaOAuthCode,
  getFigmaOAuthConfig,
  readCookie,
} from "../shared";

export const dynamic = "force-dynamic";

function redirectWithResult(request: Request, result: "connected" | "failed", extraCookies: string[] = []) {
  const redirectUrl = new URL("/", request.url);
  const headers = new Headers({
    Location: `${redirectUrl.toString()}?figma_oauth=${result}`,
  });

  headers.append("Set-Cookie", clearStateCookie(request));
  extraCookies.forEach((cookie) => headers.append("Set-Cookie", cookie));

  return new Response(null, {
    status: 302,
    headers,
  });
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code") ?? "";
  const state = url.searchParams.get("state") ?? "";
  const error = url.searchParams.get("error") ?? "";
  const expectedState = readCookie(request, FIGMA_OAUTH_STATE_COOKIE);
  const config = getFigmaOAuthConfig(request);

  if (error || !code || !state || !expectedState || state !== expectedState || !config.available) {
    return redirectWithResult(request, "failed");
  }

  try {
    const session = await exchangeFigmaOAuthCode(config, code);
    const sessionCookie = await createSessionCookie(request, config, session);

    return redirectWithResult(request, "connected", [sessionCookie]);
  } catch {
    return redirectWithResult(request, "failed");
  }
}
