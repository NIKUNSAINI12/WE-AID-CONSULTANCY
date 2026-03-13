# 🚀 Deploying to Vercel

Your We Aid Consultancy project is now ready for Vercel deployment! 

### 1. Preparation
Make sure you have the [Vercel CLI](https://vercel.com/download) installed or have connected your GitHub repository to Vercel.

### 2. Environment Variables (CRITICAL)
Vercel does **not** read your `.env` file. You MUST add these variables in the **Vercel Dashboard** (Settings > Environment Variables):
- `SUPABASE_URL`: Your Supabase Project URL
- `SUPABASE_KEY`: Your Supabase Service Role or Anon Key
- `SESSION_SECRET`: A long random string for securing admin logins

### 3. Deploy Command
Run this in your terminal:
```bash
vercel deploy --prod
```

### 4. Database Setup
Since you added several features today (Leads tracking, Signup syncing), make sure you have run the following SQL commands in your **Supabase SQL Editor**:

```sql
-- 1. Support for Blog Edits/Dates
ALTER TABLE posts ADD COLUMN IF NOT EXISTS display_date TEXT;

-- 2. Lead Management Tracking
ALTER TABLE registrations ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'uncontacted';
ALTER TABLE registrations ADD COLUMN IF NOT EXISTS response TEXT;
ALTER TABLE registrations ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();

-- 3. Unified User Tracking
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_contacted TEXT DEFAULT 'no';
ALTER TABLE users ADD COLUMN IF NOT EXISTS response TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS profession TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
```

---
**Note:** The static files (`stitch_assets`) and templates are automatically handled by the current configuration.
