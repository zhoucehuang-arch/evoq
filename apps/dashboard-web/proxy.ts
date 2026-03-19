import { NextRequest, NextResponse } from "next/server";

const REALM = 'Basic realm="Quant Evo Dashboard"';

function unauthorizedResponse(message: string, status = 401): NextResponse {
  return new NextResponse(message, {
    status,
    headers: status === 401 ? { "WWW-Authenticate": REALM } : undefined,
  });
}

export function proxy(request: NextRequest): NextResponse {
  const username = (process.env.QE_DASHBOARD_ACCESS_USERNAME ?? "").trim();
  const password = (process.env.QE_DASHBOARD_ACCESS_PASSWORD ?? "").trim();

  if (!username && !password) {
    return NextResponse.next();
  }
  if (!username || !password) {
    return unauthorizedResponse("Dashboard auth is misconfigured.", 503);
  }

  const authorization = request.headers.get("authorization");
  if (!authorization || !authorization.startsWith("Basic ")) {
    return unauthorizedResponse("Authentication required.");
  }

  try {
    const decoded = atob(authorization.slice("Basic ".length));
    const separator = decoded.indexOf(":");
    const submittedUsername = separator >= 0 ? decoded.slice(0, separator) : decoded;
    const submittedPassword = separator >= 0 ? decoded.slice(separator + 1) : "";

    if (submittedUsername === username && submittedPassword === password) {
      return NextResponse.next();
    }
  } catch {
    return unauthorizedResponse("Invalid authentication header.");
  }

  return unauthorizedResponse("Invalid dashboard credentials.");
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
