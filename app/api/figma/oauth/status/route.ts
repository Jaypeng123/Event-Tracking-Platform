import { getFigmaOAuthConfig, readFigmaOAuthSession } from "../shared";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const config = getFigmaOAuthConfig(request);
  const session = await readFigmaOAuthSession(request);

  return Response.json({
    configured: config.configured,
    connected: Boolean(session),
  });
}
