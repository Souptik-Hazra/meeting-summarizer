/**
 * Utility functions for formatting audio file sizes and playback/recording durations.
 */

export function formatFileSize(bytes) {
  if (!bytes || bytes <= 0) return '0 KB';
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function formatTime(seconds) {
  const m = Math.floor((seconds || 0) / 60).toString().padStart(2, '0');
  const s = Math.floor((seconds || 0) % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}
