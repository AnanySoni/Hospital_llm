# Hospital AI Assistant - Frontend

A modern React + TypeScript chatbot interface for medical consultations, built with a ChatGPT-like user experience.

## Features

- **Modern Chat Interface**: Clean, responsive design similar to ChatGPT
- **TypeScript Support**: Full type safety and better developer experience
- **Tailwind CSS**: Modern styling with custom chat themes
- **Real-time Messaging**: Smooth message animations and loading states
- **Mobile Responsive**: Works seamlessly on all device sizes

## Tech Stack

- React 18
- TypeScript
- Tailwind CSS
- Font Awesome (for icons)

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn package manager

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open your browser and visit `http://localhost:3000`

### Building for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/           # React components
│   ├── ChatContainer.tsx # Main chat container
│   ├── MessageBubble.tsx # Individual message component
│   ├── ChatInput.tsx     # Message input component
│   └── WelcomeScreen.tsx # Welcome/landing screen
├── types/               # TypeScript type definitions
│   └── index.ts         # Message and API types
├── App.tsx              # Main application component
├── index.tsx            # Application entry point
└── index.css            # Global styles and Tailwind imports
```

## API Integration

The frontend connects to your existing backend API at `http://localhost:8000`. Make sure your backend server is running for full functionality.

### Endpoints Used

- `POST /recommend-doctors` - Get doctor recommendations based on symptoms

## Customization

### Styling

The chat interface uses custom Tailwind colors defined in `tailwind.config.js`:

- `chat-bg`: Main background color
- `chat-sidebar`: Sidebar background
- `chat-input`: Input field background
- `chat-border`: Border colors
- `chat-user`: User message background
- `chat-assistant`: Assistant message background

### Adding Features

This is currently just the chat interface. Future features can be added as separate components:

1. Doctor recommendations display
2. Appointment booking interface
3. User profile management
4. Medical history tracking

## Next Steps

1. **Doctor Recommendations**: Add UI to display recommended doctors
2. **Appointment Booking**: Create appointment scheduling interface
3. **User Authentication**: Add login/signup functionality
4. **Medical Records**: Implement patient history tracking
5. **Notifications**: Add real-time appointment reminders

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (not recommended) 