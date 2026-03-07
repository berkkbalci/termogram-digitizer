# Termogram Dijitalleştirme Oyunu — 5 Saatlik Hackathon Planı (v2)
# Firebase + Görsel Havuzu + Çapraz Doğrulama

---

## Sistemin Çalışma Mantığı (Büyük Resim)

Sisteminiz şu döngüyle çalışacak: Bir görsel havuzunuz var (yüzlerce termogram). Bir kullanıcı siteye girdiğinde sistem havuzdan rastgele bir termogram seçer ve gösterir. Ama burada bir incelik var: **aynı termogram en fazla 3 farklı kişiye atanır**. Üç kişi aynı görseli bağımsızca çizdiğinde, çapraz doğrulama yapabilirsiniz — eğer üç çizim birbirine yakınsa veri güvenilirdir.

```
GÖRSEL HAVUZU (Firestore)            KULLANICILAR
┌─────────────────────────┐
│ termogram_001  [0/3] ───────────▶  Kullanıcı A → çizer → kaydet
│ termogram_002  [1/3]    │          Kullanıcı B → çizer → kaydet  
│ termogram_003  [3/3] ✓  │          Kullanıcı C → çizer → kaydet
│ termogram_004  [2/3]    │
│ ...                     │          Her termogram 3 kez çizilince
└─────────────────────────┘          "tamamlandı" olarak işaretlenir
```

**Firestore'daki iki koleksiyon:**

`termograms` koleksiyonu — Her termogram bir belge. İçinde görselin yolu, kalibrasyon bilgisi ve kaç kez çizildiği var. Sistem buradan "henüz 3'e ulaşmamış" olanları çeker ve rastgele birini kullanıcıya atar.

`traces` koleksiyonu — Her çizim bir belge. İçinde hangi termogramın çizildiği, hangi kullanıcının çizdiği, piksel koordinatları ve kalibre edilmiş sıcaklık/zaman değerleri var.

---

## Zaman Çizelgesi

```
SAAT 0:00–0:30   Proje kurulumu (repo + Firebase projesi)
SAAT 0:30–1:00   Kişi B: Firebase yapılandırma + güvenlik kuralları
                 Kişi A: HTML/CSS iskelet + Canvas temeli
SAAT 1:00–2:30   Kişi A: Çizim motoru (mouse tracking + kırmızı çizgi)
                 Kişi B: Görsel havuzu mantığı + veri kaydetme
SAAT 2:30–3:30   BİRLİKTE: Birleştirme + uçtan uca test
SAAT 3:30–4:30   BİRLİKTE: Kalibrasyon ince ayar + hata düzeltme
SAAT 4:30–5:00   Deploy + sunum hazırlığı
```

---

## SAAT 0:00–0:30 — Proje Kurulumu

İkiniz yan yana oturun ve birlikte yapın.

### GitHub Reposu

1. github.com → New Repository → Adı: `termogram-digitizer` → Public → Add README → Create.
2. Settings → Collaborators → diğer kişiyi ekleyin.
3. İkiniz de klonlayın:

```bash
git clone https://github.com/KULLANICI/termogram-digitizer.git
cd termogram-digitizer
```

### Firebase Projesi

1. https://console.firebase.google.com → "Add project" → Adı: `termogram-digitizer`.
2. Google Analytics'i kapatın (gereksiz, vakit kaybı).
3. Proje oluşturulunca sol menüden **Firestore Database** → "Create database" → **Start in test mode** (şimdilik test mode, güvenlik kurallarını sonra yazacaksınız) → Konum: `europe-west1` (Türkiye'ye yakın).
4. Sol menüden **Authentication** → "Get started" → Sign-in method → **Anonymous** → Enable → Save.
5. Proje ayarları (dişli ikonu) → "Your apps" → Web (\</\> ikonu) → Adı: `termogram-web` → Register app.
6. Ekranda çıkan `firebaseConfig` nesnesini kopyalayın, birazdan lazım olacak.

### Klasör Yapısı

```bash
mkdir -p images scripts
# TIF'leri PNG'ye çevirin (bkz. bir önceki plan) ve images/ klasörüne koyun
```

```
termogram-digitizer/
├── index.html              ← Tüm uygulama (tek dosya)
├── images/                 ← Termogram görselleri (PNG)
│   ├── 1971_AG_USTOS-02.png
│   ├── 1971_AG_USTOS-09.png
│   └── ...
├── scripts/
│   └── seed-firestore.html ← Firestore'a görsel havuzunu yükleyen araç
└── README.md
```

İlk commit:
```bash
git add .
git commit -m "proje iskeleti ve görseller"
git push origin main
```

---

## SAAT 0:30–1:00 — Temel Altyapı (Paralel)

### Kişi B: Firebase Yapılandırma

Kişi B, `index.html` dosyasının `<head>` kısmına Firebase SDK'larını ve yapılandırmayı yazacak. Firebase'i CDN üzerinden yükleyeceğiz (npm kurulumu gereksiz, zaman kazandırır):

```html
<!-- index.html'in <head> kısmına eklenecek -->
<script type="module">
  // Firebase SDK — CDN'den yükleniyor, kurulum gerektirmez
  import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
  import { getFirestore, collection, doc, getDoc, getDocs, addDoc, updateDoc, 
           query, where, orderBy, limit, increment, serverTimestamp } 
           from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js';
  import { getAuth, signInAnonymously, onAuthStateChanged } 
           from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';

  // ── Firebase yapılandırma (Console'dan kopyaladığınız değerler) ──
  const firebaseConfig = {
    apiKey: "BURAYA_YAPIŞTIRIN",
    authDomain: "PROJE_ADI.firebaseapp.com",
    projectId: "PROJE_ADI",
    storageBucket: "PROJE_ADI.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abc123"
  };

  const app = initializeApp(firebaseConfig);
  const db = getFirestore(app);
  const auth = getAuth(app);

  // ── Tüm Firebase fonksiyonlarını global yap (diğer scriptler kullanabilsin) ──
  window.db = db;
  window.auth = auth;
  window.fbImports = { 
    collection, doc, getDoc, getDocs, addDoc, updateDoc,
    query, where, orderBy, limit, increment, serverTimestamp 
  };
</script>
```

Sonra Kişi B, Firestore'a görsel havuzunu yüklemek için **tek seferlik bir araç sayfası** yazacak. Bu sayfayı tarayıcıda açıp "Yükle" butonuna basınca tüm termogram kayıtları Firestore'a eklenir:

```html
<!-- scripts/seed-firestore.html -->
<!-- Bu dosyayı sadece 1 kez çalıştıracaksınız, ürüne dahil değil -->
<!DOCTYPE html>
<html><head><title>Firestore Seed</title></head>
<body>
<h2>Firestore'a Görsel Havuzunu Yükle</h2>
<button onclick="seedData()">Yükle</button>
<pre id="log"></pre>

<script type="module">
  import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
  import { getFirestore, doc, setDoc } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js';

  const app = initializeApp({
    // Aynı firebaseConfig buraya da yapıştırın
    apiKey: "...", authDomain: "...", projectId: "...",
    storageBucket: "...", messagingSenderId: "...", appId: "..."
  });
  const db = getFirestore(app);

  // ── Tüm termogramların listesi ──
  // Her birinin kalibrasyon bilgisini termograma bakarak doldurun
  const TERMOGRAMS = [
    {
      id: "1971_AG_USTOS-02",
      imageFile: "images/1971_AG_USTOS-02.png",
      label: "1971 Ağustos 02–09",
      startDate: "1971-08-02T04:00:00",
      endDate: "1971-08-09T08:00:00",
      tempMin: -10,
      tempMax: 40,
      // Izgaranın köşe pikselleri (her görsel için ayrı ayrı ölçün)
      gridLeft: 120,
      gridRight: 3500,
      gridTop: 50,
      gridBottom: 1000,
      // Çapraz doğrulama sayacı
      traceCount: 0,       // Kaç kez çizildi
      maxTraces: 3,         // Hedef: 3 farklı kişi çizecek
      status: "available"   // available | completed
    },
    {
      id: "1971_AG_USTOS-09",
      imageFile: "images/1971_AG_USTOS-09.png",
      label: "1971 Ağustos 09–16",
      startDate: "1971-08-09T04:00:00",
      endDate: "1971-08-16T08:00:00",
      tempMin: -10, tempMax: 40,
      gridLeft: 120, gridRight: 3480, gridTop: 50, gridBottom: 1000,
      traceCount: 0, maxTraces: 3, status: "available"
    },
    // ... diğer termogramları da aynı şekilde ekleyin
    // NOT: gridLeft/Right/Top/Bottom değerlerini her görsel için
    // Paint veya GIMP ile ölçerek belirleyin
  ];

  window.seedData = async function() {
    const log = document.getElementById('log');
    for (const t of TERMOGRAMS) {
      await setDoc(doc(db, "termograms", t.id), t);
      log.textContent += `✓ ${t.id} yüklendi\n`;
    }
    log.textContent += `\nTamamlandı! ${TERMOGRAMS.length} termogram yüklendi.`;
  };
</script>
</body></html>
```

### Kişi A: HTML/CSS İskelet + Canvas Temeli

Kişi A bu sırada `index.html`'in gövdesini ve canvas altyapısını yazacak. CSS'i basit ama kullanılabilir tutun, süslemeye vakit harcamayın:

```html
<!-- index.html gövdesi (Kişi A yazacak) -->
<body>
  <!-- Giriş ekranı: İsim girişi -->
  <div id="loginScreen">
    <div class="login-box">
      <h1>🌡️ Termogram Dijitalleştirici</h1>
      <p>Tarihsel iklim verilerini dijitalleştirmeye yardım edin!</p>
      <input type="text" id="nameInput" placeholder="Adınızı girin..." maxlength="30">
      <button onclick="enterApp()">Başla</button>
    </div>
  </div>

  <!-- Ana uygulama -->
  <div id="appScreen" style="display:none;">
    <div class="header">
      <h1>🌡️ Termogram Dijitalleştirici</h1>
      <span id="userInfo"></span>
    </div>

    <div class="toolbar">
      <button onclick="getNewTermogram()">🎲 Yeni Termogram Getir</button>
      <button onclick="resetCanvas()">🔄 Sıfırla</button>
      <button onclick="submitTrace()" id="submitBtn" disabled>✅ Gönder</button>
      <span id="statusText">Termogram yükleniyor...</span>
    </div>

    <div class="canvas-container">
      <canvas id="termogramCanvas"></canvas>
    </div>

    <div class="info-bar">
      <span id="pointCount">Nokta: 0</span>
      <span id="termogramLabel">—</span>
      <span id="traceProgress">—</span>
    </div>
  </div>
</body>
```

---

## SAAT 1:00–2:30 — Çekirdek Geliştirme (Paralel)

Bu kısımda **Kişi A** ve **Kişi B** ayrı dosyalarda çalışacak. Çakışmayı önlemek için en basit yol: Kişi A kendi kodunu `kisiA.js` dosyasında, Kişi B kendi kodunu `kisiB.js` dosyasında yazsın. Saat 2:30'da bunları `index.html`'in `<script>` bloğuna yapıştıracaksınız.

### Kişi A: Çizim Motoru (`kisiA.js`)

```javascript
// ═══════════════════════════════════════════
// KİŞİ A — CANVAS ÇİZİM MOTORU
// ═══════════════════════════════════════════

const canvas = document.getElementById('termogramCanvas');
const ctx = canvas.getContext('2d');

let isDrawing = false;
let points = [];            // Toplanan piksel koordinatları [{x, y, t}, ...]
let currentImage = null;    // Yüklü olan Image nesnesi

// ── Görseli canvas'a yükle ──
function loadTermogram(imageSrc) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      currentImage = img;
      // Canvas boyutunu görsele eşitle
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      points = [];
      updatePointCount();
      document.getElementById('submitBtn').disabled = true;
      resolve();
    };
    img.onerror = reject;
    img.src = imageSrc;
  });
}

// ── Mouse olayları ──
canvas.addEventListener('mousedown', (e) => {
  isDrawing = true;
  const pt = getCanvasPoint(e);
  points = [pt];  // Her yeni çizimde sıfırdan başla
  // Görseli yeniden çiz (önceki kırmızı çizgiyi temizle)
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(currentImage, 0, 0);
});

canvas.addEventListener('mousemove', (e) => {
  if (!isDrawing) return;
  const pt = getCanvasPoint(e);
  points.push(pt);

  // Son iki nokta arasına kırmızı çizgi çiz
  if (points.length > 1) {
    const prev = points[points.length - 2];
    ctx.beginPath();
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(pt.x, pt.y);
    ctx.strokeStyle = '#FF0000';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.stroke();
  }

  updatePointCount();
});

canvas.addEventListener('mouseup', () => {
  isDrawing = false;
  // En az 50 nokta varsa "Gönder" butonunu aktifleştir
  // (çok kısa çizimler veri olarak işe yaramaz)
  if (points.length >= 50) {
    document.getElementById('submitBtn').disabled = false;
  }
});

// Mouse sayfadan çıkarsa çizimi durdur
canvas.addEventListener('mouseleave', () => {
  isDrawing = false;
});

// ── Yardımcı fonksiyonlar ──

// Ekrandaki mouse pozisyonunu canvas'ın gerçek piksel koordinatına çevirir.
// Canvas CSS ile küçültülmüş olabilir, bu yüzden ölçek hesabı gerekir.
function getCanvasPoint(e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: Math.round((e.clientX - rect.left) * scaleX),
    y: Math.round((e.clientY - rect.top) * scaleY),
    t: Date.now()
  };
}

function resetCanvas() {
  if (currentImage) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(currentImage, 0, 0);
    points = [];
    updatePointCount();
    document.getElementById('submitBtn').disabled = true;
  }
}

function updatePointCount() {
  document.getElementById('pointCount').textContent = `Nokta: ${points.length}`;
}
```

### Kişi B: Görsel Havuzu + Firebase İşlemleri (`kisiB.js`)

```javascript
// ═══════════════════════════════════════════
// KİŞİ B — GÖRSEL HAVUZU + FİREBASE
// ═══════════════════════════════════════════

let currentUser = null;      // { uid, displayName }
let currentTermogram = null; // Firestore'dan çekilen aktif termogram

// ── Anonim Giriş ──
// Kullanıcı isim girer, Firebase anonim hesap oluşturur,
// ismi localStorage'da tutar (bir sonraki gelişinde hatırlamak için)
async function enterApp() {
  const name = document.getElementById('nameInput').value.trim();
  if (!name) return alert('Lütfen bir isim girin');

  try {
    // Firebase anonim giriş
    const { signInAnonymously } = await import(
      'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js'
    );
    const result = await signInAnonymously(window.auth);
    
    currentUser = {
      uid: result.user.uid,
      displayName: name
    };

    // İsmi hatırla
    localStorage.setItem('userName', name);

    // Ekranları değiştir
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('appScreen').style.display = 'block';
    document.getElementById('userInfo').textContent = `Merhaba, ${name}`;

    // İlk termogramı getir
    await getNewTermogram();
  } catch (err) {
    console.error('Giriş hatası:', err);
    alert('Giriş yapılamadı. Sayfa yenilenip tekrar deneyin.');
  }
}

// ── Görsel Havuzundan Rastgele Termogram Getir ──
// Mantık: Firestore'dan status="available" olan termogramları çek,
// bu kullanıcının daha önce çizmediği birini rastgele seç.
async function getNewTermogram() {
  const { collection, getDocs, query, where } = window.fbImports;
  
  document.getElementById('statusText').textContent = 'Termogram aranıyor...';

  try {
    // 1) Henüz tamamlanmamış termogramları çek
    const q = query(
      collection(window.db, 'termograms'),
      where('status', '==', 'available')
    );
    const snapshot = await getDocs(q);
    
    if (snapshot.empty) {
      document.getElementById('statusText').textContent = 
        'Tüm termogramlar tamamlandı! 🎉';
      return;
    }

    // 2) Bu kullanıcının daha önce çizdiği termogramları bul
    const tracesQ = query(
      collection(window.db, 'traces'),
      where('userId', '==', currentUser.uid)
    );
    const tracesSnap = await getDocs(tracesQ);
    const alreadyTraced = new Set(
      tracesSnap.docs.map(d => d.data().termogramId)
    );

    // 3) Kullanıcının henüz çizmediği termogramları filtrele
    const available = snapshot.docs.filter(d => !alreadyTraced.has(d.id));

    if (available.length === 0) {
      document.getElementById('statusText').textContent = 
        'Tüm mevcut termogramları çizdiniz. Yenileri eklenince tekrar gelin! 👏';
      return;
    }

    // 4) Rastgele birini seç
    const randomDoc = available[Math.floor(Math.random() * available.length)];
    currentTermogram = { id: randomDoc.id, ...randomDoc.data() };

    // 5) Görseli yükle
    await loadTermogram(currentTermogram.imageFile);

    // UI güncelle
    document.getElementById('termogramLabel').textContent = currentTermogram.label;
    document.getElementById('traceProgress').textContent = 
      `Çizim: ${currentTermogram.traceCount}/${currentTermogram.maxTraces}`;
    document.getElementById('statusText').textContent = 
      'Mavi çizgiyi mouse ile takip edin →';

  } catch (err) {
    console.error('Termogram getirme hatası:', err);
    document.getElementById('statusText').textContent = 'Hata oluştu, tekrar deneyin.';
  }
}

// ── Çizimi Firebase'e Gönder ──
async function submitTrace() {
  if (!currentTermogram || points.length < 50) return;

  const { collection, addDoc, doc, updateDoc, increment, serverTimestamp } 
    = window.fbImports;

  document.getElementById('submitBtn').disabled = true;
  document.getElementById('statusText').textContent = 'Kaydediliyor...';

  try {
    const cal = currentTermogram;

    // 1) Piksel koordinatlarını sıcaklık/zaman değerine dönüştür
    const calibratedData = points.map(p => {
      const ratioX = (p.x - cal.gridLeft) / (cal.gridRight - cal.gridLeft);
      const ratioY = (p.y - cal.gridTop) / (cal.gridBottom - cal.gridTop);

      const startMs = new Date(cal.startDate).getTime();
      const endMs = new Date(cal.endDate).getTime();
      const timestamp = new Date(startMs + ratioX * (endMs - startMs));
      const temperature = cal.tempMax - ratioY * (cal.tempMax - cal.tempMin);

      return {
        timestamp: timestamp.toISOString(),
        temperature: Math.round(temperature * 10) / 10
      };
    });

    // 2) Çizimi traces koleksiyonuna kaydet
    await addDoc(collection(window.db, 'traces'), {
      termogramId: currentTermogram.id,
      userId: currentUser.uid,
      userName: currentUser.displayName,
      pointCount: points.length,
      // Ham pikselleri kaydet (ileride yeniden kalibrasyon gerekirse lazım)
      rawPoints: points.map(p => ({ x: p.x, y: p.y })),
      // Kalibre edilmiş değerleri kaydet
      calibratedData: calibratedData,
      createdAt: serverTimestamp()
    });

    // 3) Termogramın çizim sayacını artır
    const termRef = doc(window.db, 'termograms', currentTermogram.id);
    const newCount = currentTermogram.traceCount + 1;
    
    await updateDoc(termRef, {
      traceCount: increment(1),
      // 3'e ulaştıysa "completed" olarak işaretle
      ...(newCount >= currentTermogram.maxTraces ? { status: 'completed' } : {})
    });

    // 4) Başarı mesajı ve sonraki termograma geç
    document.getElementById('statusText').textContent = 
      '✅ Kaydedildi! Yeni termogram yükleniyor...';
    
    setTimeout(() => getNewTermogram(), 1500);

  } catch (err) {
    console.error('Kaydetme hatası:', err);
    document.getElementById('statusText').textContent = 'Kaydetme başarısız. Tekrar deneyin.';
    document.getElementById('submitBtn').disabled = false;
  }
}
```

---

## SAAT 2:30–3:30 — Birleştirme

İki kişinin kodlarını `index.html` içinde birleştirin. Nihai dosyanın yapısı şöyle olacak:

```html
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Termogram Dijitalleştirici</title>

  <!-- ① Firebase SDK ve yapılandırma (Kişi B yazdı) -->
  <script type="module">
    // ... Firebase importları ve config buraya ...
    // ... window.db, window.auth, window.fbImports atamaları ...
  </script>

  <style>
    /* ② CSS (Kişi A yazdı, basit tutun) */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; background: #111827; color: #e5e7eb; }

    #loginScreen {
      display: flex; justify-content: center; align-items: center;
      height: 100vh; background: linear-gradient(135deg, #1e3a5f, #111827);
    }
    .login-box { text-align: center; padding: 40px; }
    .login-box h1 { font-size: 2rem; margin-bottom: 12px; }
    .login-box p { color: #9ca3af; margin-bottom: 24px; }
    .login-box input {
      padding: 12px 20px; font-size: 1rem; border-radius: 8px;
      border: 2px solid #374151; background: #1f2937; color: white;
      width: 260px; margin-right: 8px;
    }
    .login-box button {
      padding: 12px 24px; font-size: 1rem; border-radius: 8px;
      border: none; background: #2563eb; color: white; cursor: pointer;
    }

    .header {
      display: flex; justify-content: space-between; align-items: center;
      padding: 12px 24px; background: #1f2937;
    }
    .header h1 { font-size: 1.2rem; }

    .toolbar {
      display: flex; gap: 8px; padding: 10px 24px;
      background: #1e3a5f; flex-wrap: wrap; align-items: center;
    }
    .toolbar button {
      padding: 8px 16px; border-radius: 6px; border: none;
      font-size: 0.85rem; cursor: pointer; color: white;
    }
    .toolbar button { background: #2563eb; }
    .toolbar button:disabled { background: #374151; cursor: not-allowed; }
    .toolbar button:hover:not(:disabled) { opacity: 0.85; }
    #statusText { margin-left: auto; font-size: 0.85rem; color: #93c5fd; }

    .canvas-container {
      overflow-x: auto; padding: 12px; background: #030712; text-align: center;
    }
    canvas { cursor: crosshair; max-width: 100%; height: auto; }

    .info-bar {
      display: flex; justify-content: space-between;
      padding: 10px 24px; background: #1f2937; font-size: 0.8rem; color: #9ca3af;
    }
  </style>
</head>
<body>

  <!-- ③ Giriş ekranı -->
  <div id="loginScreen">
    <div class="login-box">
      <h1>🌡️ Termogram Dijitalleştirici</h1>
      <p>115 yıllık iklim verilerini dijitalleştirmeye yardım edin</p>
      <input type="text" id="nameInput" placeholder="Adınızı girin...">
      <button onclick="enterApp()">Başla</button>
    </div>
  </div>

  <!-- ④ Ana uygulama -->
  <div id="appScreen" style="display:none;">
    <div class="header">
      <h1>🌡️ Termogram Dijitalleştirici</h1>
      <span id="userInfo"></span>
    </div>
    <div class="toolbar">
      <button onclick="getNewTermogram()">🎲 Yeni Termogram</button>
      <button onclick="resetCanvas()">🔄 Sıfırla</button>
      <button onclick="submitTrace()" id="submitBtn" disabled>✅ Gönder</button>
      <span id="statusText">Yükleniyor...</span>
    </div>
    <div class="canvas-container">
      <canvas id="termogramCanvas"></canvas>
    </div>
    <div class="info-bar">
      <span id="pointCount">Nokta: 0</span>
      <span id="termogramLabel">—</span>
      <span id="traceProgress">—</span>
    </div>
  </div>

  <!-- ⑤ Uygulama kodu (type="module" OLMAMALI, global scope'ta çalışmalı) -->
  <script>
    // Kişi A'nın kodu (canvas + çizim) BURAYA YAPIŞTIRIN
    // Kişi B'nin kodu (firebase + havuz) BURAYA YAPIŞTIRIN
  </script>

</body>
</html>
```

**ÖNEMLİ UYARI:** Firebase SDK'sı `type="module"` ile yükleniyor ama çizim/UI kodları global scope'ta çalışmalı. Bu yüzden Firebase importları `window.db` gibi global değişkenlere atanıyor. Çizim ve Firebase kodlarını `type="module"` **olmayan** bir `<script>` bloğuna koyun. Firebase'in yüklenmesini beklemek için uygulama kodunun başına şunu ekleyin:

```javascript
// Firebase'in yüklenmesini bekle (module script async yüklenir)
function waitForFirebase() {
  return new Promise(resolve => {
    const check = () => window.db ? resolve() : setTimeout(check, 100);
    check();
  });
}
```

---

## SAAT 3:30–4:30 — Firestore Güvenlik Kuralları + Test

Test modunu kapamadan önce güvenlik kurallarını yazın. Firebase Console → Firestore → Rules sekmesine gidin:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Termogramlar: herkes okuyabilir, kimse web'den yazamaz
    match /termograms/{docId} {
      allow read: if true;
      allow update: if request.auth != null
        && request.resource.data.diff(resource.data).affectedKeys()
           .hasOnly(['traceCount', 'status']);
      allow create, delete: if false;
    }
    
    // Çizimler: giriş yapmış kullanıcı kendi verisini yazabilir
    match /traces/{docId} {
      allow create: if request.auth != null
        && request.resource.data.userId == request.auth.uid
        && request.resource.data.rawPoints.size() <= 10000;
      allow read: if request.auth != null
        && resource.data.userId == request.auth.uid;
      allow update, delete: if false;
    }
  }
}
```

**Test kontrol listesi:**
1. İsim girip "Başla" → giriş yapılıyor mu?
2. Termogram otomatik yükleniyor mu?
3. Mouse ile çizim yapılıyor mu, kırmızı çizgi görünüyor mu?
4. "Gönder" → Firebase'e kaydediliyor mu? (Console → Firestore → traces koleksiyonunu kontrol edin)
5. "Yeni Termogram" → farklı bir görsel geliyor mu?
6. Aynı termogramı tekrar çizmeye çalışınca farklı biri mi geliyor?
7. 3 farklı tarayıcı sekmesinden (veya gizli pencereden) aynı görseli 3 kez çizin → status "completed" oluyor mu?

---

## SAAT 4:30–5:00 — Deploy

**GitHub Pages deploy:**
1. `git add . && git commit -m "hackathon final" && git push origin main`
2. GitHub → Settings → Pages → Source: "Deploy from a branch" → Branch: `main` → `/ (root)` → Save
3. 2 dakika bekleyin → `https://KULLANICI.github.io/termogram-digitizer/`

---

## Görev Dağılımı Özet

```
Saat         Kişi A (Oyun Motoru)               Kişi B (Veri Altyapısı)
───────────────────────────────────────────────────────────────────────
0:00–0:30    [BİRLİKTE] Repo + Firebase proje kurulumu
0:30–1:00    HTML/CSS iskelet, canvas temeli     Firebase config, seed aracı
1:00–2:30    kisiA.js: mouse tracking,           kisiB.js: anonim giriş,
             çizim, reset, nokta sayacı          havuz mantığı, submitTrace
2:30–3:30    [BİRLİKTE] Birleştirme + uçtan uca test
3:30–4:30    [BİRLİKTE] Güvenlik kuralları + hata düzeltme + kalibrasyon
4:30–5:00    [BİRLİKTE] Deploy + sunum hazırlığı
```

---

## Hackathon Sunumu İçin Anahtar Mesajlar

**"Aynı termogramı 3 farklı gönüllüye çizdiriyoruz."** Bu, verinin güvenilirliğini ölçmek için güçlü bir yöntem. Üç çizim birbirine ne kadar yakınsa, dijitalleştirme o kadar doğru demektir. İstatistiksel olarak standart sapma hesaplayarak her zaman dilimi için güven aralığı bile verebilirsiniz.

**"OCR'ın başaramadığı yerde insan gözü devreye giriyor."** Termogramlardaki bozuk, soluk, üst üste binmiş çizgileri otomatik algoritmalar güvenilir şekilde ayrıştıramaz. İnsan gözü bu konuda çok daha başarılı ve oyunlaştırma ile ölçeklenebilir hale geliyor.

**"Citizen Science yaklaşımı."** Zooniverse, Galaxy Zoo gibi başarılı projelerin aynı modelini meteoroloji verisine uyguluyorsunuz.
