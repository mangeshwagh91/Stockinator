# Stockinator Frontend

React + TypeScript + Vite frontend for the Stockinator automated trading system.

## Features

- 📊 Real-time market data visualization
- 📈 Technical indicator charts
- 🎯 ML success score display
- 💰 Position and P&L tracking
- 📰 News feed with sentiment analysis
- ⚙️ Trading parameters control
- 📉 Trade history and analytics
- 🔄 WebSocket real-time updates

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **shadcn/ui** component library
- **React Router** for navigation
- **Recharts** for data visualization
- **Lucide React** for icons

## Getting Started

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Lint code
npm run lint
```

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   └── ui/          # shadcn/ui components
│   ├── pages/           # Page components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utility functions
│   ├── data/            # Mock data
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
├── tailwind.config.ts   # Tailwind configuration
└── package.json         # Dependencies
```

## Available Scripts

- `npm run dev` - Start development server (port 5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run Vitest tests
- `npm run lint` - Lint with ESLint

## API Integration

The frontend connects to the FastAPI backend:

- **REST API**: `/api/v1/*` endpoints
- **WebSocket**: `/api/v1/ws/live` for real-time updates

API calls are proxied through Vite dev server to avoid CORS issues.

## Components

### Pages
- **Dashboard** - Main trading dashboard
- **Positions** - Active positions and P&L
- **Indicators** - Technical indicators
- **News** - News feed with sentiment
- **Risk** - Risk metrics and limits
- **Settings** - System configuration
- **Trending** - Market trends

### Key Components
- **Layout** - Main app layout with sidebar
- **Header** - Navigation header
- **AppSidebar** - Side navigation
- **ChartPanel** - Price charts
- **IndicatorPanel** - Indicator displays
- **PositionsPanel** - Position list
- **NewsFeed** - News articles
- **RiskPanel** - Risk metrics

## Styling

Using **Tailwind CSS** with **shadcn/ui** components:

- Dark mode support
- Responsive design
- Consistent design system
- CSS variables for theming

## WebSocket Integration

Real-time updates via WebSocket:

```typescript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/live');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle score updates, trade executions, etc.
};
```

## Building for Production

```bash
npm run build
```

Output goes to `dist/` directory. Serve with any static file server or include in Docker container.

## Docker

The frontend is Dockerized with the backend. See root `docker-compose.yml`.

## Contributing

1. Follow TypeScript best practices
2. Use existing component patterns
3. Add tests for new features
4. Update documentation

## License

MIT
