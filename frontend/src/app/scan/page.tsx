'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

function ScanRedirectContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // If we have query params (target, prompt), redirect to stream
    const target = searchParams.get('target');
    const prompt = searchParams.get('prompt');
    
    if (target) {
      const params = new URLSearchParams();
      params.set('target', target);
      if (prompt) params.set('prompt', prompt);
      router.replace(`/stream?${params.toString()}`);
    } else {
      // Otherwise redirect to home (new scan page)
      router.replace('/');
    }
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-600 border-t-transparent"></div>
    </div>
  );
}

export default function NewScanPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-600 border-t-transparent"></div>
      </div>
    }>
      <ScanRedirectContent />
    </Suspense>
  );
}
