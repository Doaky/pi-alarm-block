/**
 * Display a full-screen shutdown message
 * This replaces the entire page content with a shutdown message
 */
export const displayShutdownScreen = (): void => {
  document.body.innerHTML = '<div style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #1a202c; color: white; font-family: sans-serif;"><h1>System is shutting down...</h1></div>';
};
