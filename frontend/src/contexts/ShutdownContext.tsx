import React, { createContext, useContext, useState } from 'react';

interface ShutdownContextType {
  isShuttingDown: boolean;
  setShuttingDown: (isShuttingDown: boolean) => void;
}

const ShutdownContext = createContext<ShutdownContextType | undefined>(undefined);

export const ShutdownProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isShuttingDown, setShuttingDown] = useState(false);

  return (
    <ShutdownContext.Provider value={{ isShuttingDown, setShuttingDown }}>
      {children}
      {isShuttingDown && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-8 rounded-lg shadow-lg text-center">
            <h1 className="text-3xl font-bold text-white mb-4">System is shutting down</h1>
            <p className="text-gray-300">Please wait while the system shuts down...</p>
          </div>
        </div>
      )}
    </ShutdownContext.Provider>
  );
};

export const useShutdown = (): ShutdownContextType => {
  const context = useContext(ShutdownContext);
  if (context === undefined) {
    throw new Error('useShutdown must be used within a ShutdownProvider');
  }
  return context;
};
