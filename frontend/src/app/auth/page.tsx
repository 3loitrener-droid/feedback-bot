'use client';
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { requestMagicLink, verifyMagicLink } from '@/lib/api';

export default function AuthPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [magicUrl, setMagicUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      verifyMagicLink(token)
        .then((data) => {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('user_name', data.full_name);
          localStorage.setItem('user_role', data.role);
          router.replace('/team');
        })
        .catch(() => setError('Ссылка недействительна или истекла.'));
    }
  }, [searchParams, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const resp = await requestMagicLink(email);
      setSent(true);
      if (resp.magic_url) {
        setMagicUrl(resp.magic_url);
      }
    } catch {
      setError('Email не найден в системе. Обратись к администратору.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-brand-500 rounded-xl mb-4">
            <span className="text-white text-xl font-bold">F</span>
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Feedback Assistant</h1>
          <p className="text-gray-500 mt-1 text-sm">Performance feedback management</p>
        </div>

        <div className="card p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {sent ? (
            <div className="text-center">
              <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-lg font-medium text-gray-900 mb-2">Ссылка создана</h2>

              {magicUrl ? (
                <div className="mt-4">
                  <p className="text-sm text-gray-500 mb-3">
                    Нажми кнопку ниже для входа:
                  </p>
                  <a
                    href={magicUrl}
                    className="block w-full btn-primary py-2.5 text-center"
                  >
                    Войти в систему →
                  </a>
                  <p className="text-xs text-gray-400 mt-3">
                    В продакшене ссылка придёт на почту. Действительна 30 мин.
                  </p>
                </div>
              ) : (
                <p className="text-gray-500 text-sm">
                  Проверь email <strong>{email}</strong> — там ссылка для входа.
                </p>
              )}

              <button
                onClick={() => { setSent(false); setMagicUrl(''); }}
                className="mt-4 text-brand-500 text-sm hover:underline"
              >
                Войти с другим email
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <h2 className="text-lg font-medium text-gray-900 mb-1">Войти</h2>
              <p className="text-gray-500 text-sm mb-6">
                Введи корпоративный email — получишь ссылку для входа
              </p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  placeholder="ivan@company.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-2.5"
              >
                {loading ? 'Создаём ссылку...' : 'Получить ссылку для входа'}
              </button>

              <div className="mt-6 pt-6 border-t border-gray-100">
                <p className="text-xs text-gray-400 text-center mb-3">Демо-аккаунты</p>
                <div className="space-y-1">
                  {[
                    { email: 'alexey@company.com', role: 'Менеджер' },
                    { email: 'maria@company.com', role: 'HRBP' },
                    { email: 'dmitry@company.com', role: 'Админ' },
                  ].map(u => (
                    <button
                      key={u.email}
                      type="button"
                      onClick={() => setEmail(u.email)}
                      className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 flex justify-between items-center text-sm"
                    >
                      <span className="text-gray-700">{u.email}</span>
                      <span className="text-xs text-gray-400">{u.role}</span>
                    </button>
                  ))}
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
