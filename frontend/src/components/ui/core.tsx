import React from 'react';
import { cn } from '../../lib/utils';

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn('glass-card p-6 flex flex-col', className)}>
      {children}
    </div>
  );
}

export function Badge({ children, variant = 'default', className }: { children: React.ReactNode; variant?: 'default' | 'success' | 'warning' | 'danger', className?: string }) {
  const variants = {
    default: 'bg-primary/20 text-primary border-primary/50',
    success: 'bg-risk-low/20 text-risk-low border-risk-low/50',
    warning: 'bg-risk-medium/20 text-risk-medium border-risk-medium/50',
    danger: 'bg-risk-critical/20 text-risk-critical border-risk-critical/50',
  };
  return (
    <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-semibold border', variants[variant], className)}>
      {children}
    </span>
  );
}

export function Button({ className, children, variant = 'primary', ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'outline' }) {
  const variants = {
    primary: 'bg-primary text-white hover:bg-primary-hover border border-transparent shadow-lg shadow-primary/20',
    secondary: 'bg-secondary text-white hover:bg-secondary-hover border border-transparent',
    outline: 'bg-transparent text-white border border-white/20 hover:bg-white/10',
  };
  return (
    <button className={cn('px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2', variants[variant], className)} {...props}>
      {children}
    </button>
  );
}
