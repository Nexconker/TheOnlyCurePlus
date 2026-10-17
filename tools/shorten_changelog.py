"""Steam limita la descripción a 8000 caracteres: el apartado de cambios de las descripciones del Workshop se deja
en un resumen de la última versión y un enlace al CHANGELOG completo de GitHub.
Uso: python shorten_changelog.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
LINK = "https://github.com/Nexconker/TheOnlyCurePlus/blob/main/CHANGELOG.md"
NEW = {
 "EN": ("[h2]Changelog[/h2]", "[h2]Compatibility[/h2]", """[h2]Changelog[/h2]
[b]3.1.2[/b]
[list]
[*]Fixed: amputations made an hour or more after loading did not heal or turn septic until reloading (thanks Blakurion).
[*]Fixed: sprinting on a crutch, crawling or on a peg leg.
[*]Fixed: amputation saw sound looping forever when another mod cleared the action queue.
[*]New: improvised tourniquets from ripped sheets, denim or leather strips, or a belt, plus a stick.
[*]New sandbox option to hide the amputee traits in character creation.
[*]New language: Brazilian Portuguese.
[/list]
[b]3.1.1[/b]: Tomb's Player Body add-on, fix for saves not loading with mods that write base.X in lower case, crutch stamina per second with sandbox options.
Full history: [url=""" + LINK + """]CHANGELOG on GitHub[/url].

"""),
 "ES": ("[h2]Cambios[/h2]", "[h2]Compatibilidad[/h2]", """[h2]Cambios[/h2]
[b]3.1.2[/b]
[list]
[*]Corregido: las amputaciones hechas una hora o más tras cargar no cicatrizaban ni daban sepsis hasta recargar (gracias, Blakurion).
[*]Corregido: se podía esprintar con muleta, arrastrándose o con pata de palo.
[*]Corregido: el sonido de la sierra quedaba en bucle si otro mod vaciaba la cola de acciones.
[*]Nuevo: torniquetes improvisados con tiras de tela, vaquero o cuero, o un cinturón, y un palo.
[*]Nueva opción de sandbox para ocultar los rasgos de amputado en la creación de personaje.
[*]Nuevo idioma: portugués de Brasil.
[/list]
[b]3.1.1[/b]: mod para Tomb's Player Body, partidas que no cargaban con mods que escriben base.X en minúscula, resistencia con muleta por segundo.
Historial completo: [url=""" + LINK + """]CHANGELOG en GitHub[/url].

"""),
}
for lang, (start, end, text) in NEW.items():
    p = os.path.join(HERE, "workshop_description_%s.txt" % lang)
    s = open(p, encoding="utf-8").read()
    i, j = s.index(start), s.index(end)
    s = s[:i] + text + s[j:]
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print(lang, len(s), "caracteres", "OK" if len(s) <= 8000 else "SE PASA")
