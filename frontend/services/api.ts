// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

// Common headers for all requests
const getHeaders = (contentType: string = 'application/json') => ({
  'Content-Type': contentType,
  'X-API-Key': API_KEY,
});

// Generic request handler
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Ensure headers are properly set
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('X-API-Key', API_KEY);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || 'An error occurred');
    }

    // Handle empty responses
    const text = await response.text();
    return text ? JSON.parse(text) : {} as T;
  } catch (error) {
    console.error('API Request Error:', error);
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
  response: string;
}

// API Functions
export async function uploadItem(formData: FormData): Promise<UploadItemResponse> {
  return apiRequest<UploadItemResponse>('/api/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function chatWithAssistant(
  prompt: string, 
  optionalImageUrl?: string
): Promise<ChatResponse> {
  console.log('Sending chat request:', { prompt, optionalImageUrl });
  
  const response = await apiRequest<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ 
      prompt, 
      optional_image_url: optionalImageUrl 
    }),
  });

  console.log('Received chat response:', response);
  return response;
}
