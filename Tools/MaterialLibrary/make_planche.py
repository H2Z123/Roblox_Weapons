"""Assemble les rendus par matière en une planche légendée : python make_planche.py <dossier_sortie>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[1])
ORDER = [("AcierNoir", "Acier noir mat microrayé"), ("OrGrave", "Or gravé (vrai métal)"),
         ("CaoutchoucPoignee", "Caoutchouc / polymère de poignée"), ("PanneauGris", "Panneau gris"),
         ("AcierBrosse", "Acier brossé terni"), ("BordeauxModule", "Bordeaux du module #80282E")]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f_t, f_s, f_h = ImageFont.truetype(BOLD, 30), ImageFont.truetype(FONT, 20), ImageFont.truetype(BOLD, 44)

tiles = [Image.open(os.path.join(OUT, "rendus", f"{k}.png")).convert("RGB") for k, _ in ORDER]
tw, th = tiles[0].size
cols, head, cap, pad = 2, 110, 54, 16
W = cols * tw + (cols + 1) * pad
H = head + 3 * (th + cap + pad) + pad
board = Image.new("RGB", (W, H), (14, 14, 16))
d = ImageDraw.Draw(board)
d.text((pad + 8, 22), "LastOne · bibliothèque de matières v01", font=f_h, fill=(235, 235, 238))
d.text((pad + 8, 74), "Dans chaque case : sphère  |  cube  |  cube refait avec les 4 cartes Roblox en 1024", font=f_s, fill=(170, 172, 178))
for i, ((key, label), im) in enumerate(zip(ORDER, tiles)):
    x = pad + (i % cols) * (tw + pad)
    y = head + (i // cols) * (th + cap + pad)
    d.text((x + 8, y + 10), label, font=f_t, fill=(235, 235, 238))
    board.paste(im, (x, y + cap))
board.save(os.path.join(OUT, "planche_materiaux_v01.png"))
print("PLANCHE_OK", board.size)
