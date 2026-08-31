import { getFigmaOAuthConfig, hasSiteFigmaToken, readFigmaOAuthSession } from "../shared";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const config = getFigmaOAuthConfig(request);
  const session = await readFigmaOAuthSession(request);

  return Response.json({
    configured: config.configured,
    available: config.available,
    connected: Boolean(session),
    siteTokenConfigured: hasSiteFigmaToken(),
    unavailableReason: config.unavailableReason,
  });
}
