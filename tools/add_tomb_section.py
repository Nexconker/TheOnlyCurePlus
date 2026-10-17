"""Sección "Tomb's Player Body" de las descripciones del Workshop (banner + cómo activar el submod TombBody fit), la línea de
compatibilidad y el crédito a Tomb. Idempotente. Uso: python shorten_changelog.py && python add_tomb_section.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = "https://raw.githubusercontent.com/Nexconker/TheOnlyCurePlus/main/docs/tombbody_banner.png"
SEC = {
 "EN": ("[h2]Changelog[/h2]", """[h2]Tomb's Player Body[/h2]
[img]%s[/img]
Using Tomb's Player Body? Enable the optional mod [b]The Only Cure+ - TombBody fit[/b], included in this Workshop item, and load it after The Only Cure+ and Tomb's Player Body. Stumps are built on Tomb's body so hips and shoulders match it, and every prosthesis is refitted to its shape. It uses your own Tomb texture (normal, DOLL or NUDE).

""" % IMG,
  "[*]Body replacers such as TombBody work, but prostheses are fitted to the vanilla body and will clip on a different one.",
  "[*]Tomb's Player Body: use the add-on above. Other body replacers work, but prostheses are fitted to the vanilla body.",
  "Body-location code: RabenRabo.", "Body-location code: RabenRabo. Tomb's Player Body is by Tomb; the TombBody fit add-on is made with Tomb's permission."),
 "ES": ("[h2]Cambios[/h2]", """[h2]Tomb's Player Body[/h2]
[img]%s[/img]
¿Usas Tomb's Player Body? Activa el mod opcional [b]The Only Cure+ - TombBody fit[/b], incluido en este ítem del Workshop, y cárgalo después de The Only Cure+ y Tomb's Player Body. Los muñones están hechos sobre el cuerpo de Tomb para que cadera y hombro casen, y cada prótesis está reajustada a su forma. Usa tu propia textura de Tomb (normal, DOLL o NUDE).

""" % IMG,
  "[*]Los reemplazos de cuerpo como TombBody funcionan, pero las prótesis están ajustadas al cuerpo vanilla y lo atravesarán.",
  "[*]Tomb's Player Body: usa el mod de arriba. Otros reemplazos de cuerpo funcionan, pero las prótesis están ajustadas al cuerpo vanilla.",
  "Código de ubicaciones de cuerpo: RabenRabo.", "Código de ubicaciones de cuerpo: RabenRabo. Tomb's Player Body es de Tomb; el mod TombBody fit está hecho con su permiso."),
}
for lang, (anchor, sec, comp_old, comp_new, cred_old, cred_new) in SEC.items():
    p = os.path.join(HERE, "workshop_description_%s.txt" % lang)
    s = open(p, encoding="utf-8").read()
    if "[h2]Tomb's Player Body[/h2]" in s:
        a = s.index("[h2]Tomb's Player Body[/h2]"); s = s[:a] + s[s.index(anchor):]
    s = s.replace(anchor, sec + anchor, 1)
    s = s.replace(comp_old, comp_new, 1)
    if cred_new not in s: s = s.replace(cred_old, cred_new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print(lang, len(s), "caracteres", "OK" if len(s) <= 8000 else "SE PASA")
