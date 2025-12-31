"""
Скрипт для подготовки логотипа и favicon из исходного изображения
Требует: pip install Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Создаем папки
os.makedirs('core/static/images', exist_ok=True)
os.makedirs('core/static/favicon', exist_ok=True)

# Открываем исходное изображение (иконка мозга)
source_image = 'free-icon-convergence-3206055.png'
img = Image.open(source_image).convert('RGBA')

print(f"Исходное изображение: {img.size}")

# 1. Логотип для навигации (200x60 - горизонтальный)
logo_nav = img.resize((200, 60), Image.Resampling.LANCZOS)
logo_nav.save('core/static/images/logo.png', 'PNG', optimize=True)
print("✓ Создан logo.png (200x60)")

# 2. Логотип квадратный для иконки (512x512)
# Обрезаем по центру до квадрата
width, height = img.size
size = min(width, height)
left = (width - size) // 2
top = (height - size) // 2
img_square = img.crop((left, top, left + size, top + size))

# Создаем квадратный логотип
logo_square = img_square.resize((512, 512), Image.Resampling.LANCZOS)
logo_square.save('core/static/images/logo-square.png', 'PNG', optimize=True)
print("✓ Создан logo-square.png (512x512)")

# 3. Favicon разных размеров
favicon_sizes = [16, 32, 48, 64, 128, 192, 256, 512]

for size in favicon_sizes:
    favicon = img_square.resize((size, size), Image.Resampling.LANCZOS)
    favicon.save(f'core/static/favicon/favicon-{size}x{size}.png', 'PNG', optimize=True)
    print(f"✓ Создан favicon-{size}x{size}.png")

# 4. Создаем favicon.ico (мультиразмерный)
favicon_ico_sizes = [(16, 16), (32, 32), (48, 48)]
favicon_images = []
for size in favicon_ico_sizes:
    favicon_images.append(img_square.resize(size, Image.Resampling.LANCZOS))

favicon_images[0].save(
    'core/static/favicon/favicon.ico',
    format='ICO',
    sizes=favicon_ico_sizes,
    append_images=favicon_images[1:]
)
print("✓ Создан favicon.ico (мультиразмерный)")

# 5. Apple Touch Icon
apple_icon = img_square.resize((180, 180), Image.Resampling.LANCZOS)
apple_icon.save('core/static/favicon/apple-touch-icon.png', 'PNG', optimize=True)
print("✓ Создан apple-touch-icon.png (180x180)")

# 6. Android Chrome icons
android_192 = img_square.resize((192, 192), Image.Resampling.LANCZOS)
android_192.save('core/static/favicon/android-chrome-192x192.png', 'PNG', optimize=True)
print("✓ Создан android-chrome-192x192.png")

android_512 = img_square.resize((512, 512), Image.Resampling.LANCZOS)
android_512.save('core/static/favicon/android-chrome-512x512.png', 'PNG', optimize=True)
print("✓ Создан android-chrome-512x512.png")

print("\n✅ Все изображения созданы!")
print("\nСтруктура:")
print("core/static/images/")
print("  ├── logo.png (200x60)")
print("  └── logo-square.png (512x512)")
print("\ncore/static/favicon/")
print("  ├── favicon.ico")
print("  ├── favicon-16x16.png")
print("  ├── favicon-32x32.png")
print("  ├── favicon-192x192.png")
print("  ├── favicon-512x512.png")
print("  ├── apple-touch-icon.png")
print("  ├── android-chrome-192x192.png")
print("  └── android-chrome-512x512.png")
