# SmartAttend — Vercel Frontend Deployment Guide

## 1. Overview

The SmartAttend frontend is built with **Next.js 15.3.3 (App Router)** and deploys natively to Vercel's global Edge network.

---

## 2. Importing Repository to Vercel

1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New... $\to$ Project**.
3. Select your GitHub repository: `Developbyravi/Attendance-system`.
4. Configure Project Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `./` (Default root contains `package.json` and `src/`)
   - **Build Command**: `next build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

---

## 3. Environment Variables Configuration

In Vercel Project Settings $\to$ **Environment Variables**, add the following:

| Variable Name | Environment | Value / Description | Required? |
| :--- | :---: | :--- | :---: |
| `NEXT_PUBLIC_API_URL` | Production & Preview | `https://api.yourdomain.com/api` (URL of your AWS EC2 FastAPI backend) | **YES** |
| `NEXT_PUBLIC_SUPABASE_URL` | Production & Preview | `https://ynpvbxtrfbcwficiwphg.supabase.co` | Optional |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Production & Preview | Client publishable key | Optional |

> [!CAUTION]
> **NEVER expose `SUPABASE_SERVICE_ROLE_KEY` or `SECRET_KEY` in Vercel environment variables prefixed with `NEXT_PUBLIC_`.**

---

## 4. Custom Domain & DNS Settings

1. In Vercel Project Settings $\to$ **Domains**, add your domain (e.g. `smartattend.yourdomain.com` or `attendance.yourdomain.com`).
2. Add the generated `CNAME` or `A` record to your DNS registrar (Cloudflare, GoDaddy, Route 53).
3. Vercel will automatically provision a free SSL/TLS certificate.
