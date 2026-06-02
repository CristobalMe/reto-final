FROM node:22-alpine AS deps
WORKDIR /app
# Make the local package available at the path npm ci expects:
# lock file resolves "../../ab-testing-package" → /ab-testing-package from WORKDIR /app
COPY ab-testing-package/package.json /ab-testing-package/package.json
COPY ab-testing-package/dist/ /ab-testing-package/dist/
COPY app/frontend/package.json app/frontend/package-lock.json ./
RUN npm ci --install-links

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /ab-testing-package /ab-testing-package
COPY --from=deps /app/node_modules ./node_modules
COPY app/frontend/ .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
