from math import radians
from PIL import Image, ImageDraw, ImageFont, ImageColor
from io import BytesIO
import requests

async def createWelcomeCard(pfpURL, name):

    im = Image.open("assets/template.png")

    r = requests.get(pfpURL)
    data = BytesIO(r.content)
    pfp = Image.open(data)

    maxwidth, maxheight = 750, 720

    pfp = pfp.resize((450,450))
    draw = ImageDraw.Draw(im)
    draw.rectangle(xy=(1000, 0, 1280, 720), fill="#f1c058", outline="#f1c058", width=1)
    im.paste(pfp, (737, 134))
    draw.rounded_rectangle(xy=(727, 126, 1197,595), radius=30,outline="#f1c058",width=20)
    draw.rounded_rectangle(xy=(737, 136, 1187,585), radius=30,outline="black",width=10)

    font = ImageFont.truetype(font="assets/uni-sans.heavy-caps.otf", size=70)
    draw.text(xy=(160,170),text="Welcome to", fill="#f1c058", font=font, align="center")


    logo = Image.open("assets/logo.png")
    logo = logo.resize((270,270))
    im.paste(logo,(240,230), logo)

    w, h = draw.textsize(f"{name}!", font=font)
    draw.text(xy=((maxwidth-w)/2, 500), text=f"{name}!", fill="#f1c058",font=font, align="center")

    im.save(f"{name}.png")