FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies (from admin subdir)
COPY admin/package.json admin/package-lock.json ./
RUN npm ci --omit=dev

# Build the app
COPY admin/ .
RUN npm run build

# Production image
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static

EXPOSE 3000

ENV PORT=3000
CMD ["node", "server.js"]
