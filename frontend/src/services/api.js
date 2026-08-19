const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Helper to handle response parsing and errors
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData?.detail) {
        errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
      }
    } catch {
      // Use fallback error message if JSON parsing fails
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

/**
 * Check backend API health connectivity
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse(response);
}

/**
 * Upload meeting audio recording (Foundation method for Phase 4)
 * @param {File} audioFile 
 */
export async function uploadMeetingAudio(audioFile) {
  const formData = new FormData();
  formData.append('file', audioFile);

  const response = await fetch(`${API_BASE_URL}/api/meetings/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

/**
 * Poll meeting processing status (Foundation method for Phase 7/8)
 * @param {string} meetingId 
 */
export async function getMeetingStatus(meetingId) {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${encodeURIComponent(meetingId)}/status`);
  return handleResponse(response);
}

/**
 * Fetch meeting intelligence results (Foundation method for Phase 8)
 * @param {string} meetingId 
 */
export async function getMeetingResult(meetingId) {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${encodeURIComponent(meetingId)}`);
  return handleResponse(response);
}
