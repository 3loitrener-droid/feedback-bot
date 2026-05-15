'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getFeedback, getEmployees, getPeriods, getCriteria } from '@/lib/api';
import { formatDate, STATUS_LABELS, STATUS_COLORS, getRatingColor, getRatingLabel, cn } from '@/lib/utils';
import type { Feedback } from '@/types';

export default function TimelinePage() {
  const [employeeId, setEmployeeId] = useState('');
  const [periodId, setPeriodId] = useState('');
  const [status, setStatus] = useState('');
  const [criterionName, setCriterionName] = useState('');
  const [ratingFilter, setRatingFilter] = useState('');

  const { data: employees } = useQuery({ queryKey: ['employees'], queryFn: getEmployees });
  const { data: periods } = useQuery({ queryKey: ['periods'], queryFn: getPeriods });
  const { data: criteria } = useQuery({ queryKey: ['criteria'], queryFn: () => getCriteria() });

  const { data: feedbacks, isLoading } = useQuery({
    queryKey: ['feedback-timeline', employeeId, periodId, status],
    queryFn: () => getFeedback({
      employee_id: employeeId || undefined,
      period_id: periodId || undefined,
      status: status || undefined,
      limit: 100,
    }),
  });

  const filtered = feedbacks?.filter(fb => {
    if (!criterionName && !ratingFilter) return true;
    return fb.mappings.some(m =>
      (!criterionName || m.criterion_name?.toLowerCase().includes(criterionName.toLowerCase())) &&
      (!ratingFilter || m.confirmed_rating === ratingFilter || m.suggested_rating === ratingFilter)
    );
  }) ?? [];

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Хронология</h1>
        <p className="text-gray-500 text-sm mt-0.5">Все комментарии с оригинальным текстом</p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6 flex flex-wrap gap-3">
        <select
          value={employeeId}
          onChange={e => setEmployeeId(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">Все сотрудники</option>
          {employees?.map(e => <option key={e.employee_id} value={e.employee_id}>{e.full_name}</option>)}
        </select>

        <select
          value={periodId}
          onChange={e => setPeriodId(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">Все периоды</option>
          {periods?.map(p => <option key={p.period_id} value={p.period_id}>{p.period_name}</option>)}
        </select>

        <select
          value={status}
          onChange={e => setStatus(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">Все статусы</option>
          <option value="confirmed">Подтверждён</option>
          <option value="no_criterion">Без критерия</option>
          <option value="needs_review">Требует проверки</option>
        </select>

        <select
          value={ratingFilter}
          onChange={e => setRatingFilter(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">Все оценки</option>
          <option value="Below expectations">Below</option>
          <option value="Meet expectations">Meet</option>
          <option value="Exceeds expectations">Exceeds</option>
        </select>

        <input
          type="text"
          placeholder="Поиск по критерию..."
          value={criterionName}
          onChange={e => setCriterionName(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-44"
        />

        <span className="ml-auto text-sm text-gray-500 self-center">{filtered.length} комментариев</span>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(fb => <TimelineCard key={fb.feedback_id} feedback={fb} />)}
          {!filtered.length && (
            <div className="card p-12 text-center text-gray-400">Комментариев не найдено.</div>
          )}
        </div>
      )}
    </div>
  );
}

function TimelineCard({ feedback: fb }: { feedback: Feedback }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm text-gray-500">{formatDate(fb.feedback_date)}</span>
        <span className={cn('badge', STATUS_COLORS[fb.status])}>{STATUS_LABELS[fb.status]}</span>
        {fb.employee_name && (
          <span className="badge text-gray-600 bg-gray-50 border-gray-200">{fb.employee_name}</span>
        )}
        <span className="badge text-gray-400 bg-gray-50 border-gray-200 ml-auto">{fb.source}</span>
      </div>

      <div className="original-text mb-3">
        «{fb.original_text}»
      </div>

      {fb.mappings.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {fb.mappings.map(m => {
            const rating = m.confirmed_rating ?? m.suggested_rating;
            return (
              <div key={m.mapping_id} className="flex items-center gap-1.5 text-xs">
                <span className="text-gray-600 font-medium">{m.criterion_name}</span>
                {rating && (
                  <span className={cn('badge', getRatingColor(rating))}>
                    {getRatingLabel(rating)}
                  </span>
                )}
                {!m.manager_confirmed && (
                  <span className="text-blue-400 text-xs">~LLM</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
