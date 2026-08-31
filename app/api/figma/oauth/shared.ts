export type FigmaOAuthConfig = {
  clientId: string;
  clientSecret: string;
  cookieSecret: string;
  redirectUri: string;
  scopes: string;
  configured: boolean;
  available: boolean;
  unavailableReason: string;
};

export type FigmaOAuthSession = {
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
  tokenType: string;
};

const FIGMA_OAUTH_AUTHORIZE_URL = "https://www.figma.com/oauth";
const FIGMA_OAUTH_TOKEN_URL = "https://api.figma.com/v1/oauth/token";
const FIGMA_OAUTH_SESSION_COOKIE = "tracking_plan_figma_oauth";
export const FIGMA_OAUTH_STATE_COOKIE = "tracking_plan_figma_oauth_state";
export const FIGMA_OAUTH_NOT_CONFIGURED_MESSAGE =
  "尚未設定 Figma OAuth，請先由管理者設定 FIGMA_OAUTH_CLIENT_ID 與 FIGMA_OAUTH_CLIENT_SECRET。";
export const FIGMA_OAUTH_UNAVAILABLE_MESSAGE =
  "Figma OAuth app 尚未通過公開審核，外部 Figma 帳號暫時無法授權。平台會先使用站台預設 Figma 權限讀取稿件。";
const encoder = new TextEncoder();
const decoder = new TextDecoder();

function base64Encode(value: string) {
  return btoa(value);
}

function bytesToBase64Url(bytes: Uint8Array) {
  let binary = "";

  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });

  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlToBytes(value: string) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  const binary = atob(padded);

  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

function getSecureCookieFlag(request: Request) {
  const forwardedProto = request.headers.get("x-forwarded-proto");

  return forwardedProto === "https" || new URL(request.url).protocol === "https:";
}

function serializeCookie(
  request: Request,
  name: string,
  value: string,
  options: {
    maxAge?: number;
    httpOnly?: boolean;
  } = {},
) {
  const parts = [`${name}=${value}`, "Path=/", "SameSite=Lax"];

  if (options.maxAge !== undefined) {
    parts.push(`Max-Age=${options.maxAge}`);
  }

  if (options.httpOnly !== false) {
    parts.push("HttpOnly");
  }

  if (getSecureCookieFlag(request)) {
    parts.push("Secure");
  }

  return parts.join("; ");
}

export function readCookie(request: Request, name: string) {
  const cookieHeader = request.headers.get("cookie") ?? "";

  return cookieHeader
    .split(";")
    .map((entry) => entry.trim())
    .find((entry) => entry.startsWith(`${name}=`))
    ?.slice(name.length + 1) ?? "";
}

async function getAesKey(secret: string) {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(secret));

  return crypto.subtle.importKey("raw", digest, { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
}

async function encryptSession(session: FigmaOAuthSession, secret: string) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await getAesKey(secret);
  const encrypted = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, encoder.encode(JSON.stringify(session)));

  return `${bytesToBase64Url(iv)}.${bytesToBase64Url(new Uint8Array(encrypted))}`;
}

async function decryptSession(value: string, secret: string): Promise<FigmaOAuthSession | null> {
  const [ivValue, encryptedValue] = value.split(".");

  if (!ivValue || !encryptedValue) {
    return null;
  }

  try {
    const key = await getAesKey(secret);
    const decrypted = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: base64UrlToBytes(ivValue) },
      key,
      base64UrlToBytes(encryptedValue),
    );
    const parsed = JSON.parse(decoder.decode(decrypted)) as Partial<FigmaOAuthSession>;

    if (!parsed.accessToken || typeof parsed.expiresAt !== "number") {
      return null;
    }

    return {
      accessToken: parsed.accessToken,
      refreshToken: parsed.refreshToken,
      expiresAt: parsed.expiresAt,
      tokenType: parsed.tokenType || "bearer",
    };
  } catch {
    return null;
  }
}

function readEnabledFlag(value: string | undefined, fallback = true) {
  if (value === undefined) {
    return fallback;
  }

  const normalized = value.trim().toLowerCase();

  if (!normalized) {
    return fallback;
  }

  return !["0", "false", "no", "off", "disabled"].includes(normalized);
}

export function hasSiteFigmaToken() {
  return Boolean((process.env.FIGMA_ACCESS_TOKEN || process.env.FIGMA_TOKEN || "").trim());
}

export function getFigmaOAuthConfig(request: Request): FigmaOAuthConfig {
  const clientId = process.env.FIGMA_OAUTH_CLIENT_ID?.trim() ?? "";
  const clientSecret = process.env.FIGMA_OAUTH_CLIENT_SECRET?.trim() ?? "";
  const cookieSecret = process.env.FIGMA_OAUTH_COOKIE_SECRET?.trim() || clientSecret;
  const redirectUri =
    process.env.FIGMA_OAUTH_REDIRECT_URI?.trim() ||
    new URL("/api/figma/oauth/callback", request.url).toString();
  const scopes = process.env.FIGMA_OAUTH_SCOPES?.trim() || "file_content:read";
  const configured = Boolean(clientId && clientSecret && cookieSecret && redirectUri);
  const enabled =
    readEnabledFlag(process.env.FIGMA_OAUTH_ENABLED) &&
    readEnabledFlag(process.env.FIGMA_OAUTH_PUBLIC_READY);
  const available = configured && enabled;

  return {
    clientId,
    clientSecret,
    cookieSecret,
    redirectUri,
    scopes,
    configured,
    available,
    unavailableReason: configured && !enabled ? FIGMA_OAUTH_UNAVAILABLE_MESSAGE : "",
  };
}

export function createOAuthState() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));

  return bytesToBase64Url(bytes);
}

export function createFigmaOAuthAuthorizationUrl(config: FigmaOAuthConfig, state: string) {
  const authorizationUrl = new URL(FIGMA_OAUTH_AUTHORIZE_URL);

  authorizationUrl.searchParams.set("client_id", config.clientId);
  authorizationUrl.searchParams.set("redirect_uri", config.redirectUri);
  authorizationUrl.searchParams.set("scope", config.scopes);
  authorizationUrl.searchParams.set("state", state);
  authorizationUrl.searchParams.set("response_type", "code");

  return authorizationUrl.toString();
}

export function createStateCookie(request: Request, state: string) {
  return serializeCookie(request, FIGMA_OAUTH_STATE_COOKIE, state, { maxAge: 600 });
}

export function clearStateCookie(request: Request) {
  return serializeCookie(request, FIGMA_OAUTH_STATE_COOKIE, "", { maxAge: 0 });
}

export function clearSessionCookie(request: Request) {
  return serializeCookie(request, FIGMA_OAUTH_SESSION_COOKIE, "", { maxAge: 0 });
}

export async function createSessionCookie(request: Request, config: FigmaOAuthConfig, session: FigmaOAuthSession) {
  const value = await encryptSession(session, config.cookieSecret);
  const secondsUntilExpiry = Math.max(60, Math.floor((session.expiresAt - Date.now()) / 1000));

  return serializeCookie(request, FIGMA_OAUTH_SESSION_COOKIE, value, {
    maxAge: Math.min(secondsUntilExpiry, 60 * 60 * 24 * 90),
  });
}

export async function readFigmaOAuthSession(request: Request) {
  const config = getFigmaOAuthConfig(request);
  const sessionCookie = readCookie(request, FIGMA_OAUTH_SESSION_COOKIE);

  if (!config.available || !sessionCookie) {
    return null;
  }

  const session = await decryptSession(sessionCookie, config.cookieSecret);

  if (!session || session.expiresAt <= Date.now() + 30_000) {
    return null;
  }

  return session;
}

async function readJsonResponse(response: Response) {
  const text = await response.text();

  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { raw: text };
  }
}

function asString(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function extractFigmaOAuthError(payload: Record<string, unknown>, fallback: string) {
  return asString(payload.message, asString(payload.error_description, asString(payload.err, fallback)));
}

export async function exchangeFigmaOAuthCode(config: FigmaOAuthConfig, code: string): Promise<FigmaOAuthSession> {
  const body = new URLSearchParams({
    redirect_uri: config.redirectUri,
    code,
    grant_type: "authorization_code",
  });
  const response = await fetch(FIGMA_OAUTH_TOKEN_URL, {
    method: "POST",
    headers: {
      Authorization: `Basic ${base64Encode(`${config.clientId}:${config.clientSecret}`)}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
    cache: "no-store",
  });
  const payload = await readJsonResponse(response);

  if (!response.ok) {
    throw new Error(extractFigmaOAuthError(payload, `Figma OAuth 回傳 ${response.status}`));
  }

  const accessToken = asString(payload.access_token);
  const refreshToken = asString(payload.refresh_token);
  const tokenType = asString(payload.token_type, "bearer");
  const expiresIn = typeof payload.expires_in === "number" ? payload.expires_in : 60 * 60 * 24 * 90;

  if (!accessToken) {
    throw new Error("Figma OAuth 沒有回傳 access token");
  }

  return {
    accessToken,
    refreshToken,
    tokenType,
    expiresAt: Date.now() + Math.max(60, expiresIn - 60) * 1000,
  };
}
