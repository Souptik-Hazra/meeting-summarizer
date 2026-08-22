const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Unified API request helper with error handling
 */
async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
  if (!response.ok) {
    let message = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Use HTTP status fallback
    }
    throw new Error(message);
  }
  return response.json();
}

export const checkHealth = () => request('/health');

export const uploadMeetingAudio = (file) => {
  const body = new FormData();
  body.append('file', file);
  return request('/api/meetings/upload', { method: 'POST', body });
};

export const getMeetingStatus = (id) => request(`/api/meetings/${encodeURIComponent(id)}/status`);

export const getMeetingResult = (id) => request(`/api/meetings/${encodeURIComponent(id)}`);
