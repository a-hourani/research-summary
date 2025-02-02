import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

# Custom extension for code highlighting
class CodeBlockExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.preprocessors.register(CodeBlockPreprocessor(md), 'code_block', 25)

class CodeBlockPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
      new_lines = []
      in_code_block = False
      code_block_lines = []
      language = None

      for line in lines:
          if line.startswith("```"):
              if in_code_block:
                  # End of code block
                  lexer = get_lexer_by_name(language, stripall=True)
                  formatter = HtmlFormatter()
                  highlighted_code = highlight("\n".join(code_block_lines), lexer, formatter)
                  new_lines.append(highlighted_code)
                  in_code_block = False
                  code_block_lines = []
              else:
                  # Start of code block
                  in_code_block = True
                  language = line[3:].strip() or 'text'  # Default to 'text' if no language specified
          elif in_code_block:
              code_block_lines.append(line)
          else:
              new_lines.append(line)

      return new_lines

# Markdown to HTML conversion with LaTeX and code block support
def markdown_to_html(markdown_text):
    extensions = [
        'pymdownx.arithmatex',  # LaTeX support
        CodeBlockExtension(),   # Custom code block extension
        'fenced_code',          # Fenced code blocks
        'tables',               # Tables support
        'toc',                  # Table of contents
    ]

    html = markdown.markdown(markdown_text, extensions=extensions)
    return html


from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin

# Initialize Markdown parser
md = (
    MarkdownIt('commonmark', {'breaks': True, 'html': True, 'typographer': True})
    .use(front_matter_plugin)
    .use(footnote_plugin)
    .enable('table')
)
