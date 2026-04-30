'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Simple check: if no onboarding cookie, show onboarding
export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const onboarded = document.cookie.includes('allo_onboarded=true');
    if (onboarded) {
      router.replace('/dashboard');
    } else {
      router.replace('/onboarding');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="w-10 h-10 rounded-full bg-primary-500 animate-pulse" />
    </div>
  );
}
