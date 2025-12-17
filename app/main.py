import argparse
import os

import pandas as pd
from src.processing_cpu import bucle_autorestart


 #afegir default (4 files)

'''
def parse_args():
    parser = argparse.ArgumentParser(description="Processador d'expedients amb OCR i threading.")
    parser.add_argument("--csv-path", required=True, help="Ruta al CSV amb la columna 'expedient'.") #afegir default
    parser.add_argument("--read-pdfs", required=True, help="Carpeta base on hi ha les carpetes dels PDFs dels expedients.") #afegir default
    parser.add_argument("--save-txt", required=True, help="Carpeta on es guardaran els fitxers .txt.") #afegir default
    parser.add_argument("--progress-path", required=True, help="Fitxer CSV de progrés (es crearà si no existeix).") #afegir default
    parser.add_argument("--ocr", choices=["yes", "no"], default="yes", help="Si cal fer OCR ('yes' o 'no').")
    parser.add_argument("--max-workers", type=int, default=10, help="Nombre màxim de threads en paral·lel.")
    parser.add_argument("--max-hours", type=float, default=7.0, help="Hores màximes per sessió.")
    parser.add_argument("--cooldown-minutes", type=float, default=30.0, help="Minuts de pausa entre sessions.")
    return parser.parse_args()
'''

import argparse
import os
import pandas as pd
from src.processing_cpu import bucle_autorestart


def parse_args():
    # Carpeta base relativa al projecte
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_BASE = os.path.join(BASE_DIR, "data")

    default_csv      = os.path.join(DATA_BASE, "input_csv", "expedients_cpu.csv")
    default_read_pdf = os.path.join(DATA_BASE, "pdf_docs")
    default_save_txt = os.path.join(DATA_BASE, "txt_results")
    default_progress = os.path.join(DATA_BASE, "progress.csv")

    parser = argparse.ArgumentParser(description="Processador d'expedients amb OCR i threading.")
    
    parser.add_argument("--csv-path", default=default_csv,
                        help="Ruta al CSV amb la columna 'expedient'. (DEFAULT: data/input_csv/expedients_cpu.csv)")
    parser.add_argument("--read-pdfs", default=default_read_pdf,
                        help="Carpeta amb els PDFs dels expedients.")
    parser.add_argument("--save-txt", default=default_save_txt,
                        help="Carpeta on es guardaran els fitxers .txt.")
    parser.add_argument("--progress-path", default=default_progress,
                        help="Fitxer CSV de progrés (es crearà si no existeix).")

    parser.add_argument("--ocr", choices=["yes", "no"], default="yes",
                        help="Si cal fer OCR ('yes' o 'no').")
    parser.add_argument("--max-workers", type=int, default=5,
                        help="Nombre màxim de threads en paral·lel.")
    parser.add_argument("--max-hours", type=float, default=7.0,
                        help="Hores màximes per sessió.")
    parser.add_argument("--cooldown-minutes", type=float, default=30.0,
                        help="Minuts de pausa entre sessions.")

    return parser.parse_args()


def main():
    args = parse_args()

    print("\n=== PATHS UTILITZATS ===")
    print(f"CSV:            {args.csv_path}")
    print(f"PDFs:           {args.read_pdfs}")
    print(f"TXT results:    {args.save_txt}")
    print(f"Progress CSV:   {args.progress_path}")
    print("========================\n")

    # Assegurar que les carpetes existeixen
    os.makedirs(args.read_pdfs, exist_ok=True)
    os.makedirs(args.save_txt, exist_ok=True)
    os.makedirs(os.path.dirname(args.csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(args.progress_path), exist_ok=True)

    # Carregar dataframe
    data_df = pd.read_csv(args.csv_path, sep=";")

    # Normalitzar la columna
    col = "expedient" if "expedient" in data_df.columns else "Expedient"
    
    data_df["expedient"] = (
        data_df[col]
        .astype(str)
        .str.replace("/", "_")
        .str.replace("-", "_")
        .str.replace(".", "_")
        .str.replace(" ", "_")
    )

    # Executar procesament amb autorestart
    bucle_autorestart(
        data_df=data_df,
        path_read_files=args.read_pdfs,
        path_save_txt=args.save_txt,
        ocr=args.ocr,
        progress_path=args.progress_path,
        max_workers=args.max_workers,
        max_hours=args.max_hours,
        cooldown_minutes=args.cooldown_minutes,
    )


if __name__ == "__main__":
    main()