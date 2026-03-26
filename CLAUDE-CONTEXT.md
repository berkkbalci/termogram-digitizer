# Termogram Digitizer — Project Context & Decisions

## What This Project Is

A citizen science platform to digitize historical meteorological records (1911-2005) from Kandilli Meteorology Laboratory. Volunteers trace temperature curves on scanned thermogram images using their mouse. Multiple volunteers trace the same image, and cross-validation produces reliable digitized data. Think Galaxy Zoo but for weather records.

**Why human computing?** Traditional OCR and computer vision fail on these records because of faded ink, torn paper, overlapping grid lines, and curves that blend with the background. The human eye handles these visual ambiguities much better.

## Current Architecture

- **Frontend:** Single `index.html` file — vanilla HTML/CSS/JS, no framework, no build tools
- **Admin Panel:** `admin.html` — separate page for cross-validation analysis and leaderboard
- **Seed Tool:** `scripts/seed-firestore.html` — one-time tool to upload image metadata to Firestore
- **Backend:** Firebase (Firestore + Anonymous Auth). No server-side code.
- **Hosting:** GitHub Pages (free). Static files served from the repo.
- **Images:** Currently stored in `images/` folder in the GitHub repo, served via GitHub Pages

## Current Firestore Schema

### `termograms` collection
Each document = one meteorological record image:
```
{
  id: "1977_MAYIS-03",
  imageFile: "images/1977_MAYIS-03.png",    // relative path to image
  label: "1977 Mayıs 03",
  dataType: "termogram",                     // NEW FIELD TO ADD
  startDate: "1977-05-03T00:00:00",
  endDate: "1977-05-10T00:00:00",
  tempMin: -10, tempMax: 40,
  gridLeft: 120, gridRight: 3500,            // pixel coordinates for calibration
  gridTop: 50, gridBottom: 1000,
  traceCount: 0,
  maxTraces: 3,                              // CHANGE TO 5
  status: "available"                        // or "completed"
}
```

### `traces` collection
Each document = one user's tracing of one termogram:
```
{
  termogramId: "1977_MAYIS-03",
  userId: "anonymous-uid",
  userName: "Berk",
  pointCount: 847,
  rawPoints: [{x, y}, ...],                  // pixel coordinates
  calibratedData: [{timestamp, temperature}, ...],
  referencePoints: [{x, y, temperature}, ...], // user-marked known values
  createdAt: serverTimestamp()
}
```

### `users` collection (NEW — TO BE CREATED)
```
{
  userName: "Berk",
  totalXP: 0,
  level: 1,
  tracesCompleted: 0,
  lastActiveDate: "2026-03-26",
  streakDays: 1
}
```

## Firebase Configuration

Project is on **Spark (free) plan**. No credit card. This means:
- Firestore: 50K reads/day, 20K writes/day, 1 GB storage — more than enough
- Auth: Unlimited anonymous sign-ins
- **NO Firebase Storage** (requires Blaze plan upgrade)
- All images are served from GitHub Pages, not Firebase Storage

Firebase config (already in the code):
```javascript
{
  apiKey: "AIzaSyAiIza_wzTlnL6mrtu6pBJwDVQBOjfLlr8",
  authDomain: "termogram-digitizer.firebaseapp.com",
  projectId: "termogram-digitizer",
  storageBucket: "termogram-digitizer.firebasestorage.app",
  messagingSenderId: "818774713299",
  appId: "1:818774713299:web:1dbe686cde9147adc94526"
}
```

## Image Storage Strategy

**Decision: Keep images in GitHub repo.** No Firebase Storage (costs money).

- Images go in `images/` directory, organized by data type:
  ```
  images/
  ├── termogram/
  │   ├── 1977_MAYIS-03.png
  │   └── ...
  ├── barograf/
  │   └── ...
  ├── termohigrograf/
  │   └── ...
  └── aktinograf/
      └── ...
  ```
- Original TIF files are converted to PNG (using Pillow) and resized to max 2500px width
- GitHub repo limit: 5 GB total, 100 MB per file — plenty for thousands of PNGs
- Firestore `imageFile` field stores relative path: `"images/termogram/1977_MAYIS-03.png"`

**IMPORTANT:** When adding new image entries to seed-firestore.html, the imageFile path must match the actual file location in the repo.

## Key Problems We Identified & Decisions Made

### Problem 1: High Variance in Traces
**Current:** Users draw freely — can go backward, skip areas, make random marks. Only 3 traces per image, simple mean average.

**Solution (implement in this order):**
1. **Right-only drawing constraint:** Each new point's x must be >= previous point's x. Prevents backward drawing, loops, and random marks. This is the single highest-impact change.
2. **Y-jump cap:** If consecutive points differ by >30px in y, cap it. Prevents hand-slip spikes.
3. **Median instead of mean:** In `computeAverageCurve`, use median of y values at each x position. Median is resistant to outliers.
4. **Z-score outlier detection:** Flag traces where average z-score > 2.5. Exclude them from the average.
5. **Increase to 5 traces per image:** More data points = more reliable median.
6. **Trimmed mean:** From 5 traces, exclude best and worst by MAE, average remaining 3.
7. **Confidence band:** IQR-based confidence score at each x position.

### Problem 2: Poor Drawing Experience
**Current:** Default browser cursor is hard to see on the termogram. No feedback during drawing.

**Solution:**
1. **Custom crosshair:** Large, visible crosshair drawn on canvas with temperature tooltip. Use two-canvas approach (overlay canvas for crosshair, base canvas for image + trail) to avoid flickering.
2. **Hide default cursor** on canvas during drawing (`cursor: none`).

### Problem 3: No Game Logic
**Current:** User draws and submits. No motivation to return.

**Solution:**
1. **XP system:** 50 base XP per trace + bonuses. Stored in new `users` collection.
2. **Level system:** 10 levels with increasing XP thresholds.
3. **Daily streak:** Track consecutive active days, apply XP multiplier (up to 2x at 10+ days).
4. **Leaderboard:** Top 10 by total XP, shown on main page (collapsible).
5. **Onboarding tutorial:** 3-step overlay for first-time users.

### Problem 4: Only Termogram Data
**Current:** Only thermogram images in the system.

**Solution:**
1. Add `dataType` field to Firestore schema: "termogram", "barograf", "termohigrograf", "aktinograf"
2. Add data type filter in the UI (dropdown in toolbar)
3. Same tracing mechanic works for all these types (they're all continuous curves on paper)
4. Different data types need different calibration parameters but the UI is the same
5. Rüzgar Yönü and Yağış Plüvyogram need completely different UIs — skip for now

## Data Types We Support (and Don't)

### Phase 1 (NOW — same UI, same tracing mechanic):
| Type | Description | UI Mode |
|------|-------------|---------|
| Termogram | Temperature over time | Standard curve trace |
| Barograf | Air pressure over time | Standard curve trace |
| Termohigrograf | Temp + humidity (2 curves) | Standard curve trace (one at a time) |
| Aktinograf | Solar radiation over time | Standard curve trace |

### Phase 2 (LATER — needs different UI):
| Type | Description | Why Different |
|------|-------------|---------------|
| Yağış Plüvyogram | Rainfall (step function) | Staircase shape, not smooth curve |
| Rüzgar Yönü | Wind direction (circular) | Polar coordinate system, different canvas |
| Mereogram | Tide/wave records | Very fine oscillations |
| Mikrobarogram | Micro pressure changes | Very fine oscillations |

## What NOT to Change

- Do NOT add any npm/webpack/build tools. The project is intentionally a single HTML file.
- Do NOT switch to React or any framework.
- Do NOT add Firebase Storage or any paid service.
- Do NOT change the Firebase config or project.
- Do NOT modify the anonymous auth flow — it works fine.
- Do NOT change the Firestore security rules from Claude Code (do this manually in Firebase Console).

## File Structure

```
termogram-digitizer/
├── index.html              → Main app (single file, all HTML/CSS/JS)
├── admin.html              → Admin panel for cross-validation analysis
├── images/                 → Meteorological record images (PNG)
│   ├── termogram/          → TO BE REORGANIZED into subfolders
│   ├── barograf/
│   ├── termohigrograf/
│   └── aktinograf/
├── scripts/
│   └── seed-firestore.html → Firestore seeding tool
└── README.md
```

## Scoring Formula

Current (in admin.html):
```
score = max(0, min(10, 10 * (1 - mae / maxAcceptable)))
maxAcceptable = canvas.height * 0.15
```

New XP formula (for index.html):
```
base_xp = 50
ref_bonus = 20 if referencePoints >= 2 else 0
streak_multiplier = min(1 + streakDays * 0.1, 2.0)
xp_earned = round((base_xp + ref_bonus) * streak_multiplier)
```

## Level Thresholds

| Level | XP Required |
|-------|-------------|
| 1 | 0 |
| 2 | 100 |
| 3 | 300 |
| 4 | 600 |
| 5 | 1000 |
| 6 | 1500 |
| 7 | 2100 |
| 8 | 2800 |
| 9 | 3600 |
| 10 | 5000 |

## Team & Constraints

- 2 people, ~12 hours total
- Using Claude Code for implementation
- Zero budget — everything must be free
- Hackathon project (Boğaziçi Meteoroloji Hackathonu)
- Contributors: Berk Balcı, Burak Ceylan, advisor: Birkan Yılmaz
