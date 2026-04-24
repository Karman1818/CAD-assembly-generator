export const API_BASE_URL = 'http://localhost:8000';

export async function uploadStepFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/step/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  return response.json();
}

export async function generateAssemblyInstructions(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/api/assembly/generate/${jobId}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Instruction generation failed');
  }

  return response.json();
}
