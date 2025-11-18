# X Content RAG System - Modern Frontend

A modern, professional React/Next.js frontend for the X Content RAG System with a comprehensive design system, smooth animations, and intuitive UI.

## Features

- **Modern Design System**: Custom Tailwind configuration with fluid typography, semantic colors, and dark mode support
- **Component Library**: Built with Radix UI primitives for accessibility and Shadcn/ui patterns
- **Smooth Animations**: Framer Motion for page transitions and micro-interactions
- **Form Validation**: React Hook Form with Zod schemas for type-safe validation
- **Data Visualization**: Recharts for analytics and performance metrics
- **Responsive Layout**: Mobile-first design with adaptive navigation
- **Type Safety**: Full TypeScript support throughout

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI Components**: Radix UI + Custom component library
- **Styling**: Tailwind CSS with custom design tokens
- **Animations**: Framer Motion
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts
- **State Management**: Zustand
- **Icons**: Lucide React
- **Theme**: next-themes for dark/light mode

## Quick Start

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
npm start
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Dashboard home page
│   ├── analytics/         # Analytics page
│   ├── queue/             # Queue management page
│   ├── generate/          # Content generation page
│   └── globals.css        # Global styles and design tokens
├── components/
│   ├── ui/               # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── badge.tsx
│   │   └── ...
│   ├── layout/           # Layout components
│   │   ├── header.tsx
│   │   ├── sidebar.tsx
│   │   └── main-layout.tsx
│   └── theme-provider.tsx
├── hooks/                # Custom React hooks
│   └── use-toast.ts
├── lib/                  # Utility functions
│   └── utils.ts
├── public/              # Static assets
└── config files
```

## Design System

### Colors

The design system includes semantic color palettes with dark mode support:

- **Primary**: Blue shades for main actions and branding
- **Secondary**: Neutral grays for UI elements
- **Semantic**: Success (green), Warning (orange), Error (red), Info (blue)
- **Twitter/X Brand**: Official colors for consistency

### Typography

Fluid typography using CSS `clamp()` for responsive text sizing:

- Scales from mobile (base) to desktop (max) sizes
- Consistent line heights for readability
- Font weights: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)

### Spacing

Consistent spacing system based on rem units:

- 4px base unit (0.25rem)
- Standard scale: 8px, 12px, 16px, 24px, 32px, 48px, 64px
- Custom utilities for safe areas on mobile

### Components

All components follow these principles:

- **Accessible**: Built with Radix UI primitives
- **Composable**: Flexible and reusable
- **Themeable**: Dark mode support throughout
- **Type-safe**: Full TypeScript support
- **Consistent**: Shared design tokens

## Key Pages

### Dashboard (`/`)
- Overview statistics and metrics
- Recent activity feed
- Top performing tweets
- Quick action buttons

### Analytics (`/analytics`)
- Performance insights and recommendations
- Top hashtags analysis
- Content pattern analysis
- AI-powered suggestions

### Queue (`/queue`)
- Scheduled tweets management
- ML-powered optimization
- Predicted engagement scores
- Edit and reschedule functionality

### Generate (`/generate`)
- AI-powered content generation
- Form validation with React Hook Form + Zod
- Real-time tweet scoring
- Copy and queue actions

## API Integration

The frontend proxies API requests to the FastAPI backend:

```javascript
// Configured in next.config.js
{
  source: '/api/:path*',
  destination: 'http://localhost:8000/:path*'
}
```

All API calls should use the `/api` prefix:

```typescript
const response = await fetch('/api/generate/tweet-ideas', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ topic, num_ideas: 5 })
})
```

## Dark Mode

Dark mode is handled by `next-themes`:

```tsx
import { useTheme } from 'next-themes'

const { theme, setTheme } = useTheme()
setTheme(theme === 'dark' ? 'light' : 'dark')
```

Theme toggle is available in the header on all pages.

## Animations

Animations are implemented using Framer Motion:

- Page transitions
- Card hover effects
- Loading states
- Toast notifications

Example:

```tsx
import { motion } from 'framer-motion'

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  {children}
</motion.div>
```

## Form Validation

Forms use React Hook Form with Zod schemas:

```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

const schema = z.object({
  topic: z.string().min(3).max(100),
  numIdeas: z.number().min(1).max(10),
})

const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { topic: '', numIdeas: 5 }
})
```

## Utilities

Helper functions in `lib/utils.ts`:

- `cn()`: Merge Tailwind classes
- `formatNumber()`: Format numbers with K/M/B abbreviations
- `formatPercentage()`: Format decimal as percentage
- `formatRelativeTime()`: Relative time strings (e.g., "2 hours ago")
- `truncate()`: Truncate text with ellipsis
- `debounce()`: Debounce function calls

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Android)

## Performance

- **Code Splitting**: Automatic with Next.js
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Next.js font loading
- **Bundle Size**: Optimized with tree-shaking

## Contributing

When adding new components:

1. Follow the existing component patterns
2. Use TypeScript for type safety
3. Support dark mode
4. Include accessibility features
5. Add proper error handling

## Future Enhancements

- [ ] Real-time updates with WebSockets
- [ ] Advanced data visualization components
- [ ] Onboarding flow for new users
- [ ] Settings page for customization
- [ ] Mobile app (React Native)
- [ ] PWA support with offline mode

## License

Part of the X Content RAG System project.
