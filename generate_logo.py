from PIL import Image, ImageDraw, ImageFont
import os

# Create 1024x1024 transparent canvas
size = 1024
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Brand colors
blood_red = (153, 27, 27, 255)  # #991b1b
dark_bg = (30, 31, 34, 255)     # #1e1f22

# Draw a stylized "V" with shield-like shape
# Shield outline points (centered, large)
margin = 100
center_x = size // 2
top_y = margin
bottom_y = size - margin
mid_y = size * 0.4

# V-shaped shield points
points = [
    (center_x, bottom_y),           # Bottom point
    (margin, top_y),                # Top left
    (margin, mid_y),                # Left mid
    (center_x, size * 0.7),         # Inner bottom
    (size - margin, mid_y),         # Right mid
    (size - margin, top_y),         # Top right
]

# Draw filled shield
draw.polygon(points, fill=blood_red, outline=None)

# Add inner "veil" pattern - simple diagonal lines suggesting encryption
line_color = (200, 50, 50, 100)  # Lighter red, semi-transparent
for i in range(5):
    offset = i * 80 + 200
    draw.line([(offset, top_y + 50), (offset - 200, mid_y)], fill=line_color, width=20)

# Save
os.makedirs('assets', exist_ok=True)
img.save('assets/logo.png', 'PNG')
print("Logo saved to assets/logo.png")
