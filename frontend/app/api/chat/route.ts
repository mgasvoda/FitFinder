import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000/api/chat';
const API_KEY = process.env.API_KEY || '';

export async function POST(req: NextRequest) {
  console.log('API route: Received chat request');
  const body = await req.text();
  const headers = new Headers(req.headers);
  
  console.log('API route: Request body:', body);
  
  try {
    const backendRes = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY, // Forward the API key from environment variables
      },
      body,
    });
    
    const data = await backendRes.json();
    console.log('API route: Response from backend:', data);
    
    return NextResponse.json(data, { status: backendRes.status });
  } catch (error) {
    console.error('API route: Error fetching from backend:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with backend' }, 
      { status: 500 }
    );
  }
}
