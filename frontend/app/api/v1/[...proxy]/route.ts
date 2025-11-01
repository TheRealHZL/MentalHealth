import { NextRequest, NextResponse } from 'next/server';

// Backend API URL - use internal Docker service name
const BACKEND_URL = process.env.INTERNAL_API_URL || 'http://backend:8080';

/**
 * API Proxy Route Handler
 *
 * This handler proxies all requests to the backend while properly
 * forwarding cookies in both directions:
 * - Client -> Backend: Forward cookies from client
 * - Backend -> Client: Forward Set-Cookie headers from backend
 *
 * This solves the issue where Next.js rewrites() don't forward
 * Set-Cookie headers, causing authentication to fail.
 */

async function handleRequest(request: NextRequest, method: string) {
  try {
    // Extract the path after /api/v1/
    const pathname = request.nextUrl.pathname.replace('/api/v1/', '');
    const searchParams = request.nextUrl.searchParams.toString();
    const backendUrl = `${BACKEND_URL}/api/v1/${pathname}${searchParams ? `?${searchParams}` : ''}`;

    console.log(`[API Proxy] ${method} ${pathname}`);

    // Prepare headers
    const headers: Record<string, string> = {
      'Content-Type': request.headers.get('content-type') || 'application/json',
    };

    // Forward cookies from client to backend
    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    // Forward authorization header if present (for backward compatibility)
    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    // Prepare request options
    const fetchOptions: RequestInit = {
      method,
      headers,
      credentials: 'include', // Important: Include cookies in request
    };

    // Add body for POST, PUT, PATCH methods
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      // Check if it's multipart/form-data (file upload)
      const contentType = request.headers.get('content-type');
      if (contentType?.includes('multipart/form-data')) {
        // For FormData, let fetch handle the content-type with boundary
        delete headers['Content-Type'];
        fetchOptions.body = await request.formData();
      } else {
        // For JSON data
        const body = await request.text();
        if (body) {
          fetchOptions.body = body;
        }
      }
    }

    // Make request to backend
    const backendResponse = await fetch(backendUrl, fetchOptions);

    // Get response body
    const responseBody = await backendResponse.text();

    // Create Next.js response
    const response = new NextResponse(responseBody, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
    });

    // Forward all headers from backend to client
    backendResponse.headers.forEach((value, key) => {
      // Forward all headers including Set-Cookie
      response.headers.set(key, value);
    });

    // Ensure CORS headers are set for development
    response.headers.set('Access-Control-Allow-Origin', request.headers.get('origin') || '*');
    response.headers.set('Access-Control-Allow-Credentials', 'true');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie');

    return response;

  } catch (error) {
    console.error('[API Proxy] Error:', error);
    return NextResponse.json(
      { error: 'Proxy error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// HTTP method handlers
export async function GET(request: NextRequest) {
  return handleRequest(request, 'GET');
}

export async function POST(request: NextRequest) {
  return handleRequest(request, 'POST');
}

export async function PUT(request: NextRequest) {
  return handleRequest(request, 'PUT');
}

export async function DELETE(request: NextRequest) {
  return handleRequest(request, 'DELETE');
}

export async function PATCH(request: NextRequest) {
  return handleRequest(request, 'PATCH');
}

export async function OPTIONS(request: NextRequest) {
  // Handle CORS preflight requests
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': request.headers.get('origin') || '*',
      'Access-Control-Allow-Credentials': 'true',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie',
      'Access-Control-Max-Age': '86400', // 24 hours
    },
  });
}
