from PIL import Image
import sys

def png_to_mono_hlsb(path, width=None, height=None, threshold=128):
    img=Image.open(path).convert("L")
    if width and height:
        img=img.resize((width, height))
    img=img.point(lambda p: 255 if p>threshold else 0).convert("1")
    width, height=img.size
    bytesPerRow=(width+7)//8
    frame=bytearray(bytesPerRow*height)

    pixels=img.load()

    for y in range(height):
        for x in range(width):
            bit = 1 if pixels[x, y] == 0 else 0
            if bit:
                i=y*bytesPerRow + (x//8)
                frame[i] |=(1<<(x%8))
    return width, height, frame

# Backward-compatible alias.
def pngToMono_HSLB(path, width=None, height=None, threshold=128):
    return png_to_mono_hlsb(path, width=width, height=height, threshold=threshold)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pngToMono_HLSB.py [imageName].png [w h]")
        sys.exit(1)

    path = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) >= 4 else None
    h = int(sys.argv[3]) if len(sys.argv) >= 4 else None

    width, height, buf = png_to_mono_hlsb(path, width=w, height=h)

    print(f"W={width} H={height} BYTES={len(buf)}")
    print("frame = (")
    print(f"    {width}, {height},")
    print("    bytes([")
    # pretty-print 16 bytes per line
    for i in range(0, len(buf), 16):
        chunk = ", ".join(str(b) for b in buf[i:i+16])
        print("        " + chunk + ",")
    print("    ])")
    print("    )")
