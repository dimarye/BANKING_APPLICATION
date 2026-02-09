# SecureBank Frontend

Modern banking application frontend built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- **Authentication**: Secure login and registration system
- **Dashboard**: Overview of accounts and recent transactions
- **Transfers**: Instant money transfers between accounts
- **History**: Complete transaction history with search and filtering
- **Real-time Updates**: WebSocket integration for live balance updates
- **Responsive Design**: Mobile-first design that works on all devices
- **Type Safety**: Full TypeScript implementation
- **Modern UI**: Clean, professional banking interface

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Forms**: React Hook Form with Zod validation
- **HTTP Client**: Axios with interceptors
- **State Management**: React Context
- **Icons**: Lucide React
- **UI Components**: Custom component library

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Dashboard page
│   ├── transfer/          # Transfer page
│   ├── history/           # Transaction history page
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # Reusable components
│   ├── forms/            # Form components
│   ├── layout/           # Layout components
│   └── ui/               # UI components
├── contexts/             # React contexts
├── lib/                  # Utility functions and API client
└── types/                # TypeScript type definitions
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.local.example .env.local
```

3. Configure your environment variables in `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8001/ws
NEXT_PUBLIC_APP_NAME=SecureBank
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## API Integration

The frontend integrates with the backend API at `http://localhost:8001/api/v1`. Make sure the backend server is running for full functionality.

### API Endpoints Used

- `POST /auth/login/` - User authentication
- `POST /auth/register/` - User registration
- `GET /auth/user/` - Get current user
- `GET /accounts/` - Get user accounts
- `GET /transactions/` - Get transaction history
- `POST /transactions/transfer/` - Create transfer

## Authentication Flow

1. User logs in via `/auth/login`
2. JWT tokens are stored in localStorage
3. API client automatically includes tokens in requests
4. Token refresh handled automatically
5. User is redirected to dashboard on successful login

## Key Features Implementation

### Real-time Updates

The application uses WebSocket connections for real-time balance updates and transaction notifications. The WebSocket client automatically handles reconnections and message parsing.

### Form Validation

All forms use React Hook Form with Zod schemas for type-safe validation:
- Login form validation
- Registration form validation  
- Transfer form validation with balance checks

### Error Handling

- API errors are caught and displayed to users
- Network errors handled gracefully
- Loading states for all async operations
- Empty states for no data scenarios

### Responsive Design

- Mobile-first approach
- Tailwind CSS breakpoints
- Touch-friendly interface
- Optimized for all screen sizes

## Deployment

### Environment Variables

Make sure to set these environment variables in production:

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api/v1
NEXT_PUBLIC_WS_URL=wss://your-api-domain.com/ws
NEXT_PUBLIC_APP_NAME=SecureBank
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Build and Deploy

```bash
npm run build
npm run start
```

The application can be deployed on any platform that supports Next.js:
- Vercel (recommended)
- Netlify
- AWS Amplify
- Railway
- DigitalOcean App Platform

## Security Considerations

- JWT tokens stored in localStorage (consider httpOnly cookies for production)
- API requests use HTTPS in production
- Input validation on all forms
- XSS protection through Next.js built-in security
- CSRF protection through same-site cookie attributes

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new code
3. Add proper error handling
4. Test on mobile devices
5. Update documentation as needed

## License

This project is part of the SecureBank banking application.
