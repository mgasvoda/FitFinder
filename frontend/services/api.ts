export async function uploadItem(formData: FormData) {
  const res = await fetch('/api/upload', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload item');
  return res.json();
}

export async function chatWithAssistant(formData: FormData) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to chat with assistant');
  return res.json();
}
