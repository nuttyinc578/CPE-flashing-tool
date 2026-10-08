"""Static checks for the dependency-free GitHub Pages site."""
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[1]/'site'
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=set(); self.fragments=[]; self.local=[]; self.h1=0
    def handle_starttag(self, tag, attributes):
        values=dict(attributes)
        if tag=='h1': self.h1+=1
        if 'id' in values:
            assert values['id'] not in self.ids, 'Duplicate ID'
            self.ids.add(values['id'])
        for key in ('href','src'):
            value=values.get(key,'')
            if value.startswith('#') and len(value)>1: self.fragments.append(value[1:])
            elif value and not value.startswith(('https://','http://','#')): self.local.append(value)
page=Page(); page.feed((root/'index.html').read_text(encoding='utf-8'))
assert page.h1==1
assert set(page.fragments)<=page.ids
assert all((root/path).is_file() for path in page.local)
assert '@import' not in (root/'style.css').read_text(encoding='utf-8')
print('Site headings, navigation fragments and local assets verified.')
