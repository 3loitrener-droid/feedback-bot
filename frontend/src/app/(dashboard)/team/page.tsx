'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { getEmployeesWithStats, getPeriods } from '@/lib/api';
import { getRatingColor, getRatingLabel, cn } from '@/lib/utils';
import type { EmployeeStats } from '@/types';
import { Users, AlertCircle, ChevronRight } from 'lucide-react';

export default function TeamPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');

  const { data: periods } = useQuery({
    queryKey: ['periods'],
    queryFn: getPeriods,
  });

  const { data: employees, isLoading } = useQuery({
    queryKey: ['employees-stats', selectedPeriod],
    queryFn: () => getEmployeesWithStats(selectedPeriod || undefined),
  });

  const activePeriods = periods?.filter(p => p.is_active) ?? [];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Моя команда</h1>
          <p className="text-gray-500 text-sm mt-0.5">Фидбэк и статус по каждому сотруднику</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedPeriod}
            onChange={e => setSelectedPeriod(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">Все периоды</option>
            {periods?.map(p => (
              <option key={p.period_id} value={p.period_id}>{p.period_name}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !employees?.length ? (
        <div className="card p-12 text-center">
          <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Команда пуста. Обратитесь к администратору.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Сотрудник</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Комментарии</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Размечено</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Без критерия</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Сильные зоны</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Рекомендация</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {employees.map(emp => (
                <EmployeeRow key={emp.employee_id} employee={emp} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function EmployeeRow({ employee: emp }: { employee: EmployeeStats }) {
  const hasUnmapped = emp.unmapped_feedback > 0;

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3.5">
        <div>
          <p className="font-medium text-gray-900 text-sm">{emp.full_name}</p>
          {emp.position && <p className="text-xs text-gray-500">{emp.position}</p>}
        </div>
      </td>
      <td className="px-4 py-3.5 text-center">
        <span className="text-sm font-medium text-gray-900">{emp.total_feedback}</span>
      </td>
      <td className="px-4 py-3.5 text-center">
        <span className="text-sm text-gray-700">{emp.mapped_feedback}</span>
      </td>
      <td className="px-4 py-3.5 text-center">
        {hasUnmapped ? (
          <span className="inline-flex items-center gap-1 text-sm text-amber-600">
            <AlertCircle className="w-3.5 h-3.5" />
            {emp.unmapped_feedback}
          </span>
        ) : (
          <span className="text-sm text-gray-400">0</span>
        )}
      </td>
      <td className="px-4 py-3.5">
        <div className="flex flex-wrap gap-1">
          {emp.top_strengths.slice(0, 2).map(s => (
            <span key={s} className="badge text-green-700 bg-green-50 border-green-200">
              {s.split(' ').slice(0, 2).join(' ')}
            </span>
          ))}
        </div>
      </td>
      <td className="px-4 py-3.5">
        {emp.rating_recommendation ? (
          <span className={cn('badge', getRatingColor(emp.rating_recommendation))}>
            {getRatingLabel(emp.rating_recommendation)}
          </span>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>
      <td className="px-4 py-3.5">
        <Link
          href={`/employees/${emp.employee_id}`}
          className="text-brand-500 hover:text-brand-600 flex items-center gap-1 text-sm"
        >
          Открыть <ChevronRight className="w-4 h-4" />
        </Link>
      </td>
    </tr>
  );
}
