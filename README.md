# 🌡️ Termogram Dijitalleştirici

> Kandilli Meteoroloji Laboratuvarı'nın 1911–2005 yılları arasında kaydettiği ~35.000 termogram arşivini, gönüllü kullanıcıların katılımıyla dijitalleştiren bir vatandaş bilimi platformu.

**[🚀 Canlı Demo](https://berkkbalci.github.io/termogram-digitizer/)** &nbsp;·&nbsp; **[GitHub](https://github.com/berkkbalci/termogram-digitizer)**

---

## Neden Bu Proje?

İstanbul'un yaklaşık 100 yıllık iklim geçmişi kâğıt üzerinde hapsolmuş durumda. Bu termogramlar, sıcaklık değişimlerini dakika dakika kaydeden analog cihazların çıktılarıdır ve iklim araştırmaları için son derece değerli birincil veriler içerir.

**Sorun:** OCR ve Computer Vision yöntemleri bu kayıtlar için güvenilir çalışmıyor. Solmuş mürekkep, yırtılmış kâğıt, üst üste binen çizgiler ve ızgara çizgileriyle iç içe geçen eğriler otomatik algoritmaları yanıltıyor.

**Çözüm:** İnsan gözü. Oyunlaştırma sayesinde bu insan gücünü ölçeklenebilir hale getirdik.

---

## Nasıl Çalışır?

1. **Giriş** — Kullanıcı bir kullanıcı adı girerek platforma katılır (hesap gerekmez)
2. **Çizim** — Sistem, henüz tamamlanmamış bir termogram görseli sunar; kullanıcı sol tıkla basılı tutarak sıcaklık eğrisini soldan sağa takip eder
3. **Kalibrasyon** — `Ctrl + tık` ile grafik üzerindeki bilinen sıcaklık değerlerine referans noktaları eklenir; sistem bu noktaları kullanarak piksel koordinatlarını gerçek sıcaklık/zaman verilerine dönüştürür
4. **Gönderim** — Çizim Firebase'e kaydedilir, XP kazanılır ve sistem otomatik olarak yeni bir termogram getirir

---

## Oyunlaştırma Sistemi

Gönüllüleri motive etmek ve veri akışını sürdürmek için tam bir ilerleme sistemi kuruldu:

| Özellik | Detay |
|---|---|
| **Temel XP** | Her çizim için 50 XP |
| **Referans Bonusu** | 2+ referans noktası eklenirse +20 XP |
| **Günlük Seri** | Ardışık gün sayısına göre 1×–2× çarpan (10. günde maksimum) |
| **Seviye Sistemi** | 10 seviye, 0 XP'den 5.000 XP'ye kadar |
| **Liderboard** | En çok XP kazanan 10 kullanıcı |

---

## Veri Kalitesi: Çapraz Doğrulama

Her termogram **3 farklı gönüllü** tarafından bağımsız olarak çizilir. Üç çizim birbirine ne kadar yakınsa, dijitalleştirilen veri o kadar güvenilirdir.

- Medyan tabanlı aykırı değer tespiti uygulanır
- Her iz için MAE ve z-skoru hesaplanır
- Ortalama z-skoru 2.5'i geçen izler otomatik olarak işaretlenir

Bu yaklaşım, Zooniverse ve Galaxy Zoo gibi başarılı vatandaş bilimi projelerinde kullanılan yöntemle örtüşmektedir.

---

## Teknoloji

| Katman | Teknoloji |
|---|---|
| Frontend | Vanilla HTML5 / CSS3 / JavaScript (framework yok) |
| Çizim Motoru | HTML5 Canvas API |
| Veritabanı | Google Firestore |
| Kimlik Doğrulama | Firebase Anonymous Auth |
| Hosting | GitHub Pages |
| Görsel İşleme | Python (Pillow) — TIF → PNG dönüştürme |

Sunucu tarafında çalışan hiçbir kod yoktur. Tüm uygulama tek bir `index.html` dosyasıdır.

---

## Proje Yapısı

```
termogram-digitizer/
├── index.html              → Ana uygulama
├── admin.html              → Çapraz doğrulama analiz paneli
├── images/
│   ├── termogram/          → Sıcaklık kayıtları
│   ├── barograf/           → Hava basıncı kayıtları
│   ├── nem/                → Nem kayıtları
│   └── aktinograf/         → Güneş radyasyonu kayıtları
├── scripts/
│   ├── seed-firestore.html → Firestore'a görsel havuzunu yükleyen tek seferlik araç
│   └── tif_to_png.py       → TIF → PNG toplu dönüştürücü
└── README.md
```

---

## Veri Formatı

Firestore'da üç koleksiyon kullanılmaktadır.

**`termograms`** — Her termogram görseli için bir belge:
```json
{
  "imageFile": "images/termogram/1981_SUBAT-13.png",
  "dataType": "termogram",
  "startDate": "1981-02-13T00:00:00Z",
  "endDate": "1981-02-14T00:00:00Z",
  "tempMin": 0,
  "tempMax": 40,
  "traceCount": 1,
  "maxTraces": 3,
  "status": "active"
}
```

**`traces`** — Her kullanıcı çizimi için bir belge:
```json
{
  "termogramId": "abc123",
  "userId": "anon-xyz",
  "userName": "berk",
  "pointCount": 842,
  "referencePoints": [...],
  "calibratedData": [
    { "timestamp": "1981-02-13T08:30:00Z", "temperature": 6.2 }
  ]
}
```

**`users`** — Oyunlaştırma verileri:
```json
{
  "userName": "berk",
  "totalXP": 1340,
  "level": 5,
  "tracesCompleted": 22,
  "streakDays": 4,
  "lastActiveDate": "2026-03-26"
}
```

Ham piksel koordinatları da saklanır; ileride yeniden kalibrasyon gerekirse mevcut veriler işlenebilir.

---

## Kurulum

### Yerel Geliştirme

```bash
git clone https://github.com/berkkbalci/termogram-digitizer.git
cd termogram-digitizer
python3 -m http.server 8000
```

Tarayıcıda `http://localhost:8000` adresini açın.

> `file:///` protokolü ile doğrudan açmak Firebase SDK'sının ve görsellerin düzgün çalışmamasına neden olabilir.

### Firebase Kurulumu (Sıfırdan)

1. [Firebase Console](https://console.firebase.google.com)'da yeni proje oluşturun
2. **Authentication → Anonymous** sign-in yöntemini aktifleştirin
3. **Firestore Database** oluşturun
4. Proje ayarlarından web uygulaması ekleyin, `firebaseConfig` değerlerini `index.html`'deki ilgili alana yapıştırın
5. `scripts/seed-firestore.html` dosyasındaki config değerlerini güncelleyip tarayıcıda açın ve "Yükle" butonuna basın

### Görsel Dönüştürme

```bash
pip install Pillow
python3 scripts/tif_to_png.py
```

---

## Admin Paneli

`admin.html` dosyası yetkili kullanıcılar için bir analiz arayüzü sunar:

- Çapraz doğrulama sonuçlarını görüntüleme
- İz kalitesi metrikleri (MAE, z-skoru)
- Liderboard yönetimi
- Puanlama formülü detayları

---

## Katkıda Bulunanlar

Bu proje **Boğaziçi Meteoroloji Hackathonu 2026** kapsamında geliştirilmiştir.

**Geliştirme:** Berk Balcı, Burak Ceylan
**Danışman:** Birkan Yılmaz
