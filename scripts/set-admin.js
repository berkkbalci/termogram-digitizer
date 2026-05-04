// Tek seferlik kullanım: Bir Firebase Auth kullanıcısına `admin: true` custom claim atar.
//
// Hazırlık:
//   1) Firebase Console → Authentication → Sign-in method → Email/Password etkinleştir.
//   2) Authentication → Users → kendinize email/password ile bir hesap ekleyin.
//      (Bu hesabın UID'sini buraya kopyalayacaksınız.)
//   3) Project Settings → Service accounts → "Generate new private key".
//      İndirilen JSON'u proje köküne `serviceAccountKey.json` olarak kaydedin.
//      DİKKAT: Bu dosyayı asla commit etmeyin. .gitignore'a eklendiğinden emin olun.
//   4) `npm install firebase-admin` (proje kökünde).
//
// Çalıştırma:
//   node scripts/set-admin.js <UID>
//
// Sonra: admin.html'de bu hesapla giriş yapın. signInWithEmailAndPassword sonrası
// getIdTokenResult(true) ile claim güncel okunur.

const admin = require('firebase-admin');
const path = require('path');

const serviceAccount = require(path.resolve(__dirname, '..', 'serviceAccountKey.json'));

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

const uid = process.argv[2];
if (!uid) {
  console.error('Kullanım: node scripts/set-admin.js <UID>');
  process.exit(1);
}

admin.auth().setCustomUserClaims(uid, { admin: true })
  .then(() => admin.auth().getUser(uid))
  .then((user) => {
    console.log(`✅ ${user.email || uid} kullanıcısına admin claim atandı.`);
    console.log('   Claim güncellenmesi için kullanıcı bir kez logout/login yapmalı veya');
    console.log('   istemci tarafında getIdToken(true) ile token yenilenmeli.');
    process.exit(0);
  })
  .catch((err) => {
    console.error('Hata:', err);
    process.exit(1);
  });
