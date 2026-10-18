"""Generates the three Montgisard wallpapers from one template."""
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
tpl = (root / 'tools' / 'montgisard.template.html').read_text()
for mode, fname, title in [('battle', 'montgisard-battle.html', 'Montgisard: The Battle'),
                           ('victory', 'montgisard-victory.html', 'Jerusalem Holds'),
                           ('charge', 'montgisard-charge.html', 'The Charge of Montgisard')]:
    (root / 'wallpapers' / fname).write_text(tpl.replace('__MODE__', mode).replace('__TITLE__', title))
    print('wrote', fname)
