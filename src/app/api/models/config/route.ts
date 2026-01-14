import { NextResponse } from 'next/server';

// The target backend server base URL, derived from environment variable or defaulted.
const TARGET_SERVER_BASE_URL = process.env.SERVER_BASE_URL || 'http://localhost:8001';

export async function GET() {
  try {
    const targetUrl = `${TARGET_SERVER_BASE_URL}/models/config`;

    // Make the actual request to the backend service
    const backendResponse = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      }
    });

    // If the backend service responds with an error
    if (!backendResponse.ok) {
      return NextResponse.json(
        { error: `Backend service responded with status: ${backendResponse.status}` },
        { status: backendResponse.status }
      );
    }

    // Forward the response from the backend
    const modelConfig = await backendResponse.json();

    // Ensure qwen3-coder-plus is available for the iflow provider
    const iflowProvider = modelConfig?.providers?.find((provider: any) => provider.id === 'iflow');
    if (iflowProvider) {
      const hasQwen3CoderPlus = (iflowProvider.models || []).some(
        (model: any) => model.id === 'qwen3-coder-plus'
      );
      if (!hasQwen3CoderPlus) {
        iflowProvider.models = [
          { id: 'qwen3-coder-plus', name: 'qwen3-coder-plus' },
          ...(iflowProvider.models || []),
        ];
      }
    }

    return NextResponse.json(modelConfig);
  } catch (error) {
    console.error('Error fetching model configurations:', error);    
    return new NextResponse(JSON.stringify({ error: error }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
  }
}

// Handle OPTIONS requests for CORS if needed
export function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
