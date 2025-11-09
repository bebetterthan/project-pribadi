import { create } from 'zustand';

interface AppStore {
  geminiApiKey: string | null;
  setGeminiApiKey: (key: string) => void;
  clearGeminiApiKey: () => void;
}

export const useStore = create<AppStore>((set) => ({
  geminiApiKey: null,
  setGeminiApiKey: (key: string) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('gemini_api_key', key);
    }
    set({ geminiApiKey: key });
  },
  clearGeminiApiKey: () => {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('gemini_api_key');
    }
    set({ geminiApiKey: null });
  },
}));
