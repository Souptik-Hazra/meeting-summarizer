import { useState, useEffect } from 'react';
import { Layers, Github } from 'lucide-react';
import Home from './pages/Home';
import Meeting from './pages/Meeting';

export default function App() {
  const [currentMeetingId, setCurrentMeetingId] = useState(null);

  // Sync with URL hash for easy sharing and browser back/forward support
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.startsWith('#meeting/')) {
        const id = hash.replace('#meeting/', '').trim();
        if (id) {
          setCurrentMeetingId(id);
          return;
        }
      }
      setCurrentMeetingId(null);
    };

    // Initial check on load
    handleHashChange();

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateToMeeting = (meetingId) => {
    if (meetingId) {
      window.location.hash = `meeting/${meetingId}`;
      setCurrentMeetingId(meetingId);
    }
  };

  const navigateToHome = () => {
    window.location.hash = '';
    setCurrentMeetingId(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-sky-500 selection:text-white">
      {/* Top Navigation Header */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div 
            onClick={navigateToHome}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
              <Layers className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white group-hover:text-sky-300 transition-colors">
                Meeting Intelligence
              </span>
              <span className="ml-2 text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                v1.0
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/Souptik-Hazra/meeting-summarizer"
              target="_blank"
              rel="noreferrer"
              aria-label="View source repository on GitHub"
              className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors p-2 rounded-lg hover:bg-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
            >
              <Github className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">Repository</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentMeetingId ? (
          <Meeting 
            meetingId={currentMeetingId} 
            onBackToUpload={navigateToHome} 
          />
        ) : (
          <Home 
            onNavigateToMeeting={navigateToMeeting} 
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <p>AI Meeting Intelligence & Summarization Platform • Groq Whisper + Gemini Flash</p>
      </footer>
    </div>
  );
}
