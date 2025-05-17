import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000/api/upload';

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  // Forward the form data to the FastAPI backend
  const backendRes = await fetch(BACKEND_URL, {
    method: 'POST',
    body: formData,
  });
  const data = await backendRes.json();
  return NextResponse.json(data, { status: backendRes.status });
}
