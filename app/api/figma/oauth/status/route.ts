import { getFigmaOAuthConfig, hasSiteFigmaToken, readFigmaOAuthSessionState } from "../shared";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const config = getFigmaOAuthConfig(request);
  const sessionState = await readFigmaOAuthSessionState(request);
  const headers = new Headers({
    "Content-Type": "application/json",
  });

  if (sessionState.refreshedCookie) {
    headers.append("Set-Cookie", sessionState.refreshedCookie);
  }

  if (sessionState.clearCookie) {
    headers.append("Set-Cookie", sessionState.clearCookie);
  }

  return new Response(
    JSON.stringify({
      configured: config.configured,
      available: config.available,
      connected: Boolean(sessionState.session),
      siteTokenConfigured: hasSiteFigmaToken(),
      unavailableReason: config.unavailableReason,
      reconnectRequired: sessionState.reconnectRequired,
      reconnectReason: sessionState.reconnectReason,
    }),
    { headers },
  );
}
