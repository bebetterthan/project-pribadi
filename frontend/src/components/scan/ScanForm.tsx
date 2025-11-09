'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { ChevronDown, ChevronRight, Key, Settings, Wrench } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { AVAILABLE_TOOLS, SCAN_PROFILES } from '@/lib/constants';
import { useCreateScan } from '@/hooks/useScans';
import { ScanCreateRequest } from '@/types/scan';
import { useStore } from '@/store/useStore';

export const ScanForm = () => {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors }, watch } = useForm();
  const { mutate: createScan, isPending } = useCreateScan();
  const { geminiApiKey, setGeminiApiKey } = useStore();
  const [showApiKey, setShowApiKey] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const enableAI = watch('enable_ai', true);

  const onSubmit = (data: any) => {
    // Validate target
    if (!data.target || data.target.trim() === '') {
      toast.error('Please enter a target');
      return;
    }

    // Store API key if provided
    if (data.gemini_api_key) {
      setGeminiApiKey(data.gemini_api_key);
    }

    // Validate tools selection
    const selectedTools = Array.isArray(data.tools)
      ? data.tools.filter((t: string) => t !== '').filter(Boolean)
      : [];

    if (selectedTools.length === 0) {
      toast.error('Please select at least one tool');
      return;
    }

    const scanData: ScanCreateRequest = {
      target: data.target.trim(),
      user_prompt: data.user_prompt?.trim() || undefined,
      tools: selectedTools.length > 0 ? selectedTools : undefined, // Let AI decide if not provided
      profile: data.profile || 'normal',
      enable_ai: data.enable_ai,
    };

    // Show loading toast
    const loadingToast = toast.loading('Starting scan...');

    createScan(scanData, {
      onSuccess: (scan: any) => {
        toast.dismiss(loadingToast);
        toast.success('Scan started successfully!');
        router.push(`/scan/${scan.id}`);
      },
      onError: (error: any) => {
        toast.dismiss(loadingToast);
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to start scan';
        toast.error(`Scan failed: ${errorMessage}`);
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-3xl mx-auto space-y-4">
      {/* AI Objective Input - New Feature */}
      <div className="bg-[#2f2f2f] rounded-xl border border-[#565656] p-4">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-xl">🤖</span>
          <label className="text-sm font-semibold text-white">
            AI Agent Objective (Optional)
          </label>
        </div>
        <textarea
          {...register('user_prompt')}
          placeholder="Tell AI what you want to find... Example: 'Find SQL injection vulnerabilities and check for outdated software versions that could be exploited'"
          rows={3}
          className="w-full px-3 py-2 bg-[#1a1a1a] text-white placeholder-gray-500 border border-[#3e3e3e] rounded-lg focus:outline-none focus:border-blue-500 resize-none text-sm"
        />
        <p className="text-xs text-gray-500 mt-2">
          💡 AI will analyze your objective and automatically select the best tools & create attack strategy
        </p>
      </div>

      {/* Main Input Area - ChatGPT Style */}
      <div className="relative bg-[#2f2f2f] rounded-2xl border border-[#565656] shadow-lg">
        <textarea
          placeholder="Enter target to scan (e.g., scanme.nmap.org, 192.168.1.1)"
          {...register('target', { required: 'Target is required' })}
          rows={3}
          className="w-full px-5 py-4 pr-40 bg-transparent text-white placeholder-gray-500 focus:outline-none resize-none text-[15px] leading-relaxed"
        />

        {/* Action Buttons - Bottom Right */}
        <div className="absolute bottom-4 right-4 flex items-center space-x-2">
          {/* Tools Button */}
          <button
            type="button"
            onClick={() => setShowTools(!showTools)}
            className="p-2.5 rounded-lg bg-[#1a1a1a] hover:bg-[#252525] transition-colors border border-[#3e3e3e] group relative"
            title="Select Tools"
          >
            <Wrench className="h-4 w-4 text-gray-400 group-hover:text-white" />
            <span className="absolute -top-1.5 -right-1.5 bg-green-600 text-white text-[10px] font-semibold rounded-full w-4 h-4 flex items-center justify-center">
              {AVAILABLE_TOOLS.length}
            </span>
          </button>

          {/* API Key Button */}
          <button
            type="button"
            onClick={() => setShowApiKey(!showApiKey)}
            className={`p-2.5 rounded-lg transition-colors border ${
              geminiApiKey
                ? 'bg-green-600 hover:bg-green-700 border-green-600'
                : 'bg-[#1a1a1a] hover:bg-[#252525] border-[#3e3e3e]'
            }`}
            title="API Key"
          >
            <Key className={`h-4 w-4 ${geminiApiKey ? 'text-white' : 'text-gray-400'}`} />
          </button>

          {/* Settings Button */}
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            className="p-2.5 rounded-lg bg-[#1a1a1a] hover:bg-[#252525] transition-colors border border-[#3e3e3e] group"
            title="Settings"
          >
            <Settings className="h-4 w-4 text-gray-400 group-hover:text-white" />
          </button>
        </div>
      </div>

      {errors.target && (
        <p className="mt-2 text-sm text-red-400">{errors.target?.message as string}</p>
      )}

      {/* Tools Popup */}
      {showTools && (
        <div className="mt-4 bg-[#2f2f2f] border border-[#565656] rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Select Tools</h3>
            <button
              type="button"
              onClick={() => setShowTools(false)}
              className="text-gray-400 hover:text-white transition-colors text-lg"
            >
              ✕
            </button>
          </div>
          <div className="space-y-1">
            {AVAILABLE_TOOLS.map((tool) => (
              <label
                key={tool.id}
                className="flex items-start space-x-3 p-3 rounded-xl hover:bg-[#3a3a3a] cursor-pointer transition-all"
              >
                <input
                  type="checkbox"
                  value={tool.id}
                  defaultChecked
                  {...register('tools')}
                  className="mt-1 rounded bg-transparent border-gray-600 text-green-600 focus:ring-green-600 focus:ring-offset-0 focus:ring-1"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-white">{tool.name}</span>
                  <p className="text-xs text-gray-500 mt-0.5">{tool.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* API Key Popup */}
      {showApiKey && (
        <div className="mt-4 bg-[#2f2f2f] border border-[#565656] rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Google Gemini API Key</h3>
            <button
              type="button"
              onClick={() => setShowApiKey(false)}
              className="text-gray-400 hover:text-white transition-colors text-lg"
            >
              ✕
            </button>
          </div>
          <input
            type="password"
            placeholder="Enter your API key"
            defaultValue={geminiApiKey || ''}
            {...register('gemini_api_key', {
              required: enableAI ? 'API key required for AI analysis' : false,
            })}
            className="w-full px-4 py-3 bg-[#1a1a1a] text-white placeholder-gray-500 rounded-xl border border-[#3e3e3e] focus:border-[#565656] focus:outline-none text-sm"
          />
          {errors.gemini_api_key && (
            <p className="mt-2 text-xs text-red-400">{errors.gemini_api_key?.message as string}</p>
          )}
          <p className="mt-2 text-xs text-gray-500">Stored in browser session only</p>
        </div>
      )}

      {/* Settings Popup */}
      {showSettings && (
        <div className="mt-4 bg-[#2f2f2f] border border-[#565656] rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Scan Settings</h3>
            <button
              type="button"
              onClick={() => setShowSettings(false)}
              className="text-gray-400 hover:text-white transition-colors text-lg"
            >
              ✕
            </button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2">
                Scan Profile
              </label>
              <select
                {...register('profile')}
                defaultValue="normal"
                className="w-full px-4 py-3 bg-[#1a1a1a] text-white rounded-xl border border-[#3e3e3e] focus:border-[#565656] focus:outline-none text-sm"
              >
                {SCAN_PROFILES.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} - {profile.duration}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="flex items-center space-x-3 cursor-pointer p-3 rounded-xl hover:bg-[#3a3a3a] transition-all">
                <input
                  type="checkbox"
                  defaultChecked
                  {...register('enable_ai')}
                  className="rounded bg-transparent border-gray-600 text-green-600 focus:ring-green-600 focus:ring-offset-0 focus:ring-1"
                />
                <span className="text-sm text-white">Enable AI Analysis</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Submit Buttons - ChatGPT Style */}
      <div className="mt-6 flex justify-center space-x-4">
        {/* Live Streaming Scan - NEW! */}
        {enableAI && watch('user_prompt') && (
          <button
            type="button"
            disabled={isPending}
            onClick={handleSubmit((data: any) => {
              // Validate
              if (!data.target || !data.user_prompt) {
                toast.error('Target and AI Objective are required for live scan');
                return;
              }

              // Store API key if provided
              if (data.gemini_api_key) {
                setGeminiApiKey(data.gemini_api_key);
              }

              if (!geminiApiKey && !data.gemini_api_key) {
                toast.error('Gemini API key required for AI Agent');
                return;
              }

              // Build streaming URL
              const selectedTools = Array.isArray(data.tools)
                ? data.tools.filter((t: string) => t !== '').filter(Boolean)
                : ['nmap'];

              const params = new URLSearchParams({
                target: data.target.trim(),
                prompt: data.user_prompt.trim(),
                tools: selectedTools.join(','),
                profile: data.profile || 'normal',
              });

              toast.success('Starting live AI scan...');
              router.push(`/stream?${params.toString()}`);
            })}
            className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white rounded-xl font-medium text-sm transition-all duration-200 flex items-center space-x-2 shadow-lg disabled:shadow-none"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span>Live Scan (ChatGPT-style)</span>
          </button>
        )}

        {/* Regular Background Scan */}
        <button
          type="submit"
          disabled={isPending}
          className="px-8 py-3 bg-white hover:bg-gray-100 disabled:bg-gray-700 disabled:cursor-not-allowed text-black disabled:text-gray-500 rounded-xl font-medium text-sm transition-all duration-200 flex items-center space-x-2 shadow-lg disabled:shadow-none"
        >
          {isPending ? (
            <>
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Starting...</span>
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Start Scan</span>
            </>
          )}
        </button>
      </div>

      {enableAI && watch('user_prompt') && (
        <p className="text-center text-xs text-gray-500 mt-2">
          💡 <strong>Live Scan</strong> shows AI thinking in real-time like ChatGPT • <strong>Regular Scan</strong> runs in background
        </p>
      )}
    </form>
  );
};
