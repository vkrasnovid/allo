'use client';

import { cn } from '@/lib/utils';
import { ONBOARDING_STEPS } from '@/lib/types';
import { Check } from 'lucide-react';

interface StepIndicatorProps {
  currentStep: number;
}

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {ONBOARDING_STEPS.map((step, index) => {
        const stepNum = index + 1;
        const isCompleted = currentStep > stepNum;
        const isActive = currentStep === stepNum;
        const isUpcoming = currentStep < stepNum;

        return (
          <div key={step.id} className="flex items-center gap-2 flex-1">
            <div className={cn(
              'flex items-center gap-2',
              isUpcoming && 'opacity-40'
            )}>
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors',
                isCompleted && 'bg-success text-white',
                isActive && 'bg-primary-500 text-white',
                isUpcoming && 'bg-gray-100 text-text-tertiary'
              )}>
                {isCompleted ? <Check size={16} /> : stepNum}
              </div>
              <span className={cn(
                'text-sm font-medium hidden md:inline',
                isActive && 'text-primary-500',
                isCompleted && 'text-text-primary',
                isUpcoming && 'text-text-tertiary'
              )}>
                {step.label}
              </span>
            </div>
            {index < ONBOARDING_STEPS.length - 1 && (
              <div className={cn(
                'flex-1 h-px mx-1',
                isCompleted ? 'bg-success' : 'bg-border'
              )} />
            )}
          </div>
        );
      })}
    </div>
  );
}
