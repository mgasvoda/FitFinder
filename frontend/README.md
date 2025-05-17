# FitFinder Frontend

This is the frontend for the FitFinder application, built with Next.js and packaged for mobile using Capacitor.

## Prerequisites

- Node.js 18+ and npm 9+
- Android Studio (for Android development)
- Java Development Kit (JDK) 17+

## Getting Started

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   - Copy `.env.local.example` to `.env.local`
   - Update the environment variables as needed

### Development

To run the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Building for Production

### Web Build

To create a production build for the web:

```bash
npm run build
```

This will create an optimized production build in the `.next` directory and export static files to the `out` directory.

### Android Build

1. Ensure you have Android Studio installed
2. Build the web assets:
   ```bash
   npm run build
   ```
3. Sync with Android project:
   ```bash
   npx cap sync android
   ```
4. Open in Android Studio:
   ```bash
   npx cap open android
   ```
5. In Android Studio:
   - Wait for the project to sync
   - Select an emulator or connect a device
   - Click the "Run" button (green play icon) to launch the app

## Environment Variables

Create a `.env.local` file in the project root with the following variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

- `/app` - Next.js app router pages and layouts
- `/components` - Reusable React components
- `/lib` - Utility functions and API clients
- `/public` - Static assets
- `/styles` - Global styles and theme

## Mobile App Configuration

### Android

The Android app is configured in `capacitor.config.ts`. Key settings:

- `appId`: `dev.local.fitfinder`
- `appName`: `FitFinder`
- `webDir`: `out` (where the static export is generated)

### Updating the App

1. Make your changes to the web app
2. Build the web app:
   ```bash
   npm run build
   ```
3. Sync with the native project:
   ```bash
   npx cap sync android
   ```
4. Rebuild and run the Android app from Android Studio

## Troubleshooting

### Android Build Issues

- **Gradle sync failed**: Try `npx cap sync android` from the command line
- **Missing SDK**: Ensure you have the required Android SDK versions installed in Android Studio
- **Build errors**: Clean and rebuild the project in Android Studio

### Web Build Issues

- **Type errors**: Run `npm run type-check` to identify TypeScript issues
- **Lint errors**: Run `npm run lint` to identify and fix linting issues

## Deployment

### Web Deployment

Deploy the contents of the `out` directory to any static hosting service (Vercel, Netlify, GitHub Pages, etc.).

### Android Deployment

1. Generate a release build in Android Studio:
   - Build > Generate Signed Bundle / APK
   - Follow the wizard to create a signed APK or App Bundle
2. Upload to the Google Play Store

## Dependencies

- Next.js 14+ (React framework)
- Capacitor 7+ (Mobile runtime)
- Tailwind CSS (Styling)
- React Query (Data fetching)
- Shadcn UI (UI components)

## License

This project is licensed under the MIT License.
