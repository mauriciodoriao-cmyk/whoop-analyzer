import os
from markitdown import MarkItDown

def main():
    docs_dir = r"g:\Mi unidad\Whoop Analyzer\docs"
    out_dir = r"g:\Mi unidad\Whoop Analyzer\context\extracted_docs"
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    md = MarkItDown()
    
    for filename in os.listdir(docs_dir):
        if filename.endswith(".pdf") or filename.endswith(".docx"):
            print(f"Procesando {filename}...")
            filepath = os.path.join(docs_dir, filename)
            try:
                result = md.convert(filepath)
                out_name = filename.rsplit('.', 1)[0] + ".md"
                out_path = os.path.join(out_dir, out_name)
                
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(result.text_content)
                print(f"  Guardado en {out_path}")
            except Exception as e:
                print(f"  Error procesando {filename}: {e}")

if __name__ == "__main__":
    main()
