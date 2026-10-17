"""Steam limita la descripción a 8000 caracteres: el apartado de cambios de las descripciones del Workshop se deja
en un resumen de la última versión y un enlace al CHANGELOG completo de GitHub.
Uso: python shorten_changelog.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
LINK = "https://github.com/Nexconker/TheOnlyCurePlus/blob/main/CHANGELOG.md"
NEW = {
 "EN": ("[h2]Changelog[/h2]", "[h2]Compatibility[/h2]", """[h2]Changelog[/h2]
[b]3.2.0[/b]
[list]
[*]New: mechanical and medical hands close when gripping.
[*]New: no more ghost hand. One-handed actions use the hand you have left, with mirrored animations.
[*]New: Merle's bayonet arm (right arm, Welding 2).
[/list]
[b]3.1.2[/b]: healing and sepsis after the first hour fixed, no sprinting on crutches, looping saw sound, improvised tourniquets, option to hide amputee traits, Brazilian Portuguese.
Full history: [url=""" + LINK + """]CHANGELOG on GitHub[/url].

"""),
 "ES": ("[h2]Cambios[/h2]", "[h2]Compatibilidad[/h2]", """[h2]Cambios[/h2]
[b]3.2.0[/b]
[list]
[*]Nuevo: las manos mecánica y médica se cierran al agarrar.
[*]Nuevo: se acabó la mano fantasma. Las acciones de una mano usan la que te queda, con animaciones espejadas.
[*]Nuevo: el brazo bayoneta de Merle (brazo derecho, Soldadura 2).
[/list]
[b]3.1.2[/b]: cicatrización y sepsis tras la primera hora, sin esprintar con muleta, sonido de sierra en bucle, torniquetes improvisados, opción para ocultar los rasgos de amputado, portugués de Brasil.
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
