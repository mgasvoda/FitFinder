// This utility handles API calls in both web and native environments

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type HttpHeaders = {
  [key: string]: string;
};

export async function apiFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
  // In a native context, use Capacitor's HTTP plugin
  if (typeof window !== 'undefined' && (window as any).Capacitor) {
    try {
      const { Http } = await import('@capacitor-community/http');
      
      // Convert headers to a format compatible with Capacitor
      const headers: HttpHeaders = {
        'Content-Type': 'application/json',
        ...(options.headers as HttpHeaders || {})
      };
      
      const response = await Http.request({
        method: options.method || 'GET',
        url: `${API_BASE_URL}${endpoint}`,
        headers,
        data: options.body as any,
      });
      
      // Return a Response-like object
      return {
        ok: true,
        status: 200,
        json: async () => response.data,
        text: async () => JSON.stringify(response.data),
        headers: new Headers(response.headers as Record<string, string>),
      } as unknown as Response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }
  
  // In a web context, use the standard fetch API
  return fetch(`${API_BASE_URL}${endpoint}`, options);
}

// Example API functions
export async function chatApi(message: string) {
  const response = await apiFetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });
  return response.json();
}

export async function uploadFile(file: File) {
  // In a native context, we need to handle file uploads differently
  if (typeof window !== 'undefined' && (window as any).Capacitor) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiFetch('/api/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      body: formData as any,
    });
    return response.json();
  }
  
  // In a web context, use the standard fetch API
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiFetch('/api/upload', {
    method: 'POST',
    body: formData,
  });
  return response.json();
}
