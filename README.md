# Remi 🐚 – AI ADHD Companion

**Remi** is a simple, supportive productivity app for ADHD. It combines tasks, routines, and gentle reminders with an **AI buddy** that helps break down work and nudge you toward the next step.

## Features (MVP)
- Tasks & routines (lightweight, fast)
- Context-aware reminders (not spammy)
- Streaks & progress
- AI help: break tasks → next action
- Web first; mobile with Expo later

## Tech Stack
- **Web:** Next.js, Tailwind, shadcn/ui, TanStack Query
- **Mobile (planned):** Expo React Native
- **Backend:** Supabase (Postgres + Auth) + Prisma
- **AI:** model router (Claude/OpenAI), pgvector
- **Infra:** Vercel (web), Upstash (cache/jobs)
- **Analytics/Errors:** PostHog, Sentry

## Roadmap (short)
- [x] Repo + initial scaffold
- [ ] Auth (email + Google)
- [ ] Tasks CRUD + basic reminders
- [ ] Streaks & basic analytics
- [ ] AI v0: “break task” → steps
- [ ] Beta mobile app (Expo)

## Status
Early development. Expect rapid changes.

## Contributing
Issues/PRs welcome. Keep changes small and include a brief note or screenshot.

## License
MIT
