'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { StepIndicator } from '@/components/onboarding/StepIndicator';
import { StepWelcome } from '@/components/onboarding/StepWelcome';
import { StepPhone } from '@/components/onboarding/StepPhone';
import { StepCRMSettings } from '@/components/onboarding/StepCRMSettings';
import { StepGreeting } from '@/components/onboarding/StepGreeting';
import { StepSuccess } from '@/components/onboarding/StepSuccess';
import type { OnboardingData } from '@/lib/types';

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0); // 0 = welcome, 1-3 = wizard, 4 = success

  const handleSkip = () => {
    document.cookie = 'allo_onboarded=true;path=/;max-age=31536000';
    router.replace('/dashboard');
  };

  const handleFinish = () => {
    document.cookie = 'allo_onboarded=true;path=/;max-age=31536000';
    router.replace('/dashboard');
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center text-white font-bold text-sm">
            А
          </div>
          <span className="text-lg font-bold text-text-primary">Алло</span>
        </div>

        {/* Step indicator (only shown during wizard) */}
        {step > 0 && step < 4 && <StepIndicator currentStep={step} />}

        {step === 0 && (
          <StepWelcome
            onNext={() => setStep(1)}
            onSkip={handleSkip}
          />
        )}

        {step === 1 && (
          <StepPhone
            onNext={() => setStep(2)}
            onBack={() => setStep(0)}
          />
        )}

        {step === 2 && (
          <StepCRMSettings
            onNext={() => setStep(3)}
            onBack={() => setStep(1)}
          />
        )}

        {step === 3 && (
          <StepGreeting
            onNext={() => setStep(4)}
            onBack={() => setStep(2)}
          />
        )}

        {step === 4 && (
          <StepSuccess onFinish={handleFinish} />
        )}
      </div>
    </div>
  );
}
