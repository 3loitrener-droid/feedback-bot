import type { Rating } from '@/types';

export const RATING_COLORS: Record<string, string> = {
  'Below expectations': 'text-red-600 bg-red-50 border-red-200',
  'Meet expectations': 'text-amber-600 bg-amber-50 border-amber-200',
  'Exceeds expectations': 'text-green-600 bg-green-50 border-green-200',
  'insufficient_data': 'text-gray-500 bg-gray-50 border-gray-200',
};

export const RATING_DOT: Record<string, string> = {
  'Below expectations': 'bg-red-500',
  'Meet expectations': 'bg-amber-400',
  'Exceeds expectations': 'bg-green-500',
};

export const RATING_LABEL: Record<string, string> = {
  'Below expectations': 'Below',
  'Meet expectations': 'Meet',
  'Exceeds expectations': 'Exceeds',
  'insufficient_data': 'Нет данных',
};

export const STATUS_LABELS: Record<string, string> = {
  confirmed: 'Подтверждён',
  draft: 'Черновик',
  no_criterion: 'Без критерия',
  needs_review: 'Требует проверки',
};

export const STATUS_COLORS: Record<string, string> = {
  confirmed: 'text-green-700 bg-green-50',
  draft: 'text-blue-700 bg-blue-50',
  no_criterion: 'text-amber-700 bg-amber-50',
  needs_review: 'text-red-700 bg-red-50',
};

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

export function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function getRatingColor(rating?: string): string {
  return RATING_COLORS[rating ?? ''] ?? 'text-gray-500 bg-gray-50 border-gray-200';
}

export function getRatingLabel(rating?: string): string {
  return RATING_LABEL[rating ?? ''] ?? '—';
}
