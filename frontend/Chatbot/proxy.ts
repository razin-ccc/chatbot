import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED_PREFIXES = ["/chat", "/admin"];
const SESSION_COOKIE = "has_session";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = request.cookies.has(SESSION_COOKIE);

  const isProtected = PROTECTED_PREFIXES.some((prefix) =>
    pathname.startsWith(prefix)
  );

  if (isProtected && !hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/chat", "/chat/:path*", "/admin", "/admin/:path*", "/login", "/register"],
};
