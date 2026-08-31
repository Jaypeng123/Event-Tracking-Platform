import {
  FIGMA_OAUTH_NOT_CONFIGURED_MESSAGE,
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
        message: FIGMA_OAUTH_NOT_CONFIGURED_MESSAGE,
      },
      { status: 503 },
    );
  }

  if (!config.available) {
    return Response.json(
      {
        code: "figma_oauth_unavailable",
        message: config.unavailableReason,
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
