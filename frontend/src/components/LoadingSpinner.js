import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-blue-900 flex items-center justify-center">
      <div className="text-center">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-blue-200 dark:border-blue-800 rounded-full animate-spin border-t-blue-600 dark:border-t-blue-400"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xs">S</span>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Initializing SystemIX AI
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Setting up your AI-powered business platform...
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;