"""Formattatore personalizzato per i blocchi ```mermaid (pymdownx.superfences).

Fa esattamente quello che fa di default pymdownx (produce <pre class="mermaid"><code>...</code></pre>,
che il bundle di Material trasforma poi nel disegno), ma lo avvolge in un <figure> stabile che porta
il codice sorgente originale in un attributo (base64, per evitare problemi di escaping/quoting).
Serve a corso/assets/javascripts/mermaid-lightbox.js per ridisegnare il diagramma, più grande,
in una finestra a schermo intero quando ci si clicca sopra — Material sostituisce l'elemento
interno con lo shadow DOM del disegno, quindi il testo originale va conservato altrove.
"""
import base64


def _escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def format_mermaid(source, language, class_name, options, md, **kwargs):
    classes = kwargs['classes']
    id_value = kwargs['id_value']
    attrs = kwargs['attrs']

    if class_name:
        classes.insert(0, class_name)

    id_attr = f' id="{id_value}"' if id_value else ''
    class_attr = ' class="{}"'.format(' '.join(classes)) if classes else ''
    other_attrs = ' ' + ' '.join(f'{k}="{v}"' for k, v in attrs.items()) if attrs else ''
    b64 = base64.b64encode(source.encode('utf-8')).decode('ascii')

    return (
        '<figure class="mermaid-figure" tabindex="0" role="button" '
        f'aria-label="Apri il diagramma a schermo intero" data-mermaid-src="{b64}">'
        f'<pre{id_attr}{class_attr}{other_attrs}><code>{_escape(source)}</code></pre>'
        '</figure>'
    )
