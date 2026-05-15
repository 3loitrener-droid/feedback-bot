'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Users, List, Settings, LogOut } from 'lucide-react';

const nav = [
  { href: '/team', label: 'Моя команда', icon: Users },
  { href: '/timeline', label: 'Хронология', icon: List },
  { href: '/admin', label: 'Матрица', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/auth';
  };

  const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') ?? '' : '';

  return (
    <aside className="w-56 min-h-screen bg-white border-r border-gray-200 flex flex-col">
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">F</span>
          </div>
          <span className="font-semibold text-gray-900 text-sm">Feedback Assistant</span>
        </div>
      </div>

      <nav className="flex-1 p-3">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium mb-1 transition-colors',
              pathname.startsWith(href)
                ? 'bg-brand-50 text-brand-600'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="p-3 border-t border-gray-100">
        <div className="px-3 py-2 mb-1">
          <p className="text-xs text-gray-500">Аккаунт</p>
          <p className="text-sm font-medium text-gray-800 truncate">{userName}</p>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-100 w-full transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Выйти
        </button>
      </div>
    </aside>
  );
}
