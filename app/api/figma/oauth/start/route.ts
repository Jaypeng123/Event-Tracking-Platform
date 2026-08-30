import {
  createFigmaOAuthAuthorizationUrl,
  createOAuthState,
  createStateCookie,
  getFigmaOAuthConfig,
} from "../shared";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const config = getFigmaOAuthConfig(request);

  if (!config.configured) {
    return Response.json(
      {
        code: "figma_oauth_not_configured",
        message: "尚未設定 Figma OAuth，請先由管理者設定 FIGMA_OAUTH_CLIENT_ID 與 FIGMA_OAUTH_CLIENT_SECRET。",
      },
      { status: 503 },
    );
  }

  const state = createOAuthState();
  const headers = new Headers({
    "Content-Type": "application/json",
  });

  headers.append("Set-Cookie", createStateCookie(request, state));

  return new Response(
    JSON.stringify({
      authorizationUrl: createFigmaOAuthAuthorizationUrl(config, state),
    }),
    { headers },
  );
}
