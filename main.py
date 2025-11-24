import argparse
import os

import pandas as pd
'''


def parse_args():
    parser = argparse.ArgumentParser(description="Processador d'expedients amb OCR i threading.")
    parser.add_argument("--csv-path", required=True, help="Ruta al CSV amb la columna 'expedient'.")
    parser.add_argument("--read-pdfs", required=True, help="Carpeta base on hi ha les carpetes dels PDFs dels expedients.")
    parser.add_argument("--save-txt", required=True, help="Carpeta on es guardaran els fitxers .txt.")
    parser.add_argument("--progress-path", required=True, help="Fitxer CSV de progrés (es crearà si no existeix).")
    parser.add_argument("--ocr", choices=["yes", "no"], default="yes", help="Si cal fer OCR ('yes' o 'no').")
    parser.add_argument("--max-workers", type=int, default=10, help="Nombre màxim de threads en paral·lel.")
    parser.add_argument("--max-hours", type=float, default=8.0, help="Hores màximes per sessió.")
    parser.add_argument("--cooldown-minutes", type=float, default=30.0, help="Minuts de pausa entre sessions.")
    return parser.parse_args()


def main():
    args = parse_args()

    # Carregar dataframe
    data_df = pd.read_csv(args.csv_path)

    if "Expedient" not in data_df.columns:
        raise ValueError("El CSV ha de tenir una columna 'Expedient'.")

    # Crear columna 'expedient' neta
    data_df["expedient"] = (
        data_df["Expedient"]
        .astype(str)
        .str.replace("/", "_")
        .str.replace("-", "_")
        .str.replace(".", "_")
        .str.replace(" ", "_")
    )

    # Assegurar que les carpetes existeixen
    os.makedirs(args.save_txt, exist_ok=True)

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

'''
import os
import pandas as pd
from src.processing_cpu import bucle_autorestart


def main():

    # === CONFIGURACIÓ MANUAL DELS PATHS ===
    csv_path = r"C:\Users\aferrerr\OneDrive - Hospital Clínic de Barcelona\Hub Compres 2\DEF - Reporting i Informació de Gestió - ProyectoCompras_IA\docs\github-cpu-ocr\data\input_csv\expedients.csv"
    path_read_files = r"C:\Users\aferrerr\OneDrive - Hospital Clínic de Barcelona\Hub Compres 2\DEF - Reporting i Informació de Gestió - ProyectoCompras_IA\docs\github-cpu-ocr\data\pdf_docs"
    path_save_txt = r"C:\Users\aferrerr\OneDrive - Hospital Clínic de Barcelona\Hub Compres 2\DEF - Reporting i Informació de Gestió - ProyectoCompras_IA\docs\github-cpu-ocr\data\txt_results"
    progress_path = r"C:\Users\aferrerr\OneDrive - Hospital Clínic de Barcelona\Hub Compres 2\DEF - Reporting i Informació de Gestió - ProyectoCompras_IA\docs\github-cpu-ocr\data\progress.csv"

    ocr = "yes"             # "yes" o "no"
    max_workers = 5        # fils en paral·lel
    max_hours = 7          # hores per sessió
    cooldown_minutes = 30   # minuts de pausa

    # === CARREGAR CSV D’EXPEDIENTS ===
    data_df = pd.read_csv(csv_path)
    
    if "expedient" not in data_df.columns:
        raise ValueError("El CSV ha de contenir la columna 'expedient'.")
    # === NORMALITZAR EL NOM D’EXPEDIENT ===
    data_df["expedient"] = (
        data_df["expedient"]
        .astype(str)
        .str.replace("/", "_")
        .str.replace("-", "_")
        .str.replace(".", "_")
        .str.replace(" ", "_")
    )

    # Crear carpetes si no existeixen
    os.makedirs(path_save_txt, exist_ok=True)

    # === EXECUTAR EL PROCESSAMENT AMB AUTORESTART ===
    bucle_autorestart(
        data_df=data_df,
        path_read_files=path_read_files,
        path_save_txt=path_save_txt,
        ocr=ocr,
        progress_path=progress_path,
        max_workers=5,
        max_hours=7,
        cooldown_minutes=30
    )


if __name__ == "__main__":
    main()

