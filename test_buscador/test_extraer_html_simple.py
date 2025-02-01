import extractor_html as html_ext
resultado = html_ext.extraer_texto_html_markdown("https://es.wikipedia.org/wiki/Preámbulo_de_la_Constitución_de_la_Nación_Argentina")
#print(resultado["texto"])
try:
    with open("resultado_html2.md", "w", encoding="utf-8") as archivo:
        archivo.write("Texto extraído:\n\n")
        archivo.write(resultado["texto"])
    print(f"\nEl resultado se ha guardado en el archivo 'resultado.md'.")
except Exception as e:
    print(f"Error al guardar el archivo: {e}")