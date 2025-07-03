# Mairie Radar Frontend

React-based chat interface for the Mairie Radar budget anomaly detection system, built with [@llamaindex/chat-ui](https://github.com/run-llama/chat-ui).

## Features

- 💬 **Interactive Chat Interface**: Chat with AI agents about budget anomalies
- 📊 **Real-time Responses**: Connect to backend agents via WebSocket
- 📄 **Document Upload**: Upload budget documents for analysis
- 🔍 **Search History**: Browse previous queries and results
- 📈 **Visualization**: Charts and graphs for budget data
- 🎨 **Modern UI**: Beautiful, responsive design with Tailwind CSS

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm 8+ or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### Configuration

Create a `.env.local` file:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Enable debug mode
NEXT_PUBLIC_DEBUG=true
```

## Project Structure

```
frontend/
├── app/                 # Next.js 14 app router
│   ├── page.tsx        # Main chat page
│   ├── layout.tsx      # Root layout
│   └── globals.css     # Global styles
├── components/         # React components
│   ├── chat/          # Chat-related components
│   ├── ui/            # Reusable UI components
│   └── dashboard/     # Dashboard components
├── lib/               # Utilities and configurations
├── hooks/             # Custom React hooks
└── types/             # TypeScript type definitions
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Integration with Backend

The frontend communicates with the Python backend via:

- **REST API**: For queries and configuration
- **WebSocket**: For real-time agent responses
- **File Upload**: For budget document processing

## Customization

The chat interface can be customized by:

1. **Styling**: Modify Tailwind CSS classes
2. **Components**: Extend @llamaindex/chat-ui components
3. **Themes**: Add custom color schemes
4. **Widgets**: Create custom message widgets

## Development

```bash
# Install dependencies
npm install

# Start backend (in another terminal)
cd ../
uv run backend-api

# Start frontend
npm run dev
```

Visit `http://localhost:3000` to see the chat interface.

## Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

For deployment to Vercel, Netlify, or other platforms, see the [Next.js deployment documentation](https://nextjs.org/docs/deployment). 