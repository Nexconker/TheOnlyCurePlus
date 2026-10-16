"""Steam limita la descripción a 8000 caracteres: el apartado de cambios de las descripciones del Workshop se deja
en un resumen de la última versión y un enlace al CHANGELOG completo de GitHub.
Uso: python shorten_changelog.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
LINK = "https://github.com/Nexconker/TheOnlyCurePlus/blob/main/CHANGELOG.md"
NEW = {
 "EN": ("[h2]Changelog[/h2]", "[h2]Compatibility[/h2]", """[h2]Changelog[/h2]
[b]3.1.1[/b]
[list]
[*]New: optional add-on for Tomb's Player Body, made with Tomb's permission (see above).
[*]Fixed: saves not loading with mods that write lower-case base.X references (Medieval Makeshiftery, Vanilla Outfits Expanded): TOC's sound script declared module "base" in lower case.
[*]Fixed: TOC+ body slots are restored if another body-slot mod removes them.
[*]Fixed: skin poking out at the wrist under hand prostheses.
[*]Fixed: crutch and crawling stamina drained per frame (tired after a few steps at high FPS). New sandbox options for both, and characters with a leg amputee trait spend half.
[/list]
[b]3.1.0[/b]: Ash-style chainsaw arm, above-elbow prostheses, stumps cut from the body, clothing over stumps and many fixes.
Full history: [url=""" + LINK + """]CHANGELOG on GitHub[/url].

"""),
 "ES": ("[h2]Cambios[/h2]", "[h2]Compatibilidad[/h2]", """[h2]Cambios[/h2]
[b]3.1.1[/b]
[list]
[*]Nuevo: mod opcional para Tomb's Player Body, hecho con permiso de Tomb (ver arriba).
[*]Corregido: partidas que no cargaban con Medieval Makeshiftery, Vanilla Outfits Expanded y otros mods que escriben base.X en minúscula.
[*]Corregido: las ranuras corporales de TOC+ se restauran si otro mod las borra.
[*]Corregido: piel que asomaba en la muñeca bajo las prótesis de mano.
[*]Corregido: la resistencia con muleta y al arrastrarse se gastaba por fotograma. Opciones nuevas de sandbox; con rasgo de pierna amputada se gasta la mitad.
[/list]
[b]3.1.0[/b]: brazo motosierra estilo Ash, prótesis por encima del codo, muñones recortados del cuerpo, ropa sobre los muñones y muchos arreglos.
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
