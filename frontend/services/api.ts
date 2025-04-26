export async function uploadItem(formData: FormData) {
  const res = await fetch('/api/upload', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload item');
  return res.json();
}

export async function chatWithAssistant(prompt: string, optional_image_url?: string) {
  console.log('Sending chat request:', { prompt, optional_image_url });
  const body = JSON.stringify({ prompt, optional_image_url });
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body,
  });
  if (!res.ok) throw new Error('Failed to chat with assistant');
  const data = await res.json();
  console.log('Received chat response:', data);
  return data;
}
