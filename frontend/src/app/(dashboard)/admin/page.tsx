'use client';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCriteria, updateCriterion, createCriterion, deactivateCriterion, getPeriods, createPeriod } from '@/lib/api';
import type { Criterion, Period } from '@/types';
import { cn } from '@/lib/utils';
import { Plus, Edit2, Trash2, Check, X, Star } from 'lucide-react';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'criteria' | 'periods'>('criteria');

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Администрирование</h1>
        <p className="text-gray-500 text-sm mt-0.5">Матрица критериев и управление периодами</p>
      </div>

      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {(['criteria', 'periods'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-1.5 rounded-md text-sm font-medium transition-colors',
              activeTab === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            )}
          >
            {tab === 'criteria' ? 'Критерии матрицы' : 'Периоды'}
          </button>
        ))}
      </div>

      {activeTab === 'criteria' ? <CriteriaAdmin /> : <PeriodsAdmin />}
    </div>
  );
}

function CriteriaAdmin() {
  const qc = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);

  const { data: criteria } = useQuery({
    queryKey: ['criteria', false],
    queryFn: () => getCriteria(false),
  });

  const { mutate: doUpdate } = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Criterion> }) => updateCriterion(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['criteria'] }); setEditingId(null); },
  });

  const { mutate: doCreate } = useMutation({
    mutationFn: (data: Partial<Criterion>) => createCriterion(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['criteria'] }); setShowNew(false); },
  });

  const { mutate: doDeactivate } = useMutation({
    mutationFn: (id: string) => deactivateCriterion(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['criteria'] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">{criteria?.length ?? 0} критериев</p>
        <button onClick={() => setShowNew(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Добавить критерий
        </button>
      </div>

      {showNew && (
        <CriterionForm
          onSave={(data) => doCreate(data)}
          onCancel={() => setShowNew(false)}
        />
      )}

      <div className="space-y-2">
        {criteria?.map(c => (
          editingId === c.criterion_id ? (
            <CriterionForm
              key={c.criterion_id}
              initial={c}
              onSave={(data) => doUpdate({ id: c.criterion_id, data })}
              onCancel={() => setEditingId(null)}
            />
          ) : (
            <CriterionRow
              key={c.criterion_id}
              criterion={c}
              onEdit={() => setEditingId(c.criterion_id)}
              onToggle={() => doUpdate({ id: c.criterion_id, data: { is_active: !c.is_active } })}
              onToggleKey={() => doUpdate({ id: c.criterion_id, data: { is_key_criterion: !c.is_key_criterion } })}
            />
          )
        ))}
      </div>
    </div>
  );
}

function CriterionRow({ criterion: c, onEdit, onToggle, onToggleKey }: {
  criterion: Criterion;
  onEdit: () => void;
  onToggle: () => void;
  onToggleKey: () => void;
}) {
  return (
    <div className={cn('card p-4 flex items-center gap-4', !c.is_active && 'opacity-50')}>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900 text-sm">{c.criterion_name}</span>
          {c.is_key_criterion && <span className="badge text-amber-600 bg-amber-50 border-amber-200">Ключевой</span>}
          {!c.is_active && <span className="badge text-gray-500 bg-gray-50 border-gray-200">Неактивен</span>}
        </div>
        <div className="text-xs text-gray-400 mt-0.5">Вес: {c.weight}</div>
      </div>
      <div className="flex items-center gap-2">
        <button onClick={onToggleKey} title="Ключевой критерий" className={cn('p-1.5 rounded-md transition-colors', c.is_key_criterion ? 'text-amber-500 bg-amber-50' : 'text-gray-300 hover:text-gray-500')}>
          <Star className="w-4 h-4" />
        </button>
        <button onClick={onEdit} className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
          <Edit2 className="w-4 h-4" />
        </button>
        <button onClick={onToggle} className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
          {c.is_active ? <X className="w-4 h-4" /> : <Check className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}

function CriterionForm({ initial, onSave, onCancel }: {
  initial?: Criterion;
  onSave: (data: Partial<Criterion>) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    criterion_name: initial?.criterion_name ?? '',
    below_description: initial?.below_description ?? '',
    meet_description: initial?.meet_description ?? '',
    exceeds_description: initial?.exceeds_description ?? '',
    weight: initial?.weight ?? 1.0,
    is_key_criterion: initial?.is_key_criterion ?? false,
  });

  return (
    <div className="card p-5 border-brand-200 bg-brand-50">
      <h3 className="text-sm font-medium text-gray-900 mb-4">
        {initial ? 'Редактировать критерий' : 'Новый критерий'}
      </h3>
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Название</label>
          <input
            value={form.criterion_name}
            onChange={e => setForm(f => ({ ...f, criterion_name: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Название критерия"
          />
        </div>
        {(['below', 'meet', 'exceeds'] as const).map(level => (
          <div key={level}>
            <label className="block text-xs font-medium text-gray-600 mb-1 capitalize">
              {level === 'below' ? 'Below expectations' : level === 'meet' ? 'Meet expectations' : 'Exceeds expectations'}
            </label>
            <textarea
              value={form[`${level}_description` as keyof typeof form] as string}
              onChange={e => setForm(f => ({ ...f, [`${level}_description`]: e.target.value }))}
              rows={2}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
              placeholder={`Описание уровня ${level}...`}
            />
          </div>
        ))}
        <div className="flex gap-4 items-center">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Вес</label>
            <input
              type="number"
              min="0.5"
              max="3"
              step="0.1"
              value={form.weight}
              onChange={e => setForm(f => ({ ...f, weight: parseFloat(e.target.value) }))}
              className="w-24 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer mt-4">
            <input
              type="checkbox"
              checked={form.is_key_criterion}
              onChange={e => setForm(f => ({ ...f, is_key_criterion: e.target.checked }))}
              className="rounded"
            />
            Ключевой критерий
          </label>
        </div>
      </div>
      <div className="flex gap-2 mt-4">
        <button onClick={() => onSave(form)} className="btn-primary">Сохранить</button>
        <button onClick={onCancel} className="btn-secondary">Отмена</button>
      </div>
    </div>
  );
}

function PeriodsAdmin() {
  const qc = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const { data: periods } = useQuery({ queryKey: ['periods'], queryFn: getPeriods });

  const { mutate: doCreate } = useMutation({
    mutationFn: (data: Partial<Period>) => createPeriod(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['periods'] }); setShowNew(false); },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">{periods?.length ?? 0} периодов</p>
        <button onClick={() => setShowNew(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Добавить период
        </button>
      </div>

      {showNew && (
        <PeriodForm onSave={(d) => doCreate(d)} onCancel={() => setShowNew(false)} />
      )}

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Период</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Начало</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Конец</th>
              <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Статус</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {periods?.map(p => (
              <tr key={p.period_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{p.period_name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{p.start_date}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{p.end_date}</td>
                <td className="px-4 py-3 text-center">
                  <span className={cn('badge', p.is_active ? 'text-green-700 bg-green-50 border-green-200' : 'text-gray-500 bg-gray-50 border-gray-200')}>
                    {p.is_active ? 'Активен' : 'Закрыт'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PeriodForm({ onSave, onCancel }: { onSave: (d: Partial<Period>) => void; onCancel: () => void }) {
  const [form, setForm] = useState({ period_name: '', start_date: '', end_date: '', is_active: true });

  return (
    <div className="card p-5 mb-4 border-brand-200 bg-brand-50">
      <h3 className="text-sm font-medium text-gray-900 mb-4">Новый период</h3>
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-3">
          <input
            value={form.period_name}
            onChange={e => setForm(f => ({ ...f, period_name: e.target.value }))}
            placeholder="Название (напр. Q2 2026)"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <input type="date" value={form.start_date} onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
        <input type="date" value={form.end_date} onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
        <div className="flex gap-2">
          <button onClick={() => onSave(form)} className="btn-primary">Создать</button>
          <button onClick={onCancel} className="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>
  );
}
