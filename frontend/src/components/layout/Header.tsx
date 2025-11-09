'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, LayoutDashboard, History, User, Sparkles } from 'lucide-react';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';

export const Header = () => {
  const pathname = usePathname();

  const navigation = [
    { name: 'New Scan', href: '/', icon: Sparkles },
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'History', href: '/history', icon: History },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0A0A0A]/80 backdrop-blur-xl border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-[72px]">
          
          {/* Logo - Enhanced */}
          <Link 
            href="/" 
            className="flex items-center gap-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-blue-600/30">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Agent-P
            </span>
          </Link>

          {/* Navigation - Desktop */}
          <nav className="hidden md:flex items-center gap-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-600/30'
                      : 'text-[#A3A3A3] hover:text-white hover:bg-[#1A1A1A]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Side Actions */}
          <div className="flex items-center gap-3">
            <NotificationCenter />
            
            <button className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#1A1A1A] border border-[#2A2A2A] hover:bg-[#222222] hover:border-[#3B82F6]/50 transition-all duration-200">
              <User className="w-4 h-4 text-[#A3A3A3]" />
              <span className="text-sm font-medium text-[#F5F5F5] hidden sm:inline">Admin</span>
            </button>
          </div>
        </div>
      </div>

    </header>
  );
};
