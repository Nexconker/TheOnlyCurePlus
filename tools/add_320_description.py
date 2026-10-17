"""Novedades de la 3.2.0 en las descripciones del Workshop (EN/ES): manos que se cierran al agarrar, fin de la mano
fantasma y el brazo bayoneta de Merle. Idempotente. Uso: python add_320_description.py (antes de shorten_changelog.py)"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ADD = {
 "EN": [
  ("[*]They wear out with use.", "[*]Mechanical and medical hands [b]close when gripping[/b]: fingers and thumb follow the game's hand animations, so weapons and tools sit in a fist.\n[*]One-handed actions (pills, drinking, smoking, eating, reading...) use the hand you still have: no more ghost hand.\n", "before"),
  ("[h2]✚ Legs, crutches and crawling[/h2]", "[h2]✚ Merle's bayonet arm[/h2]\n[list]\n[*]Right arm only, a makeshift job: a rusty scrap-metal sleeve, leather straps, duct tape and a bayonet in line with the forearm.\n[*]Welding 2, a knife, scrap metal, leather and duct tape. It stabs like a hunting knife and your left hand stays free.\n[/list]\n\n", "before"),
 ],
 "ES": [
  ("[*]Se desgastan con el uso.", "[*]Las manos mecánica y médica [b]se cierran al agarrar[/b]: dedos y pulgar siguen las animaciones del juego y el arma queda en el puño.\n[*]Las acciones de una mano (pastillas, beber, fumar, comer, leer...) usan la mano que te queda: se acabó la mano fantasma.\n", "before"),
  ("[h2]✚ Piernas, muletas y arrastre[/h2]", "[h2]✚ El brazo bayoneta de Merle[/h2]\n[list]\n[*]Sólo derecho y hecho a mano: manga de chatarra oxidada, correas de cuero, cinta americana y una bayoneta en línea con el antebrazo.\n[*]Soldadura 2, un cuchillo, chatarra, cuero y cinta. Apuñala como un cuchillo de caza y la mano izquierda queda libre.\n[/list]\n\n", "before"),
 ],
}
for lang, items in ADD.items():
    p = os.path.join(HERE, "workshop_description_%s.txt" % lang)
    s = open(p, encoding="utf-8").read()
    for anchor, text, where in items:
        if text.strip().splitlines()[0] in s: continue
        if anchor not in s: raise SystemExit("%s: no encuentro %r" % (lang, anchor))
        s = s.replace(anchor, text + anchor, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print(lang, len(s), "caracteres")
