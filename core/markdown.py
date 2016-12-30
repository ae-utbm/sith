import re
from mistune import Renderer, InlineGrammar, InlineLexer, Markdown
from django.core.urlresolvers import reverse_lazy, reverse


class SithRenderer(Renderer):
    def file_link(self, id, suffix):
        return reverse('core:file_detail', kwargs={'file_id': id}) + suffix

    def exposant(self, text):
        return """<span class="exposant">%s</span>""" % text

    def indice(self, text):
        return """<span class="indice">%s</span>""" % text

    def underline(self, text):
        return """<span class="underline">%s</span>""" % text

class SithInlineGrammar(InlineGrammar):
    double_emphasis = re.compile(
        r'^\*{2}([\s\S]+?)\*{2}(?!\*)'  # **word**
    )
    emphasis = re.compile(
        r'^\*((?:\*\*|[^\*])+?)\*(?!\*)'  # *word*
    )
    underline = re.compile(
        r'^_{2}([\s\S]+?)_{2}(?!_)'  # __word__
    )
    exposant = re.compile( # FIXME Does not work for now
        r'^\^([\s\S]+?)\^'  # ^text^
        # r'|' # FIXME doesn't properly works like this
        # r'^\^(\S+)'  # ^word
    )
    indice = re.compile(
        r'^_([\s\S]+?)_'  # _text_ (^` hack, because no other solution were found :/ this sadly prevent code in indices)
        # r'|' # FIXME doesn't properly works like this
        # r'^_(\S+)'  # _word
    )

class SithInlineLexer(InlineLexer):
    grammar_class = SithInlineGrammar

    default_rules = [
        'escape',
        'inline_html',
        'autolink',
        'url',
        'footnote',
        'link',
        'reflink',
        'nolink',
        'exposant',
        'double_emphasis',
        'emphasis',
        'underline',
        'indice',
        'code',
        'linebreak',
        'strikethrough',
        'text',
    ]
    inline_html_rules = [
        'escape',
        'autolink',
        'url',
        'link',
        'reflink',
        'nolink',
        'exposant',
        'double_emphasis',
        'emphasis',
        'underline',
        'indice',
        'code',
        'linebreak',
        'strikethrough',
        'text',
    ]

    def output_underline(self, m):
        text = m.group(1)
        return self.renderer.underline(text)

    def output_exposant(self, m):
        text = m.group(1)
        return self.renderer.exposant(text)

    def output_indice(self, m):
        text = m.group(1)
        return self.renderer.indice(text)

    # Double emphasis rule changed
    def output_double_emphasis(self, m):
        text = m.group(1)
        text = self.output(text)
        return self.renderer.double_emphasis(text)

    # Emphasis rule changed
    def output_emphasis(self, m):
        text = m.group(1)
        text = self.output(text)
        return self.renderer.emphasis(text)

    def _process_link(self, m, link, title=None):
        try: # Add page:// support for links
            page = re.compile(
                r'^page://(\S*)'                   # page://nom_de_ma_page
            )
            match = page.search(link)
            page = match.group(1) or ""
            link = reverse('core:page', kwargs={'page_name': page})
        except: pass
        try: # Add file:// support for links
            file_link = re.compile(
                r'^file://(\d*)/?(\S*)?'                   # file://4000/download
            )
            match = file_link.search(link)
            id = match.group(1)
            suffix = match.group(2) or ""
            link = reverse('core:file_detail', kwargs={'file_id': id}) + suffix
        except: pass
        return super(SithInlineLexer, self)._process_link(m, link, title)

renderer = SithRenderer()
inline = SithInlineLexer(renderer)

markdown = Markdown(renderer, inline=inline)

if __name__ == "__main__":
    print(markdown.inline.default_rules)
    print(markdown.inline.inline_html_rules)
    text = """
## Basique

* Mettre le texte en **gras** : `**texte**`

* Mettre le texte en *italique* : `*texte*`

* __Souligner__ le texte : `__texte__`

* ~~Barrer du texte~~ : `~~texte~~`

* Mettre ^du texte^ en ^exposant^ : `^mot` ou `^texte^`

* _Mettre du texte_ en _indice_ : `_mot` ou `_texte_`

* Pied de page [^en pied de page]

## Blocs de citations

Un bloc de citation se crée ainsi :
```
> Ceci est
> un bloc de
> citation
```

 > Ceci est
 > un bloc de
 > citation

Il est possible d'intégrer de la syntaxe Markdown-AE dans un tel bloc.

Petit *test* _sur_ ^une^ **seule** ^ligne pour voir^

"""
    print(markdown(text))

