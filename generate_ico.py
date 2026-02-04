from PIL import Image
import os

# Load the logo
logo = Image.open('assets/logo.png')

# Required sizes for Windows (16, 24, 32, 48, 64, 128, 256)
sizes = [16, 24, 32, 48, 64, 128, 256]

# Generate resized versions with high-quality resampling
icons = []
for s in sizes:
    # Use LANCZOS for high quality downscaling
    resized = logo.resize((s, s), Image.LANCZOS)
    icons.append(resized)

# Save as multi-resolution ICO
# PIL/Pillow supports saving multiple sizes in one ICO
logo.save('assets/icon.ico', format='ICO', sizes=[(s, s) for s in sizes])

print(f"Icon saved with sizes: {sizes}")

# Verify the ICO
ico = Image.open('assets/icon.ico')
print(f"ICO format: {ico.format}, size: {ico.size}")
if hasattr(ico, 'info') and 'sizes' in ico.info:
    print(f"Embedded sizes: {ico.info['sizes']}")
