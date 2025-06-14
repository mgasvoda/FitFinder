// API Configuration
// Using environment-specific configuration
const API_BASE_URL = ''; // Empty for Next.js API routes in web context
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || process.env.API_KEY || '';

// For Capacitor mobile apps - handles special Android emulator case
const isAndroid = typeof window !== 'undefined' && window.navigator.userAgent.includes('Android');
const isEmulator = typeof window !== 'undefined' && window.navigator.userAgent.includes('Emulator');

// Use this flag to determine if we should bypass the Next.js API route in mobile contexts
const shouldUseDirectBackendCalls = isAndroid;

// Common headers for all requests
const getHeaders = (contentType: string = 'application/json') => ({
  'Content-Type': contentType,
  'X-API-Key': API_KEY,
});

// Backend URL for direct calls (used in Capacitor/Android)
// Use environment variable in production builds, fallback for development
const DIRECT_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://192.168.1.171:8000';

// Generic request handler
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  contentType: string = 'application/json'
): Promise<T> {
  // For Android, we might want to call the backend directly instead of through Next.js API routes
  let url;
  
  if (shouldUseDirectBackendCalls && endpoint.startsWith('/api/')) {
    // Special case for Android emulator - use 10.0.2.2 to access host machine
    const backendHost = isEmulator ? 'http://10.0.2.2:8000' : DIRECT_BACKEND_URL;
    // Convert /api/chat to /api/chat (keep the same path structure)
    url = `${backendHost}${endpoint}`;
    console.log(`[API] Using direct backend URL: ${url}`);
  } else {
    // Standard web approach - use Next.js API routes
    url = `${API_BASE_URL}${endpoint}`;
    console.log(`[API] Using Next.js API route: ${url}`);
  }
  
  // Ensure headers are properly set
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', contentType);
  }
  if (API_KEY) {
    headers.set('X-API-Key', API_KEY);
    console.log(`[API] Using API key: ${API_KEY.substring(0, 8)}...`);
  } else {
    console.warn('[API] No API key found in environment variables');
  }

  console.log(`[API] Making ${options.method || 'GET'} request to: ${url}`);
  console.log(`[API] Headers:`, Object.fromEntries(headers.entries()));

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    console.log(`[API] Response status: ${response.status}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API] Error response:`, errorText);
      let error;
      try {
        error = JSON.parse(errorText);
      } catch {
        error = { message: errorText || `HTTP ${response.status}` };
      }
      throw new Error(error.message || error.detail || 'An error occurred');
    }

    // Handle empty responses
    const text = await response.text();
    console.log(`[API] Response text:`, text);
    return text ? JSON.parse(text) : {} as T;
  } catch (error) {
    console.error('[API] Request Error:', error);
    throw error;
  }
}

// Types
export interface UploadItemResponse {
  id: string;
  url: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  response_text: string;
}

// API Functions
export async function uploadItem(formData: FormData): Promise<UploadItemResponse> {
  return apiRequest<UploadItemResponse>('/api/upload', {
    method: 'POST',
    body: formData,
  }, 'multipart/form-data');
}

export async function chatWithAssistant(
  prompt: string, 
  optionalImageUrl?: string
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ 
      prompt,
      ...(optionalImageUrl && { image_url: optionalImageUrl }) 
    }),
  });
}
