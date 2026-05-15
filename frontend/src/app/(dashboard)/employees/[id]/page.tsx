'use client';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import {
  getEmployee, getFeedback, getSummary, generateSummary, getPeriods,
  updateMapping, deleteMapping, addMapping, getCriteria, downloadSummary,
} from '@/lib/api';
import {
  getRatingColor, getRatingLabel, formatDate, formatDateShort,
  STATUS_LABELS, STATUS_COLORS, cn, RATING_COLORS,
} from '@/lib/utils';
import type { Feedback, FeedbackMapping, Rating, Summary, Criterion } from '@/types';
import { ChevronLeft, RefreshCw, AlertCircle, Edit2, Trash2, Plus, Download } from 'lucide-react';
import Link from 'next/link';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function EmployeePage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [editingFeedback, setEditingFeedback] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'matrix' | 'review'>('timeline');

  const { data: employee } = useQuery({ queryKey: ['employee', id], queryFn: () => getEmployee(id) });
  const { data: periods } = useQuery({ queryKey: ['periods'], queryFn: getPeriods });
  const { data: criteria } = useQuery({ queryKey: ['criteria'], queryFn: () => getCriteria() });

  const activePeriodId = selectedPeriod || periods?.find(p => p.is_active)?.period_id || periods?.[0]?.period_id;

  const { data: feedbacks, isLoading: feedbacksLoading } = useQuery({
    queryKey: ['feedback', id, activePeriodId],
    queryFn: () => getFeedback({ employee_id: id, period_id: activePeriodId, limit: 100 }),
    enabled: !!id,
  });

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['summary', id, activePeriodId],
    queryFn: () => activePeriodId ? getSummary(id, activePeriodId) : null,
    enabled: !!activePeriodId,
  });

  const { mutate: triggerSummary, isPending: summaryGenerating } = useMutation({
    mutationFn: () => generateSummary(id, activePeriodId!),
    onSuccess: () => {
      setTimeout(() => qc.invalidateQueries({ queryKey: ['summary', id, activePeriodId] }), 3000);
    },
  });

  if (!employee) return <div className="p-8 text-gray-500">Загрузка...</div>;

  const currentPeriod = periods?.find(p => p.period_id === activePeriodId);

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/team" className="text-gray-400 hover:text-gray-600">
          <ChevronLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-xl font-semibold text-gray-900">{employee.full_name}</h1>
          <p className="text-gray-500 text-sm">{employee.position} {employee.level && `· ${employee.level}`}</p>
        </div>
        <select
          value={selectedPeriod}
          onChange={e => setSelectedPeriod(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          {periods?.map(p => (
            <option key={p.period_id} value={p.period_id}>{p.period_name}</option>
          ))}
        </select>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Всего" value={feedbacks?.length ?? 0} />
        <StatCard label="Размечено" value={feedbacks?.filter(f => f.status !== 'no_criterion').length ?? 0} color="blue" />
        <StatCard
          label="Без критерия"
          value={feedbacks?.filter(f => f.status === 'no_criterion').length ?? 0}
          color="amber"
        />
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1">Рекомендация</p>
          {summary?.rating_recommendation ? (
            <span className={cn('badge', getRatingColor(summary.rating_recommendation))}>
              {getRatingLabel(summary.rating_recommendation)}
            </span>
          ) : (
            <span className="text-sm text-gray-400">—</span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {(['timeline', 'matrix', 'review'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-1.5 rounded-md text-sm font-medium transition-colors',
              activeTab === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            )}
          >
            {tab === 'timeline' ? 'Хронология' : tab === 'matrix' ? 'Матрица' : 'Performance Review'}
          </button>
        ))}
      </div>

      {activeTab === 'timeline' && (
        <TimelineTab
          feedbacks={feedbacks ?? []}
          loading={feedbacksLoading}
          criteria={criteria ?? []}
          editingFeedback={editingFeedback}
          onEditToggle={setEditingFeedback}
        />
      )}

      {activeTab === 'matrix' && (
        <MatrixTab feedbacks={feedbacks ?? []} criteria={criteria ?? []} />
      )}

      {activeTab === 'review' && (
        <ReviewTab
          summary={summary ?? null}
          loading={summaryLoading}
          generating={summaryGenerating}
          onGenerate={() => triggerSummary()}
          hasPeriod={!!activePeriodId}
          periodName={currentPeriod?.period_name ?? ''}
          employeeId={id}
          periodId={activePeriodId}
        />
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color?: string }) {
  const colors = { blue: 'text-blue-600', amber: 'text-amber-600', default: 'text-gray-900' };
  return (
    <div className="card p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={cn('text-2xl font-semibold', colors[color as keyof typeof colors] ?? colors.default)}>{value}</p>
    </div>
  );
}

// ─── Timeline ───────────────────────────────────────────────────────────────

function TimelineTab({ feedbacks, loading, criteria, editingFeedback, onEditToggle }: {
  feedbacks: Feedback[];
  loading: boolean;
  criteria: Criterion[];
  editingFeedback: string | null;
  onEditToggle: (id: string | null) => void;
}) {
  const qc = useQueryClient();

  if (loading) return <div className="text-gray-400 text-sm">Загрузка...</div>;
  if (!feedbacks.length) return (
    <div className="card p-12 text-center text-gray-400">Комментариев нет за этот период.</div>
  );

  return (
    <div className="space-y-4">
      {feedbacks.map(fb => (
        <FeedbackCard
          key={fb.feedback_id}
          feedback={fb}
          criteria={criteria}
          isEditing={editingFeedback === fb.feedback_id}
          onEditToggle={() => onEditToggle(editingFeedback === fb.feedback_id ? null : fb.feedback_id)}
        />
      ))}
    </div>
  );
}

function FeedbackCard({ feedback: fb, criteria, isEditing, onEditToggle }: {
  feedback: Feedback;
  criteria: Criterion[];
  isEditing: boolean;
  onEditToggle: () => void;
}) {
  const qc = useQueryClient();

  const { mutate: removeFeedbackMapping } = useMutation({
    mutationFn: ({ mappingId }: { mappingId: string }) => deleteMapping(fb.feedback_id, mappingId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['feedback'] }),
  });

  const { mutate: updateFeedbackMapping } = useMutation({
    mutationFn: ({ mappingId, data }: { mappingId: string; data: Partial<FeedbackMapping> }) =>
      updateMapping(fb.feedback_id, mappingId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['feedback'] }),
  });

  const { mutate: addFeedbackMapping } = useMutation({
    mutationFn: (data: Partial<FeedbackMapping>) => addMapping(fb.feedback_id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['feedback'] }),
  });

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">{formatDate(fb.feedback_date)}</span>
          <span className={cn('badge', STATUS_COLORS[fb.status])}>
            {STATUS_LABELS[fb.status]}
          </span>
          <span className="badge text-gray-500 bg-gray-50 border-gray-200">{fb.source}</span>
        </div>
        <button
          onClick={onEditToggle}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <Edit2 className="w-4 h-4" />
        </button>
      </div>

      {/* Оригинальный текст — всегда показываем, неизменно */}
      <div className="original-text mb-4">
        «{fb.original_text}»
      </div>

      {/* Связки */}
      {fb.mappings.length > 0 && (
        <div className="space-y-2">
          {fb.mappings.map(m => (
            <MappingRow
              key={m.mapping_id}
              mapping={m}
              isEditing={isEditing}
              onRatingChange={(rating) => updateFeedbackMapping({
                mappingId: m.mapping_id,
                data: { confirmed_rating: rating, manager_confirmed: true },
              })}
              onDelete={() => removeFeedbackMapping({ mappingId: m.mapping_id })}
            />
          ))}
        </div>
      )}

      {isEditing && (
        <AddMappingForm
          criteria={criteria}
          onAdd={(criterionId, rating, fragment) => addFeedbackMapping({
            criterion_id: criterionId,
            confirmed_rating: rating,
            original_fragment: fragment || fb.original_text.slice(0, 100),
            manager_confirmed: true,
          })}
        />
      )}
    </div>
  );
}

function MappingRow({ mapping: m, isEditing, onRatingChange, onDelete }: {
  mapping: FeedbackMapping;
  isEditing: boolean;
  onRatingChange: (rating: Rating) => void;
  onDelete: () => void;
}) {
  const displayRating = m.confirmed_rating ?? m.suggested_rating;

  return (
    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-gray-800">{m.criterion_name}</span>
          {!m.manager_confirmed && (
            <span className="badge text-blue-600 bg-blue-50 border-blue-200">LLM предложение</span>
          )}
        </div>
        {m.original_fragment && (
          <p className="text-xs text-gray-500 italic">«{m.original_fragment.slice(0, 100)}»</p>
        )}
        {m.llm_explanation && (
          <p className="text-xs text-gray-400 mt-0.5">{m.llm_explanation}</p>
        )}
      </div>

      {isEditing ? (
        <div className="flex items-center gap-2">
          {(['Below expectations', 'Meet expectations', 'Exceeds expectations'] as Rating[]).map(r => (
            <button
              key={r}
              onClick={() => onRatingChange(r)}
              className={cn(
                'px-2 py-1 rounded text-xs font-medium border transition-colors',
                displayRating === r
                  ? getRatingColor(r)
                  : 'text-gray-400 border-gray-200 hover:bg-gray-100'
              )}
            >
              {getRatingLabel(r)}
            </button>
          ))}
          <button onClick={onDelete} className="text-red-400 hover:text-red-600 transition-colors">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ) : (
        displayRating && (
          <span className={cn('badge', getRatingColor(displayRating))}>
            {getRatingLabel(displayRating)}
          </span>
        )
      )}
    </div>
  );
}

function AddMappingForm({ criteria, onAdd }: {
  criteria: Criterion[];
  onAdd: (criterionId: string, rating: Rating, fragment?: string) => void;
}) {
  const [criterionId, setCriterionId] = useState('');
  const [rating, setRating] = useState<Rating>('Meet expectations');
  const [fragment, setFragment] = useState('');

  return (
    <div className="mt-3 p-3 border border-dashed border-gray-300 rounded-lg">
      <p className="text-xs font-medium text-gray-600 mb-2">+ Добавить связку</p>
      <div className="flex gap-2 flex-wrap">
        <select
          value={criterionId}
          onChange={e => setCriterionId(e.target.value)}
          className="flex-1 min-w-40 px-2 py-1.5 border border-gray-200 rounded text-xs bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">Выбери критерий</option>
          {criteria.map(c => (
            <option key={c.criterion_id} value={c.criterion_id}>{c.criterion_name}</option>
          ))}
        </select>
        <select
          value={rating}
          onChange={e => setRating(e.target.value as Rating)}
          className="px-2 py-1.5 border border-gray-200 rounded text-xs bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="Below expectations">Below</option>
          <option value="Meet expectations">Meet</option>
          <option value="Exceeds expectations">Exceeds</option>
        </select>
        <button
          onClick={() => { if (criterionId && rating) { onAdd(criterionId, rating, fragment); setCriterionId(''); } }}
          disabled={!criterionId}
          className="btn-primary py-1.5 disabled:opacity-50"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

// ─── Matrix ─────────────────────────────────────────────────────────────────

function MatrixTab({ feedbacks, criteria }: { feedbacks: Feedback[]; criteria: Criterion[] }) {
  const stats: Record<string, { below: number; meet: number; exceeds: number; quotes: string[] }> = {};

  for (const fb of feedbacks) {
    for (const m of fb.mappings) {
      const name = m.criterion_name ?? 'Неизвестно';
      if (!stats[name]) stats[name] = { below: 0, meet: 0, exceeds: 0, quotes: [] };
      const rating = m.confirmed_rating ?? m.suggested_rating;
      if (rating === 'Below expectations') stats[name].below++;
      else if (rating === 'Meet expectations') stats[name].meet++;
      else if (rating === 'Exceeds expectations') stats[name].exceeds++;
      if (m.original_fragment) stats[name].quotes.push(m.original_fragment);
    }
  }

  const chartData = Object.entries(stats).map(([name, s]) => ({
    name: name.split(' ').slice(0, 2).join(' '),
    fullName: name,
    Below: s.below,
    Meet: s.meet,
    Exceeds: s.exceeds,
    total: s.below + s.meet + s.exceeds,
  })).sort((a, b) => b.total - a.total);

  if (!chartData.length) return (
    <div className="card p-12 text-center text-gray-400">Размеченных комментариев нет.</div>
  );

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h3 className="font-medium text-gray-900 mb-4 text-sm">Распределение оценок по критериям</h3>
        <ResponsiveContainer width="100%" height={Math.max(chartData.length * 36, 120)}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
            <Tooltip />
            <Bar dataKey="Below" stackId="a" fill="#ef4444" name="Below" />
            <Bar dataKey="Meet" stackId="a" fill="#f59e0b" name="Meet" />
            <Bar dataKey="Exceeds" stackId="a" fill="#22c55e" name="Exceeds" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Критерий</th>
              <th className="text-center px-4 py-3 text-xs font-medium text-red-500 uppercase">Below</th>
              <th className="text-center px-4 py-3 text-xs font-medium text-amber-500 uppercase">Meet</th>
              <th className="text-center px-4 py-3 text-xs font-medium text-green-500 uppercase">Exceeds</th>
              <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Всего</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {Object.entries(stats).sort((a, b) => (b[1].below + b[1].meet + b[1].exceeds) - (a[1].below + a[1].meet + a[1].exceeds)).map(([name, s]) => (
              <tr key={name} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-800">{name}</td>
                <td className="px-4 py-3 text-center">
                  {s.below > 0 ? <span className="font-semibold text-red-600">{s.below}</span> : <span className="text-gray-300">0</span>}
                </td>
                <td className="px-4 py-3 text-center">
                  {s.meet > 0 ? <span className="font-semibold text-amber-600">{s.meet}</span> : <span className="text-gray-300">0</span>}
                </td>
                <td className="px-4 py-3 text-center">
                  {s.exceeds > 0 ? <span className="font-semibold text-green-600">{s.exceeds}</span> : <span className="text-gray-300">0</span>}
                </td>
                <td className="px-4 py-3 text-center text-sm text-gray-600">{s.below + s.meet + s.exceeds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Performance Review ──────────────────────────────────────────────────────

function ReviewTab({ summary, loading, generating, onGenerate, hasPeriod, periodName, employeeId, periodId }: {
  summary: Summary | null;
  loading: boolean;
  generating: boolean;
  onGenerate: () => void;
  hasPeriod: boolean;
  periodName: string;
  employeeId: string;
  periodId?: string;
}) {
  if (loading) return <div className="text-gray-400 text-sm">Загрузка summary...</div>;

  if (!summary) return (
    <div className="card p-12 text-center">
      <p className="text-gray-500 text-sm mb-4">
        Summary за выбранный период не сгенерировано.
        {hasPeriod ? ' Нажми кнопку ниже для генерации.' : ' Выбери период.'}
      </p>
      {hasPeriod && (
        <button onClick={onGenerate} disabled={generating} className="btn-primary">
          {generating ? (
            <span className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin" /> Генерируем...
            </span>
          ) : 'Сгенерировать summary'}
        </button>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Recommendation block */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Рекомендация системы</h3>
          <div className="flex items-center gap-2">
            {periodId && (
              <button
                onClick={() => downloadSummary(employeeId, periodId)}
                className="btn-secondary flex items-center gap-2 text-xs"
              >
                <Download className="w-3.5 h-3.5" /> Экспорт HTML
              </button>
            )}
            <button onClick={onGenerate} disabled={generating} className="btn-secondary flex items-center gap-2 text-xs">
              <RefreshCw className={cn('w-3.5 h-3.5', generating && 'animate-spin')} />
              Обновить
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <span className={cn('px-4 py-2 rounded-lg font-medium text-sm border', getRatingColor(summary.rating_recommendation))}>
            {getRatingLabel(summary.rating_recommendation)}
          </span>
          {summary.llm_model_version && (
            <span className="text-xs text-gray-400">Модель: {summary.llm_model_version}</span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          {summary.arguments_for?.length ? (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase mb-2">Аргументы за</p>
              {summary.arguments_for.map((a, i) => (
                <p key={i} className="text-sm text-gray-700 flex gap-2 mb-1">
                  <span className="text-green-500 flex-shrink-0">+</span>{a}
                </p>
              ))}
            </div>
          ) : null}
          {summary.arguments_against?.length ? (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase mb-2">Риски</p>
              {summary.arguments_against.map((a, i) => (
                <p key={i} className="text-sm text-gray-700 flex gap-2 mb-1">
                  <span className="text-red-500 flex-shrink-0">−</span>{a}
                </p>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {/* Strengths */}
      {summary.strengths?.length ? (
        <div className="card p-6">
          <h3 className="font-medium text-gray-900 mb-4 text-sm">✅ Сильные зоны</h3>
          <div className="space-y-4">
            {summary.strengths.map((s, i) => (
              <div key={i}>
                <p className="font-medium text-gray-800 text-sm mb-1">{s.criterion_name}</p>
                <p className="text-xs text-gray-500 mb-2">{s.pattern_description}</p>
                {s.evidence_quotes.map((q, j) => (
                  <div key={j} className="original-text text-xs mb-1">«{q}»</div>
                ))}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Growth areas */}
      {summary.growth_areas?.length ? (
        <div className="card p-6">
          <h3 className="font-medium text-gray-900 mb-4 text-sm">⚠️ Зоны роста</h3>
          <div className="space-y-4">
            {summary.growth_areas.map((g, i) => (
              <div key={i}>
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-gray-800 text-sm">{g.criterion_name}</p>
                  {g.is_systemic && (
                    <span className="badge text-red-600 bg-red-50 border-red-200">Системная проблема</span>
                  )}
                  {g.is_key_criterion && (
                    <span className="badge text-purple-600 bg-purple-50 border-purple-200">Ключевой критерий</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mb-2">{g.pattern_description}</p>
                {g.evidence_quotes.map((q, j) => (
                  <div key={j} className="original-text text-xs mb-1">«{q}»</div>
                ))}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Needs attention */}
      {summary.needs_attention?.length ? (
        <div className="card p-6 border-amber-200 bg-amber-50">
          <h3 className="font-medium text-amber-800 mb-3 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Требует проверки ({summary.needs_attention.length})
          </h3>
          <div className="space-y-2">
            {summary.needs_attention.map((n, i) => (
              <div key={i} className="bg-white rounded-lg p-3 border border-amber-200">
                <p className="text-xs text-gray-500 mb-1">{n.reason}</p>
                <p className="text-sm text-gray-800">«{n.original_text.slice(0, 120)}»</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
