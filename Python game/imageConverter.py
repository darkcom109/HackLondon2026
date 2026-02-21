from PIL import Image
from pathlib import Path

source_path = Path(input("Which file do you want to convert? ").strip())
if not source_path.exists():
    raise FileNotFoundError(f"Image not found: {source_path}")

img = Image.open(source_path).convert("L")

threshold = 128

img = img.point(lambda p: 255 if p > threshold else 0)

img = img.convert("1")
output_path = source_path.with_name(f"{source_path.stem}_bw.png")
img.save(output_path)
img.show()

pixels = img.load()
width, height = img.size

print("width:", width, "height:", height)
print("saved:", output_path)
print()
print("Sprite=[")
for y in range(height):
    row = []
    for x in range(width):
        row.append("1" if pixels[x, y] == 0 else "0")
    print("    [" + ",".join(row) + "],")
print("]")
