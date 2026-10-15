"""Steam limita la descripción a 8000 caracteres: el apartado de cambios de las descripciones del Workshop se deja
en un resumen de la última versión y un enlace al CHANGELOG completo de GitHub.
Uso: python shorten_changelog.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
LINK = "https://github.com/Nexconker/TheOnlyCurePlus/blob/main/CHANGELOG.md"
NEW = {
 "EN": ("[h2]Changelog[/h2]", "[h2]Compatibility[/h2]", """[h2]Changelog[/h2]
[b]3.1.0[/b]
[list]
[*]New: Ash-style chainsaw arm, and prostheses above the elbow for every arm tier.
[*]Fixed: dark stripe around the shoulder (arm stumps are now cut from the body), skin poking through arm prostheses, wrong stump texture on zombies.
[*]Fixed: Bandits console errors, glass and cuts coming back in multiplayer, leg amputee traits unable to move (they start with a crutch; one leg without a crutch crawls), prostheses that would not go on a right stump.
[*]Fixed: arm prostheses losing parts with amputated legs, a see-through gap at the shoulder of arm stumps, trousers and jackets losing a leg or sleeve over a stump (prostheses now show under them as intended), and holes in the wound at the end of a stump.
[*]Changed: arm prostheses sized like the real arm, new mechanical and medical hands, the hook curves inwards, amputee trait icons in the vanilla style.
[*]New sandbox options: sleeping pills as anaesthesia (30 by default), self-amputation above the elbow and knee.
[/list]
Full history: [url=""" + LINK + """]CHANGELOG on GitHub[/url].

"""),
 "ES": ("[h2]Cambios[/h2]", "[h2]Compatibilidad[/h2]", """[h2]Cambios[/h2]
[b]3.1.0[/b]
[list]
[*]Nuevo: brazo motosierra estilo Ash y prótesis por encima del codo para todos los tipos de brazo.
[*]Corregido: raya oscura en el hombro (los muñones de brazo se recortan del propio cuerpo), piel que asomaba por las prótesis de brazo, textura de muñón equivocada en zombis.
[*]Corregido: errores con Bandits, cristales y cortes que volvían en multijugador, rasgos de pierna amputada sin poder moverse (empiezan con muleta; con una pierna y sin muleta se arrastran), prótesis que no se ponían en un muñón derecho.
[*]Corregido: prótesis de brazo que perdían piezas con las piernas amputadas, una rendija en el hombro de los muñones de brazo, pantalones y chaquetas que perdían la pernera o la manga sobre un muñón (las prótesis ya asoman bajo ellos como debían) y huecos en la herida del extremo del muñón.
[*]Cambiado: prótesis de brazo del tamaño del brazo real, manos mecánica y médica nuevas, el gancho se curva hacia dentro, iconos de rasgos de amputado al estilo vanilla.
[*]Nuevas opciones de sandbox: somníferos como anestesia (30 por defecto) y amputarse uno mismo por encima del codo y la rodilla.
[/list]
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
