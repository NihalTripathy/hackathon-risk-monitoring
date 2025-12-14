# Quick Setup Guide

## Step 1: Install Dependencies

```bash
cd schedule-risk-frontend
npm install
```

## Step 2: Configure Environment

Create a `.env.local` file in the `schedule-risk-frontend` directory with:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

## Step 3: Install Tailwind CSS (if not already done)

The Tailwind configuration is already set up, but if you need to reinstall:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## Step 4: Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Step 5: Verify Backend is Running

Make sure the backend API is running on `http://localhost:8000` before using the frontend.

## Troubleshooting

### Port Already in Use
If port 3000 is in use, Next.js will automatically use the next available port.

### API Connection Errors
- Verify the backend is running: `http://localhost:8000`
- Check `.env.local` has the correct API base URL
- Ensure CORS is configured on the backend if needed

### Tailwind Styles Not Loading
- Ensure `globals.css` has the Tailwind directives
- Check `tailwind.config.js` includes the correct content paths
- Restart the dev server after configuration changes

