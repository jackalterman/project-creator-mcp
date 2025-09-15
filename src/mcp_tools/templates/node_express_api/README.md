# Express TypeScript API

A RESTful API server built with Express.js and TypeScript.

## Features

- Express.js server with TypeScript
- CORS and Helmet security middleware
- Environment variable configuration
- Development with hot reload
- Production build process

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   ```
   ```bash
   npm start
   ```

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check

## Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build TypeScript to JavaScript
- `npm start` - Start production server
- `npm test` - Run tests
