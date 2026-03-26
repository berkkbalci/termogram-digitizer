"""
TIF → PNG dönüştürücü
Kullanım: python3 scripts/tif_to_png.py /TIF/klasörün/yolu termogram
          python3 scripts/tif_to_png.py /TIF/klasörün/yolu barograf
"""

import sys
import os
from PIL import Image

MAX_WIDTH = 2500  # GitHub Pages için optimize boyut

def convert(src_dir, data_type):
    dst_dir = os.path.join(os.path.dirname(__file__), '..', 'images', data_type)
    os.makedirs(dst_dir, exist_ok=True)

    files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.tif', '.tiff'))]
    if not files:
        print(f"❌ {src_dir} içinde TIF dosyası bulunamadı.")
        return

    print(f"📂 {len(files)} TIF bulundu → images/{data_type}/\n")

    for f in sorted(files):
        src_path = os.path.join(src_dir, f)
        out_name = os.path.splitext(f)[0] + '.png'
        dst_path = os.path.join(dst_dir, out_name)

        try:
            img = Image.open(src_path)
            # Renkli yap (bazı TIF'ler palette modunda olur)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            # Büyükse küçült
            if img.width > MAX_WIDTH:
                ratio = MAX_WIDTH / img.width
                new_size = (MAX_WIDTH, int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            img.save(dst_path, 'PNG', optimize=True)
            size_kb = os.path.getsize(dst_path) // 1024
            print(f"  ✓ {out_name}  ({size_kb} KB)")
        except Exception as e:
            print(f"  ❌ {f}: {e}")

    print(f"\n✅ Tamamlandı! Dosyalar: images/{data_type}/")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Kullanım: python3 tif_to_png.py <tif_klasörü> <veri_tipi>")
        print("Örnek:    python3 tif_to_png.py ~/Desktop/termogramlar termogram")
        print("Tipler:   termogram | barograf | termohigrograf | aktinograf")
        sys.exit(1)

    src = sys.argv[1]
    dtype = sys.argv[2]

    if dtype not in ('termogram', 'barograf', 'termohigrograf', 'aktinograf'):
        print(f"❌ Geçersiz tip: {dtype}")
        sys.exit(1)

    if not os.path.isdir(src):
        print(f"❌ Klasör bulunamadı: {src}")
        sys.exit(1)

    convert(src, dtype)
