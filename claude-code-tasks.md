# Termogram Digitizer — Claude Code Task List

## How to Work with Claude Code

**Golden Rule:** One task at a time. Finish → test → next.

Each task below has:
- **TASK:** What Claude Code should do
- **PROMPT:** Copy-paste this into Claude Code
- **TEST:** How to verify it works before moving on

---

## PHASE 1: Statistics Engine Fix (Hours 1-2)

### Task 1.1 — Replace Mean with Median in Average Curve

**PROMPT:**
```
In index.html AND admin.html, find the `computeAverageCurve` function. 
Currently it computes the MEAN of y values across all traces for each x position. 
Change it to compute the MEDIAN instead. 

The median calculation: sort the y values array, pick the middle value 
(or average of two middle values if even count).

Add a helper function `median(arr)` that both files can use.
Do NOT change function signatures or return types.
```

**TEST:** Open admin.html, select a termogram with 3 traces. The green average curve should still appear but be less affected by outlier traces.

---

### Task 1.2 — Add Z-Score Outlier Detection

**PROMPT:**
```
In admin.html, add outlier detection to the analysis system.

After computing the median-based average curve, for each trace calculate:
1. For each x position, compute the absolute deviation from the average curve
2. Compute the z-score: z = |y_trace - y_median| / stddev
3. If a trace's average z-score > 2.5, flag it as an outlier

In the analysis panel (buildAnalysisPanel function), show a red "⚠️ Outlier" 
badge next to traces that are flagged. 

In the average curve computation, exclude outlier traces and recompute 
the median without them.

On the canvas, draw outlier traces with a dashed line style instead of solid.
```

**TEST:** If you have a deliberately bad trace, it should show the outlier badge and the average curve should ignore it.

---

### Task 1.3 — Add Confidence Band

**PROMPT:**
```
In admin.html, after computing the average curve, also compute a 
confidence band for each x position:

1. Calculate IQR (interquartile range) of y values at each x
2. confidence(x) = max(0, 1 - IQR(x) / threshold) where threshold = canvas.height * 0.1
3. Draw the confidence band as a semi-transparent green fill around 
   the average curve. Width = IQR at each point. 
   Color opacity = confidence value (high confidence = more opaque green,
   low confidence = more transparent/red)

Draw this BEHIND the trace lines and average curve (draw it first).
```

**TEST:** The green band should be narrow where traces agree and wide where they diverge.

---

## PHASE 2: Drawing Experience Fix (Hours 3-4)

### Task 2.1 — Right-Only Drawing Constraint

**PROMPT:**
```
In index.html, modify the drawing logic (continueDrawing function and 
the touch equivalent) so that:

1. Each new point's x coordinate must be >= the previous point's x coordinate
2. If the user moves the mouse left (x decreases), ignore that point entirely
3. Also add: if the y difference between consecutive points is > 30px, 
   cap it at 30px (interpolate to prevent sharp spikes from hand slips)

This should work for both mouse and touch events.
```

**TEST:** Try drawing backwards — nothing should happen. Try making a sharp vertical jump — it should be smoothed.

---

### Task 2.2 — Custom Crosshair Cursor

**PROMPT:**
```
In index.html, replace the default browser crosshair cursor with a 
custom-drawn crosshair on the canvas:

1. Hide the real cursor on canvas: `cursor: none` when drawing mode is active
2. On mousemove (even when not drawing), draw a custom crosshair at the 
   mouse position on the canvas:
   - Vertical line: full canvas height, 1px, rgba(255,255,255,0.3)
   - Horizontal line: full canvas width, 1px, rgba(255,255,255,0.3)  
   - Center circle: 8px radius, 2px stroke, bright red (#FF0000)
   - Center dot: 2px radius, solid red fill
3. Next to the crosshair (offset +20px right, -20px up), show a small 
   tooltip with the current temperature value calculated from the y position 
   using the termogram's calibration data (tempMin, tempMax, gridTop, gridBottom)
   Format: "XX.X°C"
4. The crosshair and tooltip should be drawn on top of everything else
5. Use requestAnimationFrame or a separate overlay approach so the crosshair 
   doesn't interfere with the drawing trail

IMPORTANT: The crosshair must update smoothly without flickering. 
The existing red drawing trail must remain visible while the crosshair moves.
Consider using a two-canvas approach: one for the termogram image + drawing trail,
one transparent overlay canvas on top for the crosshair.
```

**TEST:** Move mouse over canvas — you should see a smooth crosshair with temperature readout. Draw a line — the red trail should persist while crosshair moves.

---

### Task 2.3 — Increase Max Traces to 5

**PROMPT:**
```
In seed-firestore.html, change maxTraces from 3 to 5 for all termograms 
in the TERMOGRAMS array.

In admin.html, update the scoring system to handle 5 traces:
- Use trimmed mean: exclude the best and worst trace (by MAE), 
  average the remaining 3
- Update all UI text that says "3 çizim" to "5 çizim"

In index.html, update the status text where it references the trace count.
```

**TEST:** Check seed-firestore.html — all entries should show maxTraces: 5.

---

## PHASE 3: Game Logic (Hours 5-7)

### Task 3.1 — XP and Level System

**PROMPT:**
```
In index.html, add an XP and leveling system:

1. After a trace is submitted (in submitTrace function), calculate XP:
   - base_xp = 50 (just for completing a trace)
   - If trace has >= 2 reference points: +20 bonus
   - quality_bonus will be added later when cross-validation scores exist
   - Save to Firestore: in the user's trace document, add field "xpEarned"

2. Create a new Firestore collection "users" with documents keyed by userId:
   - Fields: userName, totalXP, level, tracesCompleted, lastActiveDate, streakDays
   - After submitting a trace, update the user document:
     increment totalXP, increment tracesCompleted

3. Level thresholds: 
   Level 1: 0 XP, Level 2: 100, Level 3: 300, Level 4: 600, 
   Level 5: 1000, Level 6: 1500, Level 7: 2100, Level 8: 2800, 
   Level 9: 3600, Level 10: 5000

4. Show in the header bar (next to "Merhaba, username"):
   "⭐ Seviye X • 000 XP"
   
5. After submitting, if user leveled up, show a special popup:
   "🎉 Seviye X'e ulaştınız!" (instead of the generic success popup)

Use Firestore's increment() for atomic updates.
The user document should be created on first login (enterApp function)
with initial values if it doesn't exist yet (use setDoc with merge:true).
```

**TEST:** Submit a trace. Check Firestore — users collection should have your document with XP. Header should show level and XP.

---

### Task 3.2 — Daily Streak System

**PROMPT:**
```
In index.html, add streak tracking to the user system created in Task 3.1:

In the enterApp function, after loading/creating the user document:
1. Get the user's lastActiveDate from Firestore
2. Compare with today's date (just the date, not time)
3. If lastActiveDate is yesterday: increment streakDays by 1
4. If lastActiveDate is today: do nothing (already counted)
5. If lastActiveDate is older than yesterday: reset streakDays to 1
6. Update lastActiveDate to today

Show streak in header: "🔥 X gün" next to the XP display.

In submitTrace, apply streak bonus to XP:
- streak_multiplier = min(1 + streakDays * 0.1, 2.0)
- So 7-day streak = 1.7x XP, capped at 2x
- Show the multiplier in the success popup: "+50 XP (x1.7 streak bonus!)"
```

**TEST:** Submit a trace, check that streak shows "🔥 1 gün". Check Firestore user doc for streakDays field.

---

### Task 3.3 — Leaderboard on Main Page

**PROMPT:**
```
In index.html, add a simple leaderboard visible on the main app screen:

1. Add a collapsible section below the canvas/info-bar area:
   - Header: "🏆 Sıralama" with a toggle button to expand/collapse
   - Default: collapsed (so it doesn't distract from drawing)

2. When expanded, show top 10 users sorted by totalXP:
   - Fetch from "users" collection, orderBy totalXP desc, limit 10
   - Display: rank medal (🥇🥈🥉 for top 3, then "4." etc), 
     userName, level, totalXP, streakDays
   - Highlight the current user's row with a different background color

3. Style it to match the existing dark theme of the app.
   Keep it compact — each row should be one line.

4. Refresh the leaderboard data when a trace is submitted 
   (after the success popup).
```

**TEST:** Open the app, expand leaderboard — your user should appear. Submit a trace — XP should update.

---

## PHASE 4: Multiple Data Types (Hours 8-9)

### Task 4.1 — Add dataType Field to Schema

**PROMPT:**
```
In seed-firestore.html, add a "dataType" field to every termogram 
in the TERMOGRAMS array. Current ones should have dataType: "termogram".

Also add new entries for other data types. Here is the template — 
I will fill in the actual calibration values, but create the structure 
for these new types:

Add 3 barograf entries with dataType: "barograf"
Add 2 termohigrograf entries with dataType: "termohigrograf"  
Add 2 aktinograf entries with dataType: "aktinograf"

For now use placeholder calibration values (copy from existing termograms).
I will update the actual values later.

Set imageFile paths as: "images/barograf/FILENAME.png", 
"images/termohigrograf/FILENAME.png", "images/aktinograf/FILENAME.png"

Set maxTraces: 5 for all new entries.
```

**TEST:** Check seed-firestore.html — new entries should be there with correct dataType fields.

---

### Task 4.2 — Data Type Filter in UI

**PROMPT:**
```
In index.html, add a data type selector to the toolbar:

1. Add a dropdown/button group in the toolbar area with options:
   "Tümü", "Termogram", "Barograf", "Termohigrograf", "Aktinograf"

2. When getNewTermogram() fetches available termograms, also filter 
   by the selected dataType (unless "Tümü" is selected)

3. Show the data type of the current termogram in the info-bar:
   Add an icon+label: 🌡️ Termogram, 📊 Barograf, 💧 Termohigrograf, ☀️ Aktinograf

4. In admin.html, add a data type filter to the termogram select dropdown.
   Group termograms by dataType in the dropdown.

Keep the Firestore query efficient — use the where clause for dataType filtering.
```

**TEST:** Select "Barograf" from dropdown — only barograf termograms should appear. Select "Tümü" — all types should be available.

---

## PHASE 5: Tutorial & Polish (Hours 10-11)

### Task 5.1 — Onboarding Tutorial

**PROMPT:**
```
In index.html, add a 3-step onboarding overlay for first-time users:

1. Check localStorage for "tutorialCompleted" flag
2. If not set, show a modal overlay with 3 steps (next/back buttons):

   Step 1: "🖱️ Mavi Çizgiyi Takip Edin" 
   - Text: "Mouse'un sol tuşuna basılı tutarak termogramdaki mavi sıcaklık 
     eğrisini soldan sağa takip edin."
   - Show an arrow pointing to the canvas area
   
   Step 2: "📌 Referans Noktaları Ekleyin"
   - Text: "Çizimi bitirdikten sonra, görselde sıcaklık değeri 
     görebildiğiniz noktalara tıklayarak referans noktaları ekleyin. 
     En az 2 nokta gerekli."
   
   Step 3: "✅ Gönderin ve Puan Kazanın"  
   - Text: "Gönder butonuna basın! Her çizim size XP kazandırır. 
     Ne kadar doğru çizerseniz o kadar çok puan alırsınız."

3. "Başla!" button on last step closes the overlay and sets the flag.
4. Add a "❓ Nasıl Oynanır?" button in the toolbar that re-shows the tutorial.

Style: dark overlay with centered white card, matching the app's dark theme.
```

**TEST:** Clear localStorage, reload page, login — tutorial should appear. Complete it, reload — should NOT appear again. Click "Nasıl Oynanır?" — should appear again.

---

### Task 5.2 — Visual Polish Pass

**PROMPT:**
```
In index.html, make these visual improvements:

1. When a trace is submitted, show an animated XP counter:
   "+50 XP" that floats up and fades out (CSS animation, 
   positioned near the success popup)

2. Add a progress ring around the current termogram count:
   In the info-bar where it shows "Çizim: 2/5", replace with a small 
   circular progress indicator (SVG circle with stroke-dasharray)

3. Add smooth transitions when switching between draw mode and 
   reference point mode (background color pulse on the toolbar)

4. On the login screen, add a small stats counter:
   "🌡️ Şimdiye kadar X termogram dijitalleştirildi" 
   (fetch count of completed termograms from Firestore)

Keep all animations subtle and performant. Use CSS transitions/animations 
where possible, avoid JavaScript animation loops.
```

**TEST:** Submit a trace — XP animation should play. Check login screen — stats should show.

---

## PHASE 6: Final Testing & Deploy (Hour 12)

### Task 6.1 — Bug Fix Pass

**PROMPT:**
```
Review the entire index.html file and fix any issues:

1. Check all Firestore operations have proper error handling (try/catch)
2. Make sure the canvas works correctly on mobile (touch events)
3. Verify the custom crosshair doesn't cause performance issues 
   (check for memory leaks in animation frames)
4. Test that the right-only drawing constraint works with touch events too
5. Make sure the leaderboard doesn't break when there are 0 users
6. Verify XP calculation handles edge cases (first trace ever, etc.)

Do NOT change any working features. Only fix actual bugs.
```

---

# Quick Reference: File → Task Mapping

| File | Tasks |
|------|-------|
| `index.html` | 1.1, 2.1, 2.2, 3.1, 3.2, 3.3, 4.2, 5.1, 5.2, 6.1 |
| `admin.html` | 1.1, 1.2, 1.3, 2.3, 4.2 |
| `seed-firestore.html` | 2.3, 4.1 |

# Priority Order (if running out of time)

1. ⛔ MUST: Tasks 1.1, 2.1, 2.2, 3.1 (statistics + drawing + basic XP)
2. 🟡 IMPORTANT: Tasks 1.2, 2.3, 3.3, 4.1, 4.2 (outliers + multi-type + leaderboard)
3. 🟢 NICE: Tasks 1.3, 3.2, 5.1, 5.2 (confidence band + streak + tutorial + polish)
