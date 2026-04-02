import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedPrefixes = ["/dashboard", "/history", "/profile", "/admin"];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("metroflow_predictor_token")?.value;
  const { pathname } = request.nextUrl;

  const isProtectedRoute = protectedPrefixes.some((prefix) => pathname.startsWith(prefix));
  if (isProtectedRoute && !token) {
    return NextResponse.redirect(new URL("/auth", request.url));
  }

  if (pathname === "/auth" && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/auth", "/dashboard/:path*", "/history/:path*", "/profile/:path*", "/admin/:path*"]
};
