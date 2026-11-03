# SmartAttend — Emergency Rollback & Recovery Guide

## 1. Backend Emergency Rollback (AWS EC2 / Docker)

If a newly deployed container or release exhibits runtime errors:

```bash
# 1. Connect to EC2
ssh -i "your-key.pem" ubuntu@YOUR_EC2_IP
cd Attendance-system

# 2. View previous git commits
git log -n 5 --oneline

# 3. Roll back to previous verified commit
git checkout <PREVIOUS_COMMIT_HASH>

# 4. Rebuild and restart containers
cd deployment
docker compose down
docker compose up -d --build

# 5. Verify system health
curl -f http://localhost:8002/api/health
```

---

## 2. Frontend Rollback (Vercel)

1. Open [Vercel Dashboard](https://vercel.com).
2. Select your `Attendance-system` project.
3. Navigate to **Deployments**.
4. Identify the last known healthy deployment.
5. Click the three dots ($\dots$) and select **Instant Rollback**.
6. Traffic will instantly route to the previous stable build within seconds.

---

## 3. Database Recovery

If data corruption occurs during manual testing:
```bash
# SQLite Local Recovery
cp backend2/smartattend.db.backup backend2/smartattend.db

# PostgreSQL Supabase Recovery
# Use Supabase Point-in-Time Recovery (PITR) in Database -> Backups
```
