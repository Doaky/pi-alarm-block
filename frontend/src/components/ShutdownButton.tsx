import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { shutdownSystem } from '../services/api';

export const ShutdownButton: React.FC = () => {
    const [isConfirming, setIsConfirming] = useState(false);
    const [isShuttingDown, setIsShuttingDown] = useState(false);

    const handleShutdownClick = () => {
        if (!isConfirming) {
            setIsConfirming(true);
            // Auto-reset confirmation state after 5 seconds
            setTimeout(() => setIsConfirming(false), 5000);
            return;
        }

        // User confirmed, proceed with shutdown
        setIsShuttingDown(true);
        toast.info('Shutting down system...');
        
        shutdownSystem()
            .then(() => {
                toast.success('Shutdown initiated successfully');
                // Show a message that the app is shutting down
                setTimeout(() => {
                    document.body.innerHTML = '<div style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #1a202c; color: white; font-family: sans-serif;"><h1>System is shutting down...</h1></div>';
                }, 1000);
            })
            .catch(() => {
                toast.error('Failed to shutdown system');
                setIsShuttingDown(false);
                setIsConfirming(false);
            });
    };

    return (
        <button
            onClick={handleShutdownClick}
            disabled={isShuttingDown}
            className={`fixed top-4 right-4 rounded-full p-2 flex items-center justify-center transition-colors ${
                isConfirming 
                    ? 'bg-red-600 hover:bg-red-700' 
                    : 'bg-gray-700 hover:bg-gray-600'
            } ${isShuttingDown ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={isConfirming ? 'Click again to confirm shutdown' : 'Shutdown system'}
        >
            {/* Power icon */}
            <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-6 w-6" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
            >
                <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M13 10V3L4 14h7v7l9-11h-7z" 
                />
            </svg>
            {isConfirming && (
                <span className="ml-2 text-sm font-medium">Confirm</span>
            )}
        </button>
    );
};
