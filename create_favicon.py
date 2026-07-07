from PIL import Image

src = r'docs\assets\images\logo.png'
img = Image.open(src).convert('RGBA')
w, h = img.size
print(f"Logo size: {w}x{h}")

# Crop just the DC lettermark (no text below)
crop = img.crop((
    int(w * 0.17),   # left
    int(h * 0.19),   # top
    int(w * 0.83),   # right
    int(h * 0.54),   # bottom
))
print(f"Crop: {crop.size}")

# Make near-white pixels transparent, keep dark pixels (the DC mark)
pixels = crop.load()
cw, ch = crop.size
for y in range(ch):
    for x in range(cw):
        r, g, b, a = pixels[x, y]
        if r > 200 and g > 200 and b > 200:
            pixels[x, y] = (r, g, b, 0)  # transparent
        else:
            pixels[x, y] = (r, g, b, 255)

# Scale onto a square transparent canvas with padding
SIZE = 256
canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
scale = (SIZE * 0.82) / max(cw, ch)
nw, nh = int(cw * scale), int(ch * scale)
mark = crop.resize((nw, nh), Image.LANCZOS)
ox = (SIZE - nw) // 2
oy = (SIZE - nh) // 2
canvas.paste(mark, (ox, oy), mark)

ico_path = r'docs\assets\images\favicon.ico'
canvas.save(ico_path, format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64)])
print(f"Saved {ico_path}")

png_path = r'docs\assets\images\favicon-192.png'
canvas.resize((192, 192), Image.LANCZOS).save(png_path)
print(f"Saved {png_path}")
