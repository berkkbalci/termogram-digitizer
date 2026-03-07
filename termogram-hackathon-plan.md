# Termogram Dijitalleştirme Oyunu — Proje Yol Haritası

## Projeye Genel Bakış

**Amaç:** Tarihsel termogram fotoğraflarındaki sıcaklık eğrilerini, gönüllü kullanıcıların mouse ile takip etmesi yoluyla dijitalleştirmek. Kullanıcı termogramdaki mavi çizgiyi mouse ile izleyerek x-y koordinatlarını üretecek, bu koordinatlar sıcaklık-zaman verisine dönüştürülecek.

**Teknoloji Kararı:** Projenizi tamamen statik (sunucu gerektirmeyen) bir mimariyle kurmanızı öneriyorum. Bunun nedenleri şunlar: iki kişilik bir ekip olarak backend yönetimi, sunucu maliyeti ve güvenlik güncellemeleriyle uğraşmak istemezsiniz. GitHub Pages ile ücretsiz ve güvenli hosting yapabilirsiniz. Veri toplama için Firebase (ücretsiz katman) kullanabilirsiniz; bu şekilde hem veritabanı hem de kimlik doğrulama işleriniz hazır gelir.

---

## Mimari Tasarım

### Bileşenler ve Veri Akışı

Sistemin üç ana bileşeni vardır ve birbirleriyle şu şekilde konuşurlar:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   GitHub Pages   │────▶│  Kullanıcı       │────▶│   Firebase      │
│   (Statik Site)  │     │  Tarayıcısı      │     │   (Veritabanı)  │
│                  │     │                  │     │                 │
│  - HTML/CSS/JS   │     │  - Termogram     │     │  - Firestore    │
│  - Görseller     │     │    görüntüleme   │     │  - Auth         │
│    (WebP)        │     │  - Mouse takip   │     │  - Koordinatlar │
│  - React App     │     │  - Veri gönderme │     │  - Skorlar      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Neden bu mimari?**

GitHub Pages tamamen statik dosya sunar; yani sunucuda çalışan bir kod yoktur. Bu demektir ki SQL injection, sunucu tarafı kod çalıştırma gibi saldırı vektörleri baştan elenir. Firebase tarafında ise güvenlik kurallarını yazarak kimlerin veri okuyup yazabileceğini tam olarak kontrol edersiniz. Üstelik her iki servis de ücretsiz katmanda hackathon için fazlasıyla yeterli kapasite sunar.

### Dosya Yapısı

```
termogram-digitizer/
├── public/
│   ├── index.html
│   ├── images/              ← Termogram görselleri (WebP formatında)
│   │   ├── 1971_AG_USTOS-02.webp
│   │   ├── 1971_AG_USTOS-09.webp
│   │   └── ...
│   └── favicon.ico
├── src/
│   ├── App.jsx              ← Ana uygulama bileşeni
│   ├── main.jsx             ← React giriş noktası
│   ├── components/
│   │   ├── TermogramCanvas.jsx   ← Çizim/takip alanı (ANA BILEŞEN)
│   │   ├── ImageSelector.jsx     ← Hangi termogramın seçileceği
│   │   ├── Leaderboard.jsx       ← Skor tablosu
│   │   ├── Tutorial.jsx          ← İlk kez kullananlar için rehber
│   │   └── Navbar.jsx            ← Üst menü
│   ├── firebase/
│   │   ├── config.js             ← Firebase bağlantı ayarları
│   │   ├── auth.js               ← Giriş/çıkış işlemleri
│   │   └── db.js                 ← Veritabanı okuma/yazma fonksiyonları
│   ├── utils/
│   │   ├── coordinateMapper.js   ← Piksel → sıcaklık/zaman dönüşümü
│   │   ├── imageProcessor.js     ← Görsel yükleme ve ölçekleme
│   │   └── dataExporter.js       ← CSV/JSON dışa aktarım
│   └── styles/
│       └── global.css
├── scripts/
│   └── convert-images.sh    ← TIF → WebP dönüştürme scripti
├── firebase.json             ← Güvenlik kuralları
├── firestore.rules           ← Firestore güvenlik kuralları
├── package.json
├── vite.config.js            ← Build ayarları
├── .gitignore
└── README.md
```

---

## GitHub Kullanım Rehberi (Sıfırdan)

### 1. Hesap ve Repo Kurulumu

İkiniz de ayrı GitHub hesabı açarsınız. Biriniz (diyelim Kişi A) repoyu oluşturur. Aşağıdaki adımları sırayla takip edin.

**Kişi A (Repo Sahibi):**

1. github.com'da "New Repository" butonuna tıklayın.
2. Repository adı: `termogram-digitizer`
3. "Public" seçin (GitHub Pages ücretsiz olması için Public olmalı).
4. "Add a README file" seçeneğini işaretleyin.
5. `.gitignore` template olarak "Node" seçin.
6. "Create repository" butonuna basın.
7. Settings → Collaborators → "Add people" ile Kişi B'yi ekleyin.

**Kişi B (Collaborator):**

1. E-posta davetini kabul edin.
2. Artık aynı repoya push yapabilirsiniz.

### 2. Bilgisayarınıza Kurulumlar

Her iki kişi de şu araçları kurmalı:

```bash
# 1. Node.js'i indirin ve kurun: https://nodejs.org (LTS sürümü)
# 2. Git'i kurun: https://git-scm.com

# 3. Terminal açın, repoyu klonlayın
git clone https://github.com/KULLANICI_ADI/termogram-digitizer.git
cd termogram-digitizer

# 4. Projeyi başlatın
npm create vite@latest . -- --template react
npm install

# 5. Firebase SDK'sını ekleyin
npm install firebase
```

### 3. Günlük Çalışma Döngüsü (Git Workflow)

İki kişilik bir ekip için "branch" (dal) kullanmak çakışmaları önler. Her gün kodlamaya başlamadan önce ve bitirdikten sonra şu adımları izleyin:

```bash
# SABAH — Çalışmaya başlarken:
git checkout main           # Ana dala geçin
git pull origin main        # En güncel kodu çekin

# Kendi dalınızı oluşturun:
git checkout -b ozellik/canvas-bileşeni   # Kişi A örneği
# veya
git checkout -b ozellik/firebase-baglanti  # Kişi B örneği

# AKŞAM — İşiniz bittiğinde:
git add .                                  # Değişiklikleri ekleyin
git commit -m "Canvas bileşeni: mouse takip eklendi"  # Açıklayıcı mesaj
git push origin ozellik/canvas-bileşeni    # Dalınızı gönderin

# GitHub'da "Pull Request" açın → Diğer kişi inceler → "Merge" eder
```

**Altın Kural:** `main` dalına doğrudan commit atmayın. Her zaman dal oluşturun, Pull Request açın. Bu şekilde birbirinizin kodunu bozmazsınız.

### 4. Görev Dağılımı

İki kişi arasında görevleri şöyle bölmenizi öneriyorum. Bu bölüm bileşen bazlı olduğu için ikisinin çalışması birbirini engellemez; yani paralel ilerleyebilirsiniz.

**Kişi A — "Oyun Motoru" (Frontend Ağırlıklı)**
Bu kişi termogram görsellerinin ekranda gösterilmesi, mouse ile çizim yapılması ve kullanıcı deneyiminin tasarlanmasından sorumlu olacak. Detaylı görevleri:
- `TermogramCanvas.jsx` bileşeni (mouse tracking, çizim mantığı)
- `coordinateMapper.js` (piksel koordinatlarını gerçek sıcaklık/zaman değerine dönüştüren matematik)
- `ImageSelector.jsx` (termogram listesi ve seçim)
- `Tutorial.jsx` (kullanıcı rehberi)
- Genel CSS ve responsive tasarım

**Kişi B — "Veri Altyapısı" (Backend/Veri Ağırlıklı)**
Bu kişi Firebase bağlantısı, kullanıcı girişi, verilerin kaydedilmesi ve dışa aktarılmasından sorumlu olacak. Detaylı görevleri:
- Firebase projesi kurulumu ve yapılandırma
- `config.js`, `auth.js`, `db.js` dosyaları
- Firestore güvenlik kuralları
- `Leaderboard.jsx` (skor tablosu)
- `dataExporter.js` (veriyi CSV/JSON olarak indirme)
- Görsel optimizasyonu (TIF → WebP dönüşümü)

---

## Adım Adım Uygulama Planı (TODO)

Aşağıda her adım için tahmini süre ve hangi kişinin yapacağı belirtilmiştir. Toplam süre yaklaşık 2-3 hafta (yarım gün/gün çalışma temposunda).

### Hafta 1: Temel Altyapı

**Gün 1-2: Proje İskeleti**

- [ ] **[İKİSİ BİRLİKTE]** GitHub reposunu oluşturun ve ikisi de klonlayın.
- [ ] **[İKİSİ BİRLİKTE]** Vite + React projesini başlatın, ilk commit'i yapın.
- [ ] **[Kişi B]** Firebase Console'da yeni proje oluşturun (console.firebase.google.com).
  - Authentication → Sign-in method → "Anonymous" ve "Google" sağlayıcılarını aktifleştirin. Anonim giriş, kullanıcıların kayıt olmadan hemen oynamaya başlamasını sağlar; Google girişi ise isteyen kullanıcıların ilerlemelerini kaydetmesine olanak tanır.
  - Firestore Database → Create database → "Start in production mode" seçin.
- [ ] **[Kişi B]** `src/firebase/config.js` dosyasını oluşturun:

```javascript
// Firebase yapılandırma dosyası
// Bu bilgiler Firebase Console → Project Settings → Your apps kısmından alınır
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIza...",          // Firebase Console'dan kopyalayın
  authDomain: "proje-adi.firebaseapp.com",
  projectId: "proje-adi",
  storageBucket: "proje-adi.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};

// NOT: Bu API anahtarı herkese açıktır ve bu normaldir.
// Güvenlik, Firestore Security Rules ile sağlanır (ileride yazacağız).
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);
```

- [ ] **[Kişi A]** Temel sayfa yapısını oluşturun: Navbar, ana sayfa iskeleti.

**Gün 3-4: Görsel Hazırlığı ve Canvas Temeli**

- [ ] **[Kişi B]** TIF dosyalarını WebP'ye dönüştürme scriptini yazın. WebP formatı TIF'ten yaklaşık 10 kat daha küçüktür ve web'de çok daha hızlı yüklenir:

```bash
#!/bin/bash
# scripts/convert-images.sh
# Kullanım: bash convert-images.sh /kaynak/klasör /hedef/klasör

INPUT_DIR=$1
OUTPUT_DIR=$2
mkdir -p $OUTPUT_DIR

for file in "$INPUT_DIR"/*.tif; do
  filename=$(basename "$file" .tif)
  # Kalite 85 iyi bir denge noktasıdır: görsel detayları korur ama dosya boyutunu düşürür
  cwebp -q 85 "$file" -o "$OUTPUT_DIR/$filename.webp"
  echo "Dönüştürüldü: $filename.webp"
done
```

- [ ] **[Kişi A]** `TermogramCanvas.jsx` bileşeninin ilk versiyonunu yazın. Bu bileşen projenin kalbi olacak. Yapması gerekenler:
  1. Termogram görselini bir HTML Canvas üzerine çizmek
  2. Kullanıcının mouse hareketlerini dinlemek
  3. Mouse basılıyken koordinatları bir diziye kaydetmek
  4. Çizilen çizgiyi kırmızı renkte görselin üzerinde göstermek

```jsx
// TermogramCanvas.jsx — Temel iskelet
// Bu bileşen termogramı gösterir ve kullanıcının mouse ile çizim yapmasını sağlar

import { useRef, useState, useEffect, useCallback } from 'react';

export default function TermogramCanvas({ imageUrl, onTraceComplete }) {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [points, setPoints] = useState([]);       // Toplanan koordinatlar
  const [image, setImage] = useState(null);

  // Görsel yüklendiğinde canvas'a çiz
  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setImage(img);
      const canvas = canvasRef.current;
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
    };
    img.src = imageUrl;
  }, [imageUrl]);

  // Mouse basıldığında çizime başla
  const handleMouseDown = useCallback((e) => {
    setIsDrawing(true);
    const rect = canvasRef.current.getBoundingClientRect();
    // Mouse pozisyonunu canvas koordinatlarına çevir
    // scaleX/scaleY, canvas'ın ekranda küçültülmüş olma durumunu telafi eder
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    setPoints([{ x, y, timestamp: Date.now() }]);
  }, []);

  // Mouse hareket ettikçe noktaları topla ve çiz
  const handleMouseMove = useCallback((e) => {
    if (!isDrawing) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    setPoints(prev => [...prev, { x, y, timestamp: Date.now() }]);

    // Kırmızı çizgi olarak göster (kullanıcı ne çizdiğini görsün)
    const ctx = canvasRef.current.getContext('2d');
    const lastPoint = points[points.length - 1];
    if (lastPoint) {
      ctx.beginPath();
      ctx.moveTo(lastPoint.x, lastPoint.y);
      ctx.lineTo(x, y);
      ctx.strokeStyle = '#FF0000';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [isDrawing, points]);

  // Mouse bırakıldığında çizimi tamamla
  const handleMouseUp = useCallback(() => {
    setIsDrawing(false);
    if (points.length > 10) {  // En az 10 nokta olmalı (çok kısa çizimler geçersiz)
      onTraceComplete(points);
    }
  }, [points, onTraceComplete]);

  return (
    <canvas
      ref={canvasRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      style={{ cursor: 'crosshair', maxWidth: '100%', height: 'auto' }}
    />
  );
}
```

### Hafta 1 Devamı: Koordinat Dönüşümü

**Gün 5-6: Pikselden Gerçek Veriye Dönüşüm**

Bu adım projenin en kritik matematik kısmıdır. Termogramdaki her piksel bir sıcaklık ve zaman değerine karşılık gelir. Bu dönüşümü yapabilmek için kalibrasyon noktalarına ihtiyacınız var.

- [ ] **[Kişi A]** Kalibrasyon sistemi yazın. Her termogram için kullanıcıdan (veya sizin tarafınızdan önceden) dört referans noktası tanımlanmalı:

```javascript
// utils/coordinateMapper.js
// Bu dosya piksel koordinatlarını gerçek fiziksel değerlere dönüştürür

export function createMapper(calibration) {
  // calibration nesnesi şu şekilde tanımlanır:
  // {
  //   topLeft:     { px: {x: 120, y: 50},  value: {time: "1971-08-02T04:00", temp: 40} },
  //   topRight:    { px: {x: 3500, y: 50},  value: {time: "1971-08-09T08:00", temp: 40} },
  //   bottomLeft:  { px: {x: 120, y: 1000}, value: {time: "1971-08-02T04:00", temp: -10} },
  //   bottomRight: { px: {x: 3500, y: 1000}, value: {time: "1971-08-09T08:00", temp: -10} },
  // }
  //
  // Bu dört nokta, termogramdaki ızgara köşelerine karşılık gelir.
  // Piksel koordinatlarını (px) gerçek değerlere (value) eşler.

  const { topLeft, topRight, bottomLeft } = calibration;

  // Piksel aralığı
  const pxWidth = topRight.px.x - topLeft.px.x;
  const pxHeight = bottomLeft.px.y - topLeft.px.y;

  // Zaman aralığı (milisaniye cinsinden)
  const timeStart = new Date(topLeft.value.time).getTime();
  const timeEnd = new Date(topRight.value.time).getTime();
  const timeRange = timeEnd - timeStart;

  // Sıcaklık aralığı
  const tempMax = topLeft.value.temp;     // Üst = yüksek sıcaklık
  const tempMin = bottomLeft.value.temp;  // Alt = düşük sıcaklık
  const tempRange = tempMax - tempMin;

  return function mapPixelToValue(px_x, px_y) {
    // Normalize: pikselin ızgara içindeki oransal konumu (0-1 arası)
    const ratioX = (px_x - topLeft.px.x) / pxWidth;
    const ratioY = (px_y - topLeft.px.y) / pxHeight;

    // Gerçek değerlere dönüştür
    const timestamp = new Date(timeStart + ratioX * timeRange);
    const temperature = tempMax - ratioY * tempRange;  // Y ekseni ters: yukarı = sıcak

    return { timestamp, temperature };
  };
}
```

- [ ] **[Kişi B]** Her termogram görseli için bir metadata (kalibrasyon) JSON dosyası hazırlayın. Bu dosya her görselin zaman aralığını, sıcaklık ölçeğini ve referans piksel koordinatlarını içerecek:

```json
// public/metadata/1971_AG_USTOS-02.json
{
  "id": "1971_AG_USTOS-02",
  "startDate": "1971-08-02",
  "endDate": "1971-08-09",
  "tempMin": -10,
  "tempMax": 40,
  "calibration": {
    "topLeft": { "px": {"x": 120, "y": 50}, "value": {"time": "1971-08-02T04:00", "temp": 40} },
    "topRight": { "px": {"x": 3500, "y": 50}, "value": {"time": "1971-08-09T08:00", "temp": 40} },
    "bottomLeft": { "px": {"x": 120, "y": 1000}, "value": {"time": "1971-08-02T04:00", "temp": -10} },
    "bottomRight": { "px": {"x": 3500, "y": 1000}, "value": {"time": "1971-08-09T08:00", "temp": -10} }
  },
  "status": "pending",
  "difficulty": "easy"
}
```

### Hafta 2: Oyunlaştırma ve Firebase Entegrasyonu

**Gün 7-8: Firebase Veri Kaydetme**

- [ ] **[Kişi B]** Firestore güvenlik kurallarını yazın. Bu kurallar, kimin ne yapabileceğini belirler ve veri güvenliğinizin temelini oluşturur:

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Çizim verileri: Herkes kendi verisini yazabilir, okuyamaz
    // Bu kural, bir kullanıcının başkalarının çizim verisini görmesini engeller
    match /traces/{traceId} {
      allow create: if request.auth != null       // Giriş yapmış olmalı
        && request.resource.data.userId == request.auth.uid  // Kendi ID'si olmalı
        && request.resource.data.points.size() <= 5000;      // Max 5000 nokta (DoS koruması)
      allow read: if request.auth != null
        && resource.data.userId == request.auth.uid;  // Sadece kendi verisini okuyabilir
    }

    // Skor tablosu: Herkes okuyabilir, sadece kendi skorunu yazabilir
    match /leaderboard/{userId} {
      allow read: if true;                              // Skor tablosu herkese açık
      allow write: if request.auth != null
        && request.auth.uid == userId;                  // Sadece kendi skorunu güncelleyebilir
    }

    // Termogram metadata: Sadece okunabilir (siz Firebase Console'dan yönetirsiniz)
    match /termograms/{termogramId} {
      allow read: if true;
      allow write: if false;  // Kimse web'den yazamaz
    }
  }
}
```

- [ ] **[Kişi B]** Veritabanı yazma/okuma fonksiyonlarını oluşturun:

```javascript
// src/firebase/db.js
import { db, auth } from './config';
import {
  collection, addDoc, query, where,
  orderBy, limit, getDocs, serverTimestamp
} from 'firebase/firestore';

// Kullanıcının çizim verisini kaydet
export async function saveTrace(termogramId, points, calibratedData) {
  // calibratedData: coordinateMapper ile dönüştürülmüş sıcaklık/zaman dizisi
  const trace = {
    termogramId,
    userId: auth.currentUser.uid,
    // Ham piksel koordinatları (ileride yeniden kalibrasyon gerekirse lazım olur)
    rawPoints: points.map(p => ({ x: Math.round(p.x), y: Math.round(p.y) })),
    // Dönüştürülmüş değerler
    calibratedData: calibratedData.map(d => ({
      timestamp: d.timestamp.toISOString(),
      temperature: Math.round(d.temperature * 10) / 10  // 1 ondalık basamak yeterli
    })),
    createdAt: serverTimestamp(),
    pointCount: points.length
  };

  const docRef = await addDoc(collection(db, 'traces'), trace);
  return docRef.id;
}

// Skor tablosunu getir (en çok termogram tamamlayan ilk 20 kişi)
export async function getLeaderboard() {
  const q = query(
    collection(db, 'leaderboard'),
    orderBy('completedCount', 'desc'),
    limit(20)
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
}
```

**Gün 9-10: Oyunlaştırma Elementleri**

- [ ] **[Kişi A]** Çizim deneyimini iyileştirin:
  - "Geri al" butonu (son çizimi sil, görseli yeniden yükle)
  - Yakınlaştırma (zoom) özelliği — termogramlar yatay olarak çok geniş olduğundan, bölüm bölüm çizim yapma imkanı sunun
  - Çizim tamamlandığında konfeti veya basit bir animasyon gösterin
  - Çizim hızına göre basit bir skor hesaplayın (hız + kapsanan alan)

- [ ] **[Kişi A]** Tutorial (rehber) bileşenini yazın:
  - İlk kez giren kullanıcıya "Bu termogramda mavi çizgiyi mouse ile takip edin" gibi 3-4 adımlık bir görsel rehber gösterin
  - Örnek bir mini termogram üzerinde pratik yaptırın

- [ ] **[Kişi B]** Leaderboard (skor tablosu) bileşenini yazın:
  - En çok termogram dijitalleştiren kullanıcıları listeleyin
  - Anonim kullanıcılar "Gönüllü #1234" şeklinde görünsün
  - Google ile giriş yapanlar isimlerini gösterebilsin

### Hafta 2 Devamı: Entegrasyon ve Test

**Gün 11-12: Tüm Parçaları Birleştirme**

- [ ] **[İKİSİ BİRLİKTE]** Tüm bileşenleri `App.jsx` içinde birleştirin:

```jsx
// src/App.jsx — Ana uygulama akışı
function App() {
  // Uygulama durumu: hangi ekranda olduğumuz
  // "select" → termogram seç, "trace" → çiz, "result" → sonuç göster
  const [screen, setScreen] = useState('select');
  const [selectedTermogram, setSelectedTermogram] = useState(null);
  const [user, setUser] = useState(null);

  return (
    <div>
      <Navbar user={user} />
      {screen === 'select' && (
        <ImageSelector
          onSelect={(termogram) => {
            setSelectedTermogram(termogram);
            setScreen('trace');
          }}
        />
      )}
      {screen === 'trace' && (
        <TermogramCanvas
          imageUrl={selectedTermogram.imageUrl}
          calibration={selectedTermogram.calibration}
          onTraceComplete={async (points) => {
            // Pikselleri gerçek değerlere dönüştür
            const mapper = createMapper(selectedTermogram.calibration);
            const calibrated = points.map(p => mapper(p.x, p.y));
            // Firebase'e kaydet
            await saveTrace(selectedTermogram.id, points, calibrated);
            setScreen('result');
          }}
        />
      )}
      {screen === 'result' && (
        <div>
          <h2>Tebrikler! Termogram dijitalleştirildi.</h2>
          <Leaderboard />
          <button onClick={() => setScreen('select')}>Bir tane daha yap</button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **[İKİSİ BİRLİKTE]** Uçtan uca test yapın: Termogram seç → Çiz → Kaydet → Skor tablosunda gör.

**Gün 13-14: Yayınlama (Deploy)**

- [ ] **[Kişi B]** GitHub Pages'e deploy edin. `vite.config.js` dosyasına şu ayarı ekleyin:

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/termogram-digitizer/',  // GitHub repo adıyla aynı olmalı
});
```

- [ ] **[Kişi B]** GitHub Actions ile otomatik deploy ayarlayın. Repo'da `.github/workflows/deploy.yml` dosyası oluşturun:

```yaml
# .github/workflows/deploy.yml
# Bu dosya, main dalına her push yapıldığında siteyi otomatik olarak yeniden yayınlar

name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci            # Bağımlılıkları kur
      - run: npm run build     # Projeyi derle
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist            # Vite'ın çıktı klasörü
      - uses: actions/deploy-pages@v4
```

- [ ] **[Kişi B]** GitHub'da Settings → Pages → Source: "GitHub Actions" seçin.

Artık siteniz `https://KULLANICI_ADI.github.io/termogram-digitizer/` adresinde yayında olacak.

---

## Güvenlik Kontrol Listesi

Güvenlik endişeniz için aşağıdaki önlemleri almanız yeterli olacaktır. Bu liste, bir hackathon projesi için uygun seviyede koruma sağlar.

### Veri Güvenliği
- [x] Firebase Security Rules yazıldı (yukarıda). Kullanıcılar sadece kendi verilerine erişebilir.
- [ ] Firebase Console'da "App Check" özelliğini aktifleştirin. Bu özellik, API'nize sadece sizin sitenizden istek gelmesini sağlar; başka siteler Firebase anahtarınızı kullanamaz.
- [ ] Rate limiting: Firestore kurallarında nokta sayısını sınırladık (5000 max). Bu, birinin devasa veri göndererek sistemi doldurmasını engeller.
- [ ] Hassas bilgi (şifre, kişisel veri) toplamıyorsunuz; anonim giriş yeterli. Sadece çizim koordinatları kaydediliyor.

### Kod Güvenliği
- [ ] Firebase API anahtarları frontend'de bulunacak ve bu normaldir. Firebase'de güvenlik, API anahtarıyla değil Security Rules ile sağlanır. Yine de `.env` dosyası kullanarak anahtarları koddan ayırmak iyi pratiktir:

```bash
# .env dosyası (bu dosya .gitignore'a eklenmeli)
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_PROJECT_ID=proje-adi
```

```javascript
// config.js'te böyle kullanın:
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  // ...
};
```

### Performans
- [ ] Görselleri WebP formatına çevirin (TIF'ten 10x daha küçük).
- [ ] Görselleri "lazy loading" ile yükleyin (ekranda görünene kadar yüklemeyin).
- [ ] Canvas üzerinde çizim sırasında `requestAnimationFrame` kullanın (akıcı performans için).

---

## Veri Dışa Aktarım

Hackathon jürisine sunmak ve kendi analizleriniz için toplanan veriyi CSV olarak indirmeniz gerekecek.

```javascript
// utils/dataExporter.js
// Bu fonksiyon Firestore'daki çizim verilerini CSV'ye dönüştürür

export function exportToCSV(traces) {
  // CSV başlık satırı
  const header = 'termogram_id,user_id,timestamp,temperature_celsius\n';

  const rows = traces.flatMap(trace =>
    trace.calibratedData.map(point =>
      `${trace.termogramId},${trace.userId},${point.timestamp},${point.temperature}`
    )
  );

  const csv = header + rows.join('\n');

  // Tarayıcıda dosya olarak indir
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'termogram_data.csv';
  a.click();
}
```

---

## Hızlı Başlangıç Özeti

Projeyi sıfırdan başlatmak için tam komut dizisi:

```bash
# 1. Repo oluştur (GitHub'da) ve klonla
git clone https://github.com/KULLANICI/termogram-digitizer.git
cd termogram-digitizer

# 2. Vite + React projesi oluştur
npm create vite@latest . -- --template react
npm install
npm install firebase

# 3. Klasör yapısını oluştur
mkdir -p src/components src/firebase src/utils src/styles public/images public/metadata scripts

# 4. Geliştirme sunucusunu başlat
npm run dev
# Tarayıcıda http://localhost:5173 adresini açın

# 5. İlk commit
git add .
git commit -m "Proje iskeleti oluşturuldu"
git push origin main
```

---

## Hackathon Sunumu İçin İpuçları

Jüriye sunumda şu noktaları vurgulamanızı öneriyorum:

1. **"Citizen Science" yaklaşımı:** Profesyonel OCR/CV yöntemleri yerine insan gücünü oyunlaştırarak kullandınız. Bu, Zooniverse gibi bilimsel projelere benzer bir yaklaşım ve hackathon temasına çok uygun.

2. **Doğrulama mekanizması:** Aynı termogramı birden fazla kişiye çizdirerek verileri çapraz doğrulayabilirsiniz. İki farklı kişinin çizimi birbirine ne kadar yakınsa veri o kadar güvenilir demektir.

3. **Ölçeklenebilirlik:** 4 GB'lık görsel veriyi bir avuç insan yerine yüzlerce gönüllüyle işleyebilirsiniz. Bir viral tweet ile binlerce kişiye ulaşabilirsiniz.

4. **Veri kalitesi:** Mouse çizimleri, piksel piksel OCR'dan daha "insan dostu" bir doğruluk sağlar; çünkü insan gözü bozuk, soluk veya üst üste binmiş çizgileri OCR'dan çok daha iyi ayırt edebilir.
