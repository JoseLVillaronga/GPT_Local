import extractor_html as html_ext
resultado = html_ext.extraer_texto_html_markdown("https://www.argentina.gob.ar/normativa/nacional/ley-26994-235975/texto")
#print(resultado["texto"])
try:
    with open("resultado_html.md", "w", encoding="utf-8") as archivo:
        archivo.write("Texto extraído:\n\n")
        archivo.write(resultado["texto"])
    print(f"\nEl resultado se ha guardado en el archivo 'resultado.md'.")
except Exception as e:
    print(f"Error al guardar el archivo: {e}")