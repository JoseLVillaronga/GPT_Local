import pymupdf4llm

md_text = pymupdf4llm.to_markdown("/home/jose/Modelo-Etico-Adaptativo/docs/modelo/Modelo_Etico_Adaptativo_Explicación_Detallada.pdf")

# now work with the markdown text, e.g. store as a UTF8-encoded file
import pathlib
pathlib.Path("output-mea.md").write_bytes(md_text.encode())
