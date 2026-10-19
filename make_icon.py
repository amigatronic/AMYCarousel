# Generates AMYCarousel.ico: stylized carousel (merry-go-round) in the app's amber palette
from PIL import Image, ImageDraw

S = 1024  # drawing size (supersampled, downscaled per icon size)
BG, AMBER, DARK, LIGHT = (23, 23, 26, 255), (232, 160, 32, 255), (196, 112, 16, 255), (255, 214, 120, 255)

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, S - 1, S - 1), radius=200, fill=BG)  # dark rounded tile

cx = S // 2
# Flag on top of the roof
d.line((cx, 120, cx, 215), fill=LIGHT, width=22)
d.polygon([(cx, 120), (cx + 95, 150), (cx, 182)], fill=LIGHT)
# Canopy: big triangle with scalloped lower edge
roof_top, roof_bot = 205, 430
d.polygon([(cx, roof_top), (110, roof_bot), (S - 110, roof_bot)], fill=AMBER)
n = 5
w = (S - 220) / n
for k in range(n):  # scallops
    x0 = 110 + k * w
    d.pieslice((x0, roof_bot - w / 2, x0 + w, roof_bot + w / 2), 0, 180, fill=DARK if k % 2 else AMBER)
# Poles (center pole thicker) with horses represented by round beads
for x, wd in ((215, 26), (cx, 34), (S - 215, 26)):
    d.rectangle((x - wd // 2, roof_bot + 30, x + wd // 2, 720), fill=LIGHT)
for x in (215, S - 215):
    d.ellipse((x - 48, 560, x + 48, 656), fill=AMBER)
d.ellipse((cx - 56, 520, cx + 56, 632), fill=DARK)
# Base platform (ellipse + rim)
d.ellipse((90, 680, S - 90, 860), fill=DARK)
d.ellipse((90, 660, S - 90, 820), fill=AMBER)
d.ellipse((150, 690, S - 150, 790), fill=BG)
d.ellipse((190, 705, S - 190, 775), fill=DARK)

sizes = [16, 24, 32, 48, 64, 128, 256]
img.save("AMYCarousel.ico", sizes=[(z, z) for z in sizes])
img.resize((256, 256), Image.LANCZOS).save("AMYCarousel_preview.png")
print("icon written")
