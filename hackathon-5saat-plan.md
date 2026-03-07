# Termogram Dijitalleştirme Oyunu — 5 Saatlik Hackathon Planı

## Ne Yapıyoruz?

Tek bir HTML dosyası. Veritabanı yok, login yok, sunucu yok. Kullanıcı termogram görselini görür, mouse ile mavi çizgiyi takip eder, koordinatlar JSON/CSV olarak indirilir. GitHub Pages ile yayınlanır.

---

## Zaman Çizelgesi

```
SAAT 0:00–0:30  →  Proje kurulumu (repo, klasör, ilk dosya)
SAAT 0:30–2:30  →  Çekirdek geliştirme (Kişi A: canvas + çizim, Kişi B: UI + dışa aktarım)
SAAT 2:30–3:30  →  Birleştirme ve kalibrasyon (piksel → sıcaklık dönüşümü)
SAAT 3:30–4:30  →  Test, hata düzeltme, görsel iyileştirme
SAAT 4:30–5:00  →  Deploy (GitHub Pages) ve sunum hazırlığı
```

---

## SAAT 0:00–0:30 — Proje Kurulumu

İkiniz yan yana oturun ve şu adımları birlikte yapın:

**1) GitHub reposu oluşturun:**
- github.com → "New Repository" → Adı: `termogram-digitizer`
- Public seçin (GitHub Pages için şart)
- "Add a README file" işaretleyin → Create
- Settings → Collaborators → diğer kişiyi ekleyin

**2) İkiniz de klonlayın:**
```bash
git clone https://github.com/KULLANICI_ADI/termogram-digitizer.git
cd termogram-digitizer
```

**3) Klasör yapısını oluşturun:**
```
termogram-digitizer/
├── index.html          ← TEK DOSYA (tüm uygulama burada)
├── images/             ← Termogram görselleri (WebP veya PNG)
│   ├── 1971_AG_USTOS-02.webp
│   ├── 1971_AG_USTOS-09.webp
│   └── ...
├── metadata.json       ← Her görselin kalibrasyon bilgisi
└── README.md
```

**4) Görselleri dönüştürün:**
TIF dosyaları web'de çalışmaz, PNG veya WebP'ye çevirmeniz lazım.
```bash
# Bilgisayarınızda ImageMagick kuruluysa:
for f in *.tif; do convert "$f" "${f%.tif}.png"; done

# Veya online: https://convertio.co/tif-png/ kullanın
# Sonra images/ klasörüne koyun
```

**5) İlk commit:**
```bash
git add .
git commit -m "proje iskeleti"
git push origin main
```

---

## SAAT 0:30–2:30 — Çekirdek Geliştirme (Paralel Çalışma)

Buradan itibaren iki kişi ayrı dallarda çalışacak. **Tek bir `index.html` dosyası olduğu için çakışma riski var.** Bunu şöyle çözün: Kişi A dosyanın üst yarısını (canvas + çizim JS), Kişi B alt yarısını (UI + export JS) yazsın. Veya en basiti, birleştirme aşamasında (saat 2:30) copy-paste ile birleştirin.

### Kişi A — Canvas ve Çizim Motoru

Kişi A şu işlevleri yazacak:
- Termogram görselini canvas'a yükleme
- Mouse basılıyken koordinat toplama
- Çizilen çizgiyi kırmızı olarak gösterme
- Geri al (undo) ve sıfırla (reset) butonları
- Zoom (yakınlaştırma) özelliği

Bu kısım `index.html` dosyası içinde `<script>` bloğunda olacak. Aşağıda tam çalışan iskelet var:

```html
<!-- Kişi A'nın yazacağı kısım: CANVAS + ÇİZİM -->
<canvas id="termogramCanvas"></canvas>

<script>
// ===== ÇİZİM MOTORU =====
const canvas = document.getElementById('termogramCanvas');
const ctx = canvas.getContext('2d');

let isDrawing = false;
let points = [];         // Toplanan piksel koordinatları
let currentImage = null;

// Görseli canvas'a yükle
function loadTermogram(imageSrc) {
  const img = new Image();
  img.onload = () => {
    currentImage = img;
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.drawImage(img, 0, 0);
    points = [];
  };
  img.src = imageSrc;
}

// Mouse olayları
canvas.addEventListener('mousedown', (e) => {
  isDrawing = true;
  const pt = getCanvasPoint(e);
  points = [pt]; // Yeni çizime başla
});

canvas.addEventListener('mousemove', (e) => {
  if (!isDrawing) return;
  const pt = getCanvasPoint(e);
  points.push(pt);

  // Kırmızı çizgi çiz
  if (points.length > 1) {
    const prev = points[points.length - 2];
    ctx.beginPath();
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(pt.x, pt.y);
    ctx.strokeStyle = '#FF0000';
    ctx.lineWidth = 2;
    ctx.stroke();
  }
});

canvas.addEventListener('mouseup', () => {
  isDrawing = false;
});

// Ekrandaki mouse pozisyonunu canvas piksel koordinatına çevir
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

// Canvas'ı sıfırla (görseli yeniden çiz, çizimi sil)
function resetCanvas() {
  if (currentImage) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(currentImage, 0, 0);
    points = [];
  }
}
</script>
```

### Kişi B — UI, Kalibrasyon ve Veri Dışa Aktarım

Kişi B şu işlevleri yazacak:
- Termogram seçme dropdown'ı
- Kalibrasyon sistemi (piksel → sıcaklık/zaman)
- JSON ve CSV indirme butonları
- Basit skor/sayaç gösterimi
- Genel sayfa düzeni ve stil

```html
<!-- Kişi B'nin yazacağı kısım: UI + EXPORT -->

<script>
// ===== KALİBRASYON =====
// Her termogram için kalibrasyon verisi
// "Izgaranın sol üst köşesi pikselde nerede ve hangi değere karşılık geliyor?"
const CALIBRATIONS = {
  "1971_AG_USTOS-02": {
    // Izgaranın köşe pikselleri (görsele bakarak belirleyin)
    gridLeft: 120,      // Izgaranın sol kenarının x pikseli
    gridRight: 3500,    // Izgaranın sağ kenarının x pikseli
    gridTop: 50,        // Izgaranın üst kenarının y pikseli
    gridBottom: 1000,   // Izgaranın alt kenarının y pikseli
    // Bu piksellerin karşılık geldiği gerçek değerler
    tempMax: 40,        // Üst kenar = 40°C
    tempMin: -10,       // Alt kenar = -10°C
    startDate: "1971-08-02T04:00:00",
    endDate: "1971-08-09T08:00:00"
  }
  // ... diğer termogramlar
};

// Piksel koordinatını sıcaklık + zaman değerine dönüştür
function pixelToValue(px_x, px_y, calibration) {
  const cal = calibration;
  // X ekseni: zaman
  const ratioX = (px_x - cal.gridLeft) / (cal.gridRight - cal.gridLeft);
  const startMs = new Date(cal.startDate).getTime();
  const endMs = new Date(cal.endDate).getTime();
  const timestamp = new Date(startMs + ratioX * (endMs - startMs));
  
  // Y ekseni: sıcaklık (yukarı = sıcak, bu yüzden ters)
  const ratioY = (px_y - cal.gridTop) / (cal.gridBottom - cal.gridTop);
  const temperature = cal.tempMax - ratioY * (cal.tempMax - cal.tempMin);

  return {
    timestamp: timestamp.toISOString(),
    temperature: Math.round(temperature * 10) / 10
  };
}

// ===== VERİ DIŞA AKTARIM =====

// JSON olarak indir
function downloadJSON(termogramId) {
  const cal = CALIBRATIONS[termogramId];
  if (!cal || points.length === 0) return alert("Önce bir çizim yapın!");

  const data = {
    termogramId,
    tracedAt: new Date().toISOString(),
    pointCount: points.length,
    rawPixels: points.map(p => ({ x: p.x, y: p.y })),
    calibratedValues: points.map(p => pixelToValue(p.x, p.y, cal))
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${termogramId}_trace.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// CSV olarak indir
function downloadCSV(termogramId) {
  const cal = CALIBRATIONS[termogramId];
  if (!cal || points.length === 0) return alert("Önce bir çizim yapın!");

  let csv = "pixel_x,pixel_y,timestamp,temperature_celsius\n";
  for (const p of points) {
    const val = pixelToValue(p.x, p.y, cal);
    csv += `${p.x},${p.y},${val.timestamp},${val.temperature}\n`;
  }

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${termogramId}_trace.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>
```

---

## SAAT 2:30–3:30 — Birleştirme

İki kişinin yazdığı kodları tek `index.html` dosyasında birleştirin. Aşağıda nihai dosyanın iskeleti var — boşlukları kendi kodlarınızla dolduracaksınız:

```html
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Termogram Dijitalleştirici</title>
  <style>
    /* Buraya Kişi B'nin yazdığı CSS gelecek */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; }
    
    .header { padding: 16px 24px; background: #16213e; }
    .header h1 { font-size: 1.4rem; }
    
    .toolbar { display: flex; gap: 8px; padding: 12px 24px; background: #0f3460; flex-wrap: wrap; align-items: center; }
    .toolbar select, .toolbar button {
      padding: 8px 16px; border-radius: 6px; border: none;
      font-size: 0.9rem; cursor: pointer;
    }
    .toolbar select { background: #1a1a2e; color: #eee; }
    .toolbar button { background: #e94560; color: white; }
    .toolbar button.secondary { background: #533483; }
    .toolbar button:hover { opacity: 0.9; }
    
    .canvas-container {
      overflow-x: auto; padding: 16px;
      background: #0a0a1a; text-align: center;
    }
    canvas { cursor: crosshair; max-width: 100%; height: auto; border: 2px solid #333; }
    
    .status { padding: 12px 24px; background: #16213e; font-size: 0.9rem; }
    .info { padding: 16px 24px; color: #888; font-size: 0.85rem; }
  </style>
</head>
<body>

  <div class="header">
    <h1>🌡️ Termogram Dijitalleştirici</h1>
  </div>

  <div class="toolbar">
    <select id="imageSelect" onchange="onImageChange()">
      <option value="">-- Termogram seçin --</option>
      <!-- Görseller buraya eklenecek -->
    </select>
    <button onclick="resetCanvas()">🔄 Sıfırla</button>
    <button class="secondary" onclick="downloadJSON(currentTermogramId)">📥 JSON İndir</button>
    <button class="secondary" onclick="downloadCSV(currentTermogramId)">📥 CSV İndir</button>
    <span class="status" id="pointCount">Nokta: 0</span>
  </div>

  <div class="canvas-container">
    <canvas id="termogramCanvas"></canvas>
  </div>

  <div class="info">
    <p>💡 Mouse'un sol tuşuna basılı tutarak mavi sıcaklık çizgisini takip edin. 
    Bitirdiğinizde JSON veya CSV olarak indirin.</p>
  </div>

  <script>
    // ===== Kişi A'nın kodu (canvas + çizim) buraya =====
    
    // ===== Kişi B'nin kodu (kalibrasyon + export) buraya =====

    // ===== Birleştirme: görsel listesi =====
    let currentTermogramId = '';

    // Görsel listesini doldur
    const IMAGES = [
      { id: "1971_AG_USTOS-02", label: "1971 Ağustos 02-09", file: "images/1971_AG_USTOS-02.png" },
      { id: "1971_AG_USTOS-09", label: "1971 Ağustos 09-16", file: "images/1971_AG_USTOS-09.png" },
      { id: "1971_AG_USTOS-16", label: "1971 Ağustos 16-23", file: "images/1971_AG_USTOS-16.png" },
      { id: "1971_AG_USTOS-23", label: "1971 Ağustos 23-30", file: "images/1971_AG_USTOS-23.png" },
      { id: "1971_AG_USTOS-30", label: "1971 Ağustos 30-Eyl", file: "images/1971_AG_USTOS-30.png" },
    ];

    const select = document.getElementById('imageSelect');
    IMAGES.forEach(img => {
      const opt = document.createElement('option');
      opt.value = img.id;
      opt.textContent = img.label;
      select.appendChild(opt);
    });

    function onImageChange() {
      const id = select.value;
      if (!id) return;
      currentTermogramId = id;
      const img = IMAGES.find(i => i.id === id);
      loadTermogram(img.file);
    }

    // Nokta sayacını güncelle (mousemove'da çağrılacak)
    setInterval(() => {
      document.getElementById('pointCount').textContent = `Nokta: ${points.length}`;
    }, 200);
  </script>

</body>
</html>
```

---

## SAAT 3:30–4:30 — Kalibrasyon ve Test

Bu aşamada termogramların kalibrasyon değerlerini belirlemeniz gerekiyor. Yani her görseldeki ızgaranın köşelerinin piksel koordinatlarını bulmanız lazım.

**Kalibrasyon nasıl yapılır:**
1. Herhangi bir görsel editörde (Paint, GIMP, hatta tarayıcıdaki canvas'ın kendisi) termogramı açın.
2. Izgaranın sol üst köşesine mouse'u götürün, piksel koordinatını (x, y) not alın.
3. Sağ üst, sol alt, sağ alt köşeler için de aynısını yapın.
4. Termogramdaki sıcaklık etiketlerinden üst ve alt sıcaklık değerlerini okuyun (muhtemelen 40°C üst, -10°C alt).
5. Başlık kısmındaki tarih bilgisinden zaman aralığını belirleyin.
6. Bu değerleri `CALIBRATIONS` nesnesine girin.

**Test kontrol listesi:**
- [ ] Görsel seçince canvas'a yükleniyor mu?
- [ ] Mouse ile çizim yapılabiliyor mu?
- [ ] Kırmızı çizgi görünüyor mu?
- [ ] Sıfırla butonu çalışıyor mu?
- [ ] JSON indirince dosya geliyor mu?
- [ ] CSV indirince dosya geliyor mu?
- [ ] İndirilen dosyadaki sıcaklık değerleri mantıklı mı? (mesela Ağustos ayında 20-35°C arası beklenir)

---

## SAAT 4:30–5:00 — Deploy ve Sunum

**GitHub Pages deploy (3 dakika):**
1. Tüm dosyaları commit'leyin: `git add . && git commit -m "final" && git push`
2. GitHub'da repo → Settings → Pages
3. Source: "Deploy from a branch" → Branch: `main` → Folder: `/ (root)` → Save
4. 1-2 dakika bekleyin, siteniz `https://KULLANICI.github.io/termogram-digitizer/` adresinde yayında

**Sunum için vurgulayın:**
- "Crowd-sourcing" ile veri dijitalleştirme (Zooniverse benzeri yaklaşım)
- Aynı termogramı birden fazla kişiye çizdirerek çapraz doğrulama yapılabilir
- OCR'ın başaramadığı bozuk/soluk verilerde insan gözü çok daha başarılı
- Ölçeklenebilir: yüzlerce gönüllü aynı anda çalışabilir

---

## Görev Dağılımı Özet Tablosu

```
Saat        Kişi A                          Kişi B
─────────────────────────────────────────────────────────────
0:00-0:30   [BİRLİKTE] Repo + klasör kurulumu
0:30-1:30   Canvas'a görsel yükleme         TIF→PNG dönüşümü
            Mouse event dinleme             Kalibrasyon JSON hazırlama
            Koordinat toplama               Sayfa HTML/CSS iskeleti
1:30-2:30   Kırmızı çizgi çizimi            pixelToValue() fonksiyonu
            Reset/undo butonları            JSON/CSV indirme fonksiyonu
            Zoom özelliği (varsa vakit)     Dropdown + buton bağlama
2:30-3:30   [BİRLİKTE] Kodları birleştirme + ilk test
3:30-4:30   [BİRLİKTE] Hata düzeltme + kalibrasyon ince ayar
4:30-5:00   [BİRLİKTE] Deploy + sunum hazırlığı
```

---

## Dikkat Edilecekler

**Git çakışmasını önlemek için:** İlk 2 saatte ayrı dosyalarda çalışın (`kisiA.js` ve `kisiB.js`), saat 2:30'da bunları `index.html` içine yapıştırın. Bu en basit yol.

**Kalibrasyon en kritik kısım:** Eğer piksel → sıcaklık dönüşümü yanlışsa tüm çıktı veri çöp olur. Bir termogramın bilinen bir sıcaklık noktasını (örneğin ızgara üzerinde 30°C çizgisi) kontrol ederek doğrulayın.

**Yetişmezse neleri çıkarın:** Zoom'u çıkarın, skoru çıkarın, CSS'i basit tutun. Önemli olan: "görsel yükle → çiz → indir" döngüsünün çalışması.
