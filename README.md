# 🌡️ Termogram Dijitalleştirici

Kandilli Meteoroloji Laboratuvarı İklim İstasyonu'nun 1911–2005 yılları arasında kaydedilmiş tarihsel termogram verilerini, gönüllü kullanıcıların katılımıyla dijitalleştirmeyi amaçlayan bir citizen science (vatandaş bilimi) platformu.

Bu proje, **Boğaziçi Meteoroloji Hackathonu'nda**  geliştirilmiştir.

## Proje Hakkında

Termogramlar, sıcaklık değişimlerini sürekli olarak kâğıt üzerine kaydeden analog cihazların ürettiği grafiklerdir. Yaklaşık 100 yıllık bu arşiv, iklim araştırmaları için son derece değerli bir veri kaynağıdır.

Bu platform, termogram görsellerindeki sıcaklık eğrilerini dijitalleştirmek için oyunlaştırma (gamification) yaklaşımını kullanır. Kullanıcılar, ekranlarında gördükleri termogram üzerindeki mavi sıcaklık çizgisini mouse ile takip eder. Bu takip sırasında toplanan piksel koordinatları, kalibrasyon verileri kullanılarak gerçek sıcaklık (°C) ve zaman (tarih/saat) değerlerine dönüştürülür ve veritabanına kaydedilir.

### Neden İnsan Gücü?

OCR ve Computer Vision teknikleri düz metinler için oldukça başarılı olsa da, termogram verileri bu yöntemler için ciddi zorluklar içerir. Solmuş mürekkep, yırtılmış kâğıt, üst üste binmiş çizgiler ve ızgara çizgileriyle karışan eğriler gibi sorunlar, otomatik algoritmaların güvenilirliğini düşürür. İnsan gözü ise bu tür görsel belirsizlikleri çözmekte çok daha başarılıdır. Oyunlaştırma sayesinde bu insan gücü ölçeklenebilir hale getirilmiştir.

### Çapraz Doğrulama

Veri kalitesini garanti altına almak için her termogram **3 farklı gönüllü** tarafından bağımsız olarak çizilir. Üç çizim birbirine ne kadar yakınsa, dijitalleştirilen veri o kadar güvenilir kabul edilir. Bu yaklaşım, Zooniverse ve Galaxy Zoo gibi başarılı citizen science projelerinde de kullanılan bir yöntemdir.

## Nasıl Çalışır?

Kullanıcı siteye girdiğinde bir isim girerek başlar. Sistem, görsel havuzundan henüz tamamlanmamış ve bu kullanıcının daha önce çizmediği bir termogramı rastgele seçerek ekrana getirir. Kullanıcı mouse'un sol tuşuna basılı tutarak termogramdaki mavi sıcaklık eğrisini soldan sağa takip eder. Takip sırasında çizilen kırmızı çizgi ekranda anlık olarak görünür. Çizim tamamlandığında "Gönder" butonuna basılır ve toplanan koordinatlar otomatik olarak sıcaklık/zaman değerlerine dönüştürülerek Firebase veritabanına kaydedilir. Ardından sistem otomatik olarak yeni bir termogram getirir.

## Teknoloji Altyapısı

Proje tamamen statik bir mimari üzerine kurulmuştur. Sunucu tarafında çalışan bir kod bulunmaz, bu sayede SQL injection gibi sunucu taraflı saldırı vektörleri baştan elenir.

**Frontend:** Tek bir `index.html` dosyası içinde HTML, CSS ve vanilla JavaScript kullanılmıştır. Herhangi bir framework veya build aracı gerektirmez. Termogram görselleri HTML5 Canvas API kullanılarak gösterilir ve mouse olayları ile piksel koordinatları toplanır.

**Backend:** Google Firebase platformu kullanılmaktadır. Firestore veritabanı termogram metadata'sını ve çizim verilerini saklar. Firebase Authentication ile anonim kullanıcı girişi sağlanır. Güvenlik, Firestore Security Rules ile kontrol edilir.

**Hosting:** GitHub Pages üzerinden ücretsiz olarak sunulmaktadır.

## Proje Yapısı

```
termogram-digitizer/
├── index.html              → Ana uygulama (tek dosya)
├── images/                 → Termogram görselleri (PNG formatında)
│   ├── 1976_MART-01.png
│   ├── 1977_MAYIS-03.png
│   ├── 1977_NòSAN-04.png
│   ├── 1977_NòSAN-25.png
│   ├── 1981_ûUBAT-13.png
│   ├── 1985_EYLöL-01.png
│   ├── 1985_EYLöL-17.png
│   ├── 1991_ûUBAT-05.png
│   ├── 1998_MART-05.png
│   └── 1998_MART-16.png
├── scripts/
│   └── seed-firestore.html → Firestore'a görsel havuzunu yükleyen tek seferlik araç
└── README.md
```

## Kurulum ve Çalıştırma

### Gereksinimler

Projeyi yerel ortamda çalıştırmak için yalnızca bir web tarayıcısı ve basit bir HTTP sunucusu gereklidir. Herhangi bir paket yüklemeye gerek yoktur.

### Yerel Geliştirme

Repoyu klonladıktan sonra proje klasöründe bir yerel sunucu başlatmanız yeterlidir. Dosyayı doğrudan `file:///` protokolü ile açmak, Firebase SDK'sının ve görsellerin düzgün çalışmamasına neden olabilir.

```bash
git clone https://github.com/berkkbalci/termogram-digitizer.git
cd termogram-digitizer
python3 -m http.server 8000
```

Ardından tarayıcıda `http://localhost:8000` adresini açın.

### Firebase Kurulumu (Yeni Bir Ortam İçin)

Projeyi sıfırdan kurmak isteyenler için Firebase tarafındaki adımlar şu şekildedir. Önce Firebase Console'da yeni bir proje oluşturun. Authentication bölümünde Anonymous sign-in yöntemini aktifleştirin. Firestore Database oluşturun. Proje ayarlarından web uygulaması ekleyip `firebaseConfig` değerlerini `index.html`'deki ilgili alana yapıştırın. Son olarak `scripts/seed-firestore.html` dosyasındaki config değerlerini de güncelleyip bu dosyayı tarayıcıda açarak "Yükle" butonuna basın. Bu işlem termogram metadata'sını Firestore'a yükleyecektir.

## Veri Formatı

Firestore'da iki koleksiyon kullanılmaktadır.

**`termograms` koleksiyonu** her termogram görseli için bir belge içerir. Bu belgede görselin dosya yolu, tarih aralığı, sıcaklık ölçeği, kalibrasyon için ızgara köşelerinin piksel koordinatları, kaç kez çizildiği ve tamamlanıp tamamlanmadığı bilgisi bulunur.

**`traces` koleksiyonu** her çizim işlemi için bir belge içerir. Bu belgede hangi termogramın çizildiği, hangi kullanıcının çizdiği, ham piksel koordinatları (ileride yeniden kalibrasyon gerekirse diye) ve kalibre edilmiş sıcaklık/zaman değerleri saklanır.

Kalibre edilmiş veriler şu formatta kaydedilir:

```json
{
  "timestamp": "1981-02-13T14:30:00.000Z",
  "temperature": 18.3
}
```

## Katkıda Bulunanlar

Bu proje Meteoroloji Hackathon 2026 kapsamında **Berk Balcı ve Burak Ceylan tarafından Birkan Yılmaz hocamızın katkılarıyla** geliştirilmiştir.
