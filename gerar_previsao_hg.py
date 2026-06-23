import requests, cairosvg, io, urllib.request, numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os

LAT     = -27.8681
LON     = -54.4789
LARGURA = 360
ALTURA  = 240
HG_KEY  = "96908f4d"
HG_URL  = f"https://api.hgbrasil.com/weather?lat={LAT}&lon={LON}&key={HG_KEY}"

ICON_BASE = "https://raw.githubusercontent.com/erikflowers/weather-icons/master/svg/wi-{}.svg"

# Mapeamento de condition_slug do HG Brasil para ícones weather-icons
ICON_MAP = {
    "clear_day":      ("day-sunny",     (245,158,11)),
    "clear_night":    ("night-clear",   (99,102,241)),
    "cloud":          ("cloudy",        (100,116,139)),
    "cloudly_day":    ("day-cloudy",    (148,163,184)),
    "cloudly_night":  ("night-cloudy",  (100,116,139)),
    "fog":            ("fog",           (148,163,184)),
    "hail":           ("hail",          (147,197,253)),
    "rain":           ("rain",          (59,130,246)),
    "rain_night":     ("night-rain",    (59,130,246)),
    "sleet":          ("sleet",         (147,197,253)),
    "snow":           ("snow",          (147,197,253)),
    "storm":          ("storm-showers", (99,102,241)),
    "storm_night":    ("storm-showers", (99,102,241)),
    "none_day":       ("day-cloudy",    (148,163,184)),
    "none_night":     ("night-cloudy",  (100,116,139)),
}

# Mapeamento de condition do forecast (pode ser diferente do slug atual)
FORECAST_ICON_MAP = {
    "clear_day":      ("day-sunny",     (245,158,11)),
    "clear_night":    ("night-clear",   (99,102,241)),
    "cloud":          ("cloudy",        (100,116,139)),
    "cloudly_day":    ("day-cloudy",    (148,163,184)),
    "cloudly_night":  ("night-cloudy",  (100,116,139)),
    "fog":            ("fog",           (148,163,184)),
    "hail":           ("hail",          (147,197,253)),
    "rain":           ("rain",          (59,130,246)),
    "rain_night":     ("night-rain",    (59,130,246)),
    "sleet":          ("sleet",         (147,197,253)),
    "snow":           ("snow",          (147,197,253)),
    "storm":          ("storm-showers", (99,102,241)),
    "storm_night":    ("storm-showers", (99,102,241)),
    "none_day":       ("day-cloudy",    (148,163,184)),
    "none_night":     ("night-cloudy",  (100,116,139)),
}

def wmo_icone(condition, forecast=False):
    m = FORECAST_ICON_MAP if forecast else ICON_MAP
    return m.get(condition, ("day-cloudy", (148,163,184)))

def cache_icone(nome, cor, tamanho=52):
    cor_str = f"{cor[0]}-{cor[1]}-{cor[2]}"
    path = f"/tmp/wef_{nome}_{cor_str}_{tamanho}.png"
    if os.path.exists(path):
        return Image.open(path).convert("RGBA")
    try:
        url = ICON_BASE.format(nome)
        with urllib.request.urlopen(url) as r:
            svg = r.read()
        png = cairosvg.svg2png(bytestring=svg, output_width=tamanho, output_height=tamanho)
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        _, _, _, a = img.split()
        tinted = Image.merge("RGBA", [
            Image.new("L", img.size, cor[0]),
            Image.new("L", img.size, cor[1]),
            Image.new("L", img.size, cor[2]),
            a
        ])
        tinted.save(path)
        return tinted
    except Exception as e:
        print(f"Erro icone {nome}: {e}")
        return None

def colar_icone(img, ic, cx, cy):
    if ic is None: return
    iw, ih = ic.size
    img.paste(ic, (cx - iw//2, cy - ih//2), ic)

def buscar_previsao():
    r = requests.get(HG_URL, timeout=15)
    r.raise_for_status()
    return r.json()["results"]

def fonte(tam, bold=False):
    paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, tam)
            except: pass
    return ImageFont.load_default()

def nome_dia(weekday_str, i):
    if i == 0: return "Hoje"
    if i == 1: return "Amanhã"
    dias = {"Dom":"Domingo","Seg":"Segunda","Ter":"Terça",
            "Qua":"Quarta","Qui":"Quinta","Sex":"Sexta","Sáb":"Sábado"}
    return dias.get(weekday_str, weekday_str)

def gerar_imagem(dados):
    img  = Image.new("RGB", (LARGURA, ALTURA), (255,255,255))
    draw = ImageDraw.Draw(img)

    for y in range(ALTURA):
        t = y / ALTURA
        draw.line([(0,y),(LARGURA,y)], fill=(
            int(240 - t*25), int(248 - t*20), int(255 - t*10)
        ))

    fb28 = fonte(28, bold=True)
    fb13 = fonte(13, bold=True)
    fb11 = fonte(11, bold=True)
    fb10 = fonte(10, bold=True)
    f9   = fonte(9)

    forecast  = dados["forecast"]
    hoje      = forecast[0]
    condition = dados.get("condition_slug", "none_day")
    tmax0     = hoje["max"]
    tmin0     = hoje["min"]
    chuva0    = hoje.get("rain", 0) or 0
    umid      = dados.get("humidity", 0) or 0
    vento0    = dados.get("wind_speedy", "0 km/h")
    desc0     = dados.get("description", hoje.get("description", ""))
    sr        = dados.get("sunrise", "--:--")
    ss        = dados.get("sunset",  "--:--")

    draw.text((14, 10), "Santa Rosa - RS", font=fb13, fill=(40,40,80))

    nome_ic, cor_ic = wmo_icone(condition)
    ic_hoje = cache_icone(nome_ic, cor_ic, tamanho=54)
    colar_icone(img, ic_hoje, 42, 65)

    draw.text((78, 40), f"{tmax0}°/{tmin0}°", font=fb28, fill=(25,25,60))
    draw.text((90, 78), desc0[:18],            font=fb11, fill=(80,80,130))

    cy_info = 106
    nome_ic2, cor_ic2 = wmo_icone("rain")
    ic_chuva = cache_icone(nome_ic2, cor_ic2, tamanho=18)
    colar_icone(img, ic_chuva, 20, cy_info+6)
    draw.text((32, cy_info),    f"{chuva0:.0f} mm", font=fb10, fill=(50,90,200))
    draw.text((32, cy_info+13), "Chuva",             font=f9,   fill=(110,120,160))

    draw.text((105, cy_info),    f"{umid}%", font=fb10, fill=(50,90,200))
    draw.text((105, cy_info+13), "Umidade",  font=f9,   fill=(110,120,160))

    draw.text((32,  cy_info+30), str(vento0),   font=fb10, fill=(50,90,200))
    draw.text((32,  cy_info+43), "Vento máx.",  font=f9,   fill=(110,120,160))

    draw.text((105, cy_info+30), f"{sr}  {ss}", font=fb10, fill=(50,90,200))
    draw.text((105, cy_info+43), "Nasc / Pôr",  font=f9,   fill=(110,120,160))

    draw.line([(193,8),(193,ALTURA-8)], fill=(195,210,230), width=1)

    row_h = (ALTURA - 16) // 3
    for i in range(1, 4):
        ri  = i - 1
        ry  = 8 + ri * row_h
        if ri > 0:
            draw.line([(197, ry),(LARGURA-6, ry)], fill=(205,218,235), width=1)

        cy_row  = ry + row_h//2 - 12
        dia     = forecast[i]
        cond_i  = dia.get("condition", "none_day")
        desc_i  = dia.get("description", "")
        tx      = dia["max"]
        tn      = dia["min"]
        chuva_i = dia.get("rain", 0) or 0

        draw.text((200, cy_row),    nome_dia(dia.get("weekday",""), i), font=fb10, fill=(70,70,120))
        draw.text((200, cy_row+14), desc_i[:14],                        font=f9,   fill=(110,120,165))

        nome_ic3, cor_ic3 = wmo_icone(cond_i, forecast=True)
        ic = cache_icone(nome_ic3, cor_ic3, tamanho=30)
        colar_icone(img, ic, 282, cy_row+10)

        if chuva_i > 0:
            txt_mm = f"{chuva_i:.0f}mm"
            tw_mm  = draw.textlength(txt_mm, font=f9)
            draw.text((282 - int(tw_mm)//2, cy_row+26), txt_mm, font=f9, fill=(70,130,210))

        t_txt = f"{tx}°"
        n_txt = f"{tn}°"
        tw    = draw.textlength(t_txt, font=fb11)
        draw.text((LARGURA-58,           cy_row), t_txt, font=fb11, fill=(210,70,30))
        draw.text((LARGURA-58+int(tw)+3, cy_row), n_txt, font=fb11, fill=(60,130,210))

    try:
        logo_url = "https://raw.githubusercontent.com/gitprocessoscoopermil/previsao-tempo/main/logotipo-coopermil-jpg.jpg"
        with urllib.request.urlopen(logo_url) as r:
            logo_data = r.read()
        logo = Image.open(io.BytesIO(logo_data)).convert("RGBA")
        data = np.array(logo)
        r2, g2, b2 = data[:,:,0], data[:,:,1], data[:,:,2]
        mask = (r2 > 220) & (g2 > 220) & (b2 > 220)
        data[:,:,3] = np.where(mask, 0, 255)
        logo = Image.fromarray(data)
        ratio = 22 / logo.height
        logo  = logo.resize((int(logo.width * ratio), 22), Image.LANCZOS)
        img.paste(logo, (6, ALTURA - 28), logo)
    except Exception as e:
        print(f"Logo erro: {e}")

    return img

def main():
    print("Buscando dados HG Brasil...")
    dados = buscar_previsao()
    print(f"Condição: {dados.get('description')} | Temp: {dados['forecast'][0]['max']}°/{dados['forecast'][0]['min']}°")
    print("Gerando imagem...")
    img = gerar_imagem(dados)
    img.save("previsao_hg.png", "PNG", optimize=True)
    print("Salvo: previsao_hg.png")

if __name__ == "__main__":
    main()
