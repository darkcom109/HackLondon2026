from PIL import Image

img=Image.open(input("Which file do you want to convert?"))
img=img.convert("L")

threshold = 128

img=img.point(lambda p: 255 if p > threshold else 0)

img = img.convert("1")
img.save("happy_bw.png")
img.show()

pixels=img.load()
width, height = img.size

print("width:", width, "height:", height)
print()
print("Sprite=[")
for y in range(height):
    row=[]
    for x in range(width):
        row.append("1" if pixels[x, y]==0 else "0")
    print("    ["+",".join(row)+"],")
print("]")