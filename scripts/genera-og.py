"""Genera le immagini social (og:image) 1200x630 del corso, IT e EN, tema chiaro."""
from PIL import Image, ImageDraw, ImageFont
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
for suf, titolo, sotto, firma in [
    ("", "Corso pratico di llama.cpp", "Modelli linguistici in locale: dall'installazione alla produzione", "Prof. Giuseppe Bosi · corso gratuito"),
    (".en", "llama.cpp Practical Course", "Run language models locally: from installation to production", "Prof. Giuseppe Bosi · free course")]:
    im = Image.new("RGB", (1200, 630), "#ffffff"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1200, 18], fill="#3f51b5")
    d.text((80, 200), titolo, font=ImageFont.truetype(F + "-Bold.ttf", 72), fill="#1a237e")
    d.text((80, 320), sotto, font=ImageFont.truetype(F + ".ttf", 34), fill="#333333")
    d.text((80, 520), firma, font=ImageFont.truetype(F + ".ttf", 30), fill="#555555")
    d.text((80, 565), "corso-llamacpp.giuseppebosi.com", font=ImageFont.truetype(F + ".ttf", 26), fill="#3f51b5")
    im.save(f"corso/assets/img/og-corso{suf}.png", optimize=True)
