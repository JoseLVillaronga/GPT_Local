import extractor_pdf as pdf_ext
resultado = pdf_ext.extraer_texto_pdf_markdown("https://www.oas.org/dil/esp/codigo_civil_de_la_republica_argentina.pdf")
#print(resultado["texto"])
try:
    with open("resultado.md", "w", encoding="utf-8") as archivo:
        archivo.write("Texto extraído:\n\n")
        archivo.write(resultado["texto"])
    print(f"\nEl resultado se ha guardado en el archivo 'resultado.md'.")
except Exception as e:
    print(f"Error al guardar el archivo: {e}")