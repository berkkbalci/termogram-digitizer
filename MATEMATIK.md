# Termogram Dijitalleştirici — Matematiksel ve İstatistiksel Yöntemler

Bu belge sistemin tüm matematiksel hesaplamalarını kaynak kod referanslarıyla birlikte açıklamaktadır.

---

## 1. Koordinat Sistemi ve Piksel-Değer Dönüşümü

### 1.1 Piksel Koordinat Uzayı

Her görsel için iki koordinat uzayı vardır:

- **CSS piksel uzayı**: ekranda görünen boyut (telefon ekranında ~375 px genişlik)
- **Görsel piksel uzayı**: orijinal tarama çözünürlüğü (örn. barograf: 5019 × 2046 px)

Kullanıcı parmağını veya mouseunu hareket ettirdiğinde koordinatlar şu dönüşümle görsel piksel uzayına çevrilir:

```
x_görsel = (x_css - rect.left) × (canvas.width / rect.width)
y_görsel = (y_css - rect.top)  × (canvas.height / rect.height)
```

Tüm `rawPoints`, `referencePoints` ve grid koordinatları **görsel piksel uzayında** saklanır. Bu sayede farklı ekran boyutlarına sahip cihazlardaki çizimler birbiriyle kıyaslanabilir.

### 1.2 Grid Koordinatları ve Ölçek

Her termogram kaydında fiziksel ölçüm aralığını piksele bağlayan dört sabit vardır:

| Değişken | Anlam |
|---|---|
| `gridLeft`, `gridRight` | Zaman ekseninin yatay piksel sınırları |
| `gridTop` | Maksimum değere karşılık gelen y pikseli (üstte) |
| `gridBottom` | Minimum değere karşılık gelen y pikseli (altta) |
| `tempMin`, `tempMax` | Fiziksel değer aralığı (°C, mbar, cal/cm²·min, %) |

Bu değerler **piksel analizi** ile elde edilmiştir: her görsel için Python/PIL ile yatay ve dikey çizgilerin piksel yoğunluğu hesaplanmış, major gridline konumları tespit edilmiştir.

**Örnek — Barograf (5019 × 2046 px):**
- Major yatay çizgiler: y = 683, 1040, 1398, 1757 → aralık ≈ 357 px = 20 mbar
- Ölçek: 1790 px / 100 mbar = **17.9 px/mbar**
- 1000 mbar → y = 1040

---

## 2. Kalibrasyon (Piksel y → Fiziksel Değer)

### 2.1 Yöntem A: Grid Doğrusal Enterpolasyonu (Fallback)

Referans nokta kalibrasyonu geçersizse veya yoksa kullanılır:

```
oran  = (y - gridTop) / (gridBottom - gridTop)       ∈ [0, 1]
değer = tempMax − oran × (tempMax − tempMin)
```

`y = gridTop` → `değer = tempMax` (üst = maksimum)
`y = gridBottom` → `değer = tempMin` (alt = minimum)

**Nem grafiği istisnası**: `tempMin = 100`, `tempMax = 0` olarak tanımlanmıştır; bu sayede üst = 0%, alt = 100% olmaktadır (yani oran formülü tersten çalışır, sabit kodlama gerekmez).

Son olarak değer, ilan edilen aralığa sıkıştırılır:

```
değer = clamp(değer, min(tempMin, tempMax), max(tempMin, tempMax))
```

### 2.2 Yöntem B: Referans Noktalarından Regresyon

Kullanıcı, grafiğin tanıdığı noktalarına tıklayıp fiziksel değer girer. Her nokta `(y_piksel, değer)` çifti oluşturur. Bu çiftlerden **basit doğrusal regresyon** yapılır:

```
değer = a × y_piksel + b
```

**Regresyon katsayıları** (En Küçük Kareler):

```
a = (n · Σ(yᵢ · vᵢ) − Σyᵢ · Σvᵢ) / (n · Σyᵢ² − (Σyᵢ)²)

b = (Σvᵢ − a · Σyᵢ) / n
```

### 2.3 Regresyon Kalitesi: R² Katsayısı

Kalibrasyonun ne kadar güvenilir olduğu R² ile ölçülür:

```
SS_res = Σ (vᵢ − (a·yᵢ + b))²        (artık kareler toplamı)
SS_tot = Σ (vᵢ − v̄)²                  (toplam varyans)

R² = 1 − SS_res / SS_tot              ∈ (−∞, 1]
```

R² = 1 → mükemmel fit, R² = 0 → yatay çizgi kadar bilgisiz, R² < 0 → fit berbat.

**Eşik**: `R² ≥ 0.75` → regresyon kabul edilir; düşükse grid fallback kullanılır.

### 2.4 Sağlamlık Filtreleri (Kötü Kalibrasyonu Reddetme)

Referans regresyonu kabul edilmeden önce iki kontrol uygulanır:

**Kontrol 1 — Eğim Oranı:**

Beklenen fiziksel eğim:
```
a_beklenen = (tempMin − tempMax) / (gridBottom − gridTop)
```

Gerçek regresyon eğiminin beklentiyle oranı:
```
oran = a / a_beklenen
```

`0.1 ≤ oran ≤ 10` değilse → **kalibrasyon reddedilir, grid fallback kullanılır.**

*Neden gerekli?* Kullanıcı iki referans noktasını birbirine çok yakın (örn. 8 piksel arayla) fakat farklı değerlerle (1010 ve 1005 mbar) işaretlediğinde eğim 10× yanlış çıkabilir.

**Kontrol 2 — Orta Nokta Tahmini:**

Grid'in y ortasındaki değer tahmini beklenen aralığın ±%50'si içinde olmalı:

```
y_orta     = (gridTop + gridBottom) / 2
tahmin     = a × y_orta + b
aralık     = |tempMax − tempMin|

lo = min(tempMin, tempMax) − 0.5 × aralık
hi = max(tempMin, tempMax) + 0.5 × aralık
```

`tahmin ∉ [lo, hi]` → **kalibrasyon reddedilir.**

### 2.5 MAD Tabanlı Aykırı Referans Filtresi (index.html)

Kullanıcının kendi referans noktaları arasında aykırı olanları atmak için:

```
medY = median(yᵢ)        medV = median(vᵢ)
dᵢ  = |yᵢ − medY| + |vᵢ − medV|
MAD = median(dᵢ)

nokta_skoru = dᵢ / MAD
```

`nokta_skoru > 3.5` → nokta regresyondan çıkarılır.

---

## 3. Ortalama Eğri Hesabı

### 3.1 x Ekseni Boyunca Medyan Enterpolasyonu

Tüm izlerin ortak bir zaman ekseni (x) üzerinde ortalanması için:

1. Her x konumunda (`adım = 5 px`), izlerden **doğrusal enterpolasyon** ile y değeri alınır.
2. O x konumunda en az `⌈n/2⌉` iz veri sağlamalıdır (yarısından azsa atlanır).
3. Toplanan y değerlerinin **medyanı** alınır:

```
x ∈ [x_min, x_max],  adım = 5 px
y_ort(x) = median({ interpolate(iz_k, x) | iz_k veri sağlıyorsa })
```

**Neden medyan, ortalama değil?**
Medyan, kötü çizilen izlerin ortalamayı sürüklemesini engeller. Bir kullanıcı eğriyi ters çizse bile medyan, çoğunluğa yakın kalır.

### 3.2 Doğrusal Enterpolasyon

İki nokta arasındaki ara değer:

```
y = y₁ + ((x − x₁) / (x₂ − x₁)) × (y₂ − y₁)
```

### 3.3 Hareketli Ortalama Pürüzsüzleştirme

Ortalama eğri üzerindeki titreşimi gidermek için pencere boyutu 7 olan simetrik hareketli ortalama:

```
ŷᵢ = (1 / |pencere|) × Σ yⱼ,    j ∈ [i−3, i+3] ∩ [0, N−1]
```

Uçlarda pencere daraltılarak kenarlardaki değerler de hesaplanır.

---

## 4. Aykırı İz Tespiti

### 4.1 Kalite Filtresi

İzin ortalama hesabına dahil edilmesi için iki ön koşul:

```
nokta_sayısı ≥ 30
kapsama_oranı = (x_max − x_min)_iz / (x_max − x_min)_global ≥ 0.10
```

Bu iki koşulu sağlamayan izler **doğrudan aykırı** sayılır.

### 4.2 IQR Tabanlı Aykırı Tespiti

Her iz için ortalama eğriye olan **MAE** (Ortalama Mutlak Hata) hesaplanır:

```
MAE_k = (1/m) × Σ |y_iz_k(xᵢ) − y_ort(xᵢ)|
```

Tüm izlerin MAE değerleri sıralanarak çeyrekler hesaplanır:

```
Q1 = MAE[⌊n × 0.25⌋]
Q3 = MAE[⌊n × 0.75⌋]
IQR = Q3 − Q1
```

Üst eşik:

```
çarpan = 3.0    eğer n < 8
çarpan = 1.5    eğer n ≥ 8

eşik = Q3 + çarpan × IQR
```

`MAE_k > eşik` → iz aykırı sayılır.

**Neden n < 8 için 3.0 çarpanı?**
Az veriyle IQR'ın varyansı yüksektir; daha dar eşik, iyi izleri yanlışlıkla aykırı sayabilir.

**Neden z-skor değil?**
Z-skor, normal dağılım varsayar ve tek bir aykırı değer standart sapmayı şişirebilir. IQR bu etkiye karşı dirençlidir.

---

## 5. Güven Bandı

Her x konumunda, aykırı olmayan izlerin y değerlerinden IQR hesaplanır:

```
bant_üst(x)  = Q1(y_değerleri)     (düşük quartile = "üstteki" sınır)
bant_alt(x)  = Q3(y_değerleri)     (yüksek quartile = "alttaki" sınır)

güven(x)     = max(0, 1 − IQR(x) / eşik)
eşik         = canvas.height × 0.10
```

Güven bandı görsel olarak yarı saydam alanda gösterilir: dar bant = yüksek güven = sarı-yeşil; geniş bant = düşük güven = koyu.

---

## 6. Puanlama: Bırak-Bir-Dışarıda (Leave-One-Out)

### 6.1 Sapma Ölçütleri

Her iz için referans eğrisine olan **MAE** ve **maksimum sapma** hesaplanır:

```
MAE    = (1/m) × Σ |y_iz(xᵢ) − y_ref(xᵢ)|      (ortalama mutlak hata)
maxDev = max{ |y_iz(xᵢ) − y_ref(xᵢ)| }          (en yüksek anlık sapma)
```

### 6.2 Bırak-Bir-Dışarıda Yöntemi

Her kişi, **kendisi hariç** diğer izlerin ortalamasıyla kıyaslanır:

```
ref_k = ortalama_eğri({ iz_j | j ≠ k, j aykırı değil })
MAE_k = deviation(iz_k, ref_k).mae
```

Bu yöntem, olağandışı iyi bir çizimin ortalama eğrisini kendine çekmesini ve yapay yüksek puan almasını önler.

### 6.3 Puan Hesabı

Maksimum kabul edilebilir sapma:

```
max_kabul = (gridBottom − gridTop) × 0.08     (grid yüksekliğinin %8'i)
```

Ham puan (0–10):

```
puan = max(0,  10 × (1 − MAE_k / max_kabul))
```

**Yorumlama**: MAE = 0 → 10 puan, MAE = max_kabul → 0 puan, MAE > max_kabul → 0 puan.

---

## 7. Kırpılmış Ortalama (Sıralama İçin)

Sıralama tablosundaki nihai ortalama eğrisi için en kötü %15'lik dilim çıkarılır:

```
kırpma_sayısı = max(1, ⌊n × 0.15⌋)
sırala MAE değerlerine göre (artan)
koru: ilk (n − kırpma_sayısı) iz
```

Bu sayede aşırı kötü çizimler, sıralamanın kullandığı referans eğrisini bozmaz.

---

## 8. Çizim Güven Değerlendirmesi

Bir çizim Firestore'a kaydedilmeden önce kalitesi dört kritere göre değerlendirilir:

| Kriter | Koşul |
|---|---|
| Yeterli nokta | `nokta_sayısı ≥ 120` |
| Alan kapsamı | `kapsama_oranı ≥ 0.45` (grafiğin ≥ %45'ini kapsıyor) |
| Nokta yoğunluğu | `yoğunluk ≥ 0.03 nokta/px` |
| Kalibrasyon | Regresyon: `R² ≥ 0.75` ve `≥ 2 ref nokta` **VEYA** Grid fallback + kapsama |

Tüm koşullar sağlanıyorsa iz `isConfident = true` olarak işaretlenir ve termogramın `traceCount` sayacı artırılır. Güvensiz izler Firestore'a yine kaydedilir (araştırma için) fakat sayaca eklenmez.

---

## 9. XP ve Seviye Sistemi

### 9.1 XP Hesabı

Her başarılı çizimden sonra:

```
temelXP = 50
refBonus = 20     (≥ 2 referans nokta verilmişse)

streakÇarpanı = min(1 + streakGün × 0.1, 2.0)

xpKazanılan = round((temelXP + refBonus) × streakÇarpanı)
```

**Streak çarpanı**: 1 gün → 1.1×, 5 gün → 1.5×, 10 gün → 2.0× (tavan).

### 9.2 Seviye Eşikleri

| Seviye | Gerekli XP |
|---|---|
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

Seviye belirleme: XP'nin aştığı en yüksek eşiğin bir fazlası.

---

## 10. Boru Hattı Özeti

Bir kullanıcının çizimi gönderildiğinde sistemin uyguladığı adımlar sırasıyla:

```
1. Kullanıcı çizer           → rawPoints (x, y piksel)
2. Kalibrasyon modeli        → referans regresyon veya grid fallback
3. calibratedData            → her piksel-x için (zaman, fiziksel değer) çifti
4. Güven değerlendirmesi     → isConfident?
5. Firestore'a kaydet        → traces koleksiyonu

Admin panelinde:
6. Kalite filtresi           → nokta sayısı / kapsama kontrolü
7. İlk ortalama              → medyan enterpolasyonu (aykırı dahil)
8. IQR outlier tespiti       → aykırı bayrakları
9. Temizlenmiş ortalama      → aykırısız medyan + hareketli ortalama
10. Leave-one-out puanlama   → her kişi kendisi hariç ortalamayla kıyaslanır
11. Güven bandı              → IQR tabanlı ±bant
12. Referans kalibrasyonu    → regresyon + eğim/orta-nokta sağlamlık kontrolü
13. Tooltip değeri           → referans kalibrasyon veya grid fallback
```

---

## 11. Grid Koordinatlarının Piksel Analizi ile Belirlenmesi

Grid sınırları elle ölçülmemiş, Python PIL + NumPy ile otomatik tespit edilmiştir:

```python
gray = np.mean(arr, axis=2)        # RGB → gri ton
row_dark = np.sum(gray < 120, axis=1)   # her satırdaki koyu piksel sayısı
```

Yüksek koyu piksel yoğunluğuna sahip satırlar major yatay çizgilerdir. Sütunlar için aynı işlem uygulanarak dikey sınırlar bulunur.

**Doğrulama örneği — Barograf:**

```
Tespit edilen major çizgiler: y = 683, 1040, 1398, 1757
Aralık: ~357 px
1000 mbar etiketi y ≈ 1000 pikselinde → 1000 mbar çizgisi y = 1040
Ölçek: 357 px / 20 mbar = 17.85 px/mbar ≈ 17.9 px/mbar
```

**Aktinograf:**

```
Tespit edilen major çizgiler: y = 130, 324, 517, 709, 901
Aralık: ~193 px = 0.5 cal/cm²·min
Üst (y=130) → 2.0 cal/cm²·min, Alt (y=901) → 0.0 cal/cm²·min
```
