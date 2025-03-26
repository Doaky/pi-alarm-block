# Alarm Block Frontend

A modern, responsive web interface for the Alarm Block project built with React, TypeScript, and Tailwind CSS.

## Features

- **Modern UI/UX**:
  - Clean, responsive design using Tailwind CSS
  - Real-time status updates
  - Loading states and animations
  - Toast notifications for user actions
  - Form validation with immediate feedback

- **Core Functionality**:
  - Dual alarm schedule management
  - White noise control
  - Schedule type selection
  - Time input with validation
  - Day selection with visual feedback
  - Sound control for alarms and white noise

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Toastify

## Project Structure

```
src/
├── components/     # React components
├── types/         # TypeScript type definitions
├── api/           # API integration
├── utils/         # Helper functions
└── styles/        # CSS and Tailwind styles
```

## Development

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Code Quality

- TypeScript for type safety
- ESLint for code linting
- Proper error handling
- Loading state management
- Async/await for API calls
- Component-based architecture
