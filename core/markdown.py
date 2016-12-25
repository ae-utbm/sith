import re
from mistune import Renderer, InlineGrammar, InlineLexer, Markdown
from django.core.urlresolvers import reverse_lazy, reverse


class SithRenderer(Renderer):
    def file_link(self, id, suffix):
        return reverse('core:file_detail', kwargs={'file_id': id}) + suffix

class SithInlineLexer(InlineLexer):
    def _process_link(self, m, link, title=None):
        try:
            page = re.compile(
                r'^page://(\S*)'                   # page://nom_de_ma_page
            )
            match = page.search(link)
            page = match.group(1) or ""
            link = reverse('core:page', kwargs={'page_name': page})
        except: pass
        try:
            file_link = re.compile(
                r'^file://(\d*)/?(\S*)?'                   # file://4000/download
            )
            match = file_link.search(link)
            id = match.group(1)
            suffix = match.group(2) or ""
            link = reverse('core:file_detail', kwargs={'file_id': id}) + suffix
        except: pass
        return super(SithInlineLexer, self)._process_link(m, link, title)

    # def enable_file_link(self):
    #     # add file_link rules
    #     self.rules.file_link = re.compile(
    #         r'dfile://(\d*)/?(\S*)?'                   # dfile://4000/download
    #     )
    #     # Add file_link parser to default rules
    #     # you can insert it some place you like
    #     # but place matters, maybe 2 is not good
    #     self.default_rules.insert(0, 'file_link')

    # def output_file_link(self, m):
    #     id = m.group(1)
    #     suffix = m.group(2) or ""
    #     # you can create an custom render
    #     # you can also return the html if you like
    #     # return directly html like this:
    #     # return reverse('core:file_detail', kwargs={'file_id': id}) + suffix
    #     return self.renderer.file_link(id, suffix)

renderer = SithRenderer()
inline = SithInlineLexer(renderer)

# enable the features
# inline.enable_file_link()
markdown = Markdown(renderer, inline=inline)


