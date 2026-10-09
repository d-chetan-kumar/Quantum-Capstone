# Frontend Architecture

## Tech Stack
- React + Vite
- TypeScript
- Tailwind CSS (for styling)
- Framer Motion (for animations and dynamic UI)
- Recharts (for data visualization)
- Lucide React (for icons)

## Theming (Light / Dark Mode)
- Deep integration of Tailwind's `dark:` classes.
- Theme preference persisted in localStorage.
- **Light Theme**: Clean fintech white/slate, professional, strong readability.
- **Dark Theme**: Premium dark fintech appearance, deep charcoal/slate, clear contrast, no excessive neon.
- Strict avoidance of generic templates, cyberpunk aesthetics, or excessive glassmorphism.

## Information Architecture & Navigation
1. **Dashboard**: High-level overview, key metrics.
2. **Live Payments**: Primary showcase page. WebSocket driven.
3. **Transactions**: Historical ledger and search.
4. **Alerts**: Queue for REVIEW and ALERT flagged transactions.
5. **Analytics**: Aggregate charts and trends.
6. **AI Models**: Performance metrics of classical/hybrid models.
7. **VQC Lab**: Dedicated view for the quantum circuit and metrics.
8. **Methodology**: Research-oriented explanation of the pipeline.
9. **Simulator / Controls**: Manage the real-time simulation engine.
10. **Settings**: Theme and application preferences.

## State Management
- React Context for Theme and WebSocket connections.
- Local component state for UI interactions.
- Avoid overly complex global state (Redux) unless necessary; prefer custom hooks for API/WS data fetching.
