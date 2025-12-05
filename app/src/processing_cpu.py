import os
import time
from datetime import datetime
import logging
import csv
from multiprocessing import Pool, current_process

import PyPDF2
import pandas as pd

from src import read_files_text_images_cpu

#--------------------------------------------------------------------------
# Variables de configuracion de sistema
#--------------------------------------------------------------------------
#borrar
'''
DATA_BASE = r"./data"

path_read_files = os.path.join(DATA_BASE, "pdf_docs")
path_save_txt   = os.path.join(DATA_BASE, "txt_results")

csv_path = os.path.join(DATA_BASE, "input_csv", "expedients.csv")
progress_path = "progress.csv"

#Variables paralelizacion
USE_OCR = False
OCR_MODEL = None
WORKERS = 5
COOLDOWN = 30
WORK_TIME = 7
'''
#---------------------------------------------------------------------------


def init_worker(ocr_enabled: bool, lang: str = "es", use_angle_cls: bool = True):
    """
    Inicialitzador del worker de multiprocessing.
    Es crida una vegada per procés fill.

    - Si ocr_enabled = True, carrega PaddleOCR en aquest procés.
    """
    global USE_OCR, OCR_MODEL
    USE_OCR = ocr_enabled

    if USE_OCR:
        from paddleocr import PaddleOCR
        print(f"[{current_process().name}] Inicialitzant PaddleOCR...")
        #OCR_MODEL = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, use_gpu=False,cpu_threads=4,enable_mkldnn=True)
        OCR_MODEL = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang)

    else:
        OCR_MODEL = None


def processar_expedient(row_dict, path_read_files, path_save_txt):
    """
    Funció que rep el nom d'expedient (row_dict["expedient"]) i llegeix
    text lliure + OCR (si s'especifica) i retorna un .txt.

    Retorna un diccionari amb:
      - expedient
      - status
      - time
      - documents
      - pages

    Aquesta funció s'executa dins de cada procés del Pool.
    """
    global USE_OCR, OCR_MODEL

    exp_raw = str(row_dict["expedient"])
    exp = (
        exp_raw.replace("/", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )
    logging.info(f"Processant {exp}")

    pdf_dir = os.path.join(path_read_files, exp)
    output_txt_path = os.path.join(path_save_txt, f"{exp}.txt")

    start_time = datetime.now()
    full_text_all = ""

    documents_count = 0
    pages_count = 0

    try:
        if not os.path.exists(pdf_dir):
            return {
                "expedient": exp,
                "status": "Carpeta no trobada",
                "time": None,
                "documents": 0,
                "pages": 0,
            }

        fitxers = os.listdir(pdf_dir)
        if not any(fitxers):
            return {
                "expedient": exp,
                "status": "Carpeta buida",
                "time": None,
                "documents": 0,
                "pages": 0,
            }

        for file in fitxers:
            pdf_path = os.path.join(pdf_dir, file)

            if os.path.isdir(pdf_path):
                continue

            if not file.lower().endswith(".pdf"):
                continue

            documents_count += 1

            # Comptar pàgines si es pot
            try:
                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages_count += len(reader.pages)
            except Exception:
                pass

            # TEXT PLA
            full_text = read_files_text_images_cpu.plaintext_extraction_from_pdf(pdf_path)
            full_text_all += f"\n\n====== {file} - TEXT PLA ======\n{full_text.strip()}"

            # OCR (imatges)
            if USE_OCR:
                if OCR_MODEL is not None:
                    full_text_images = read_files_text_images_cpu.text_extraction_from_images_from_pdf(
                        pdf_file_fullpath=pdf_path,
                        ocr=OCR_MODEL,
                    )
                else:
                    # Fallback (no hauria de passar si init_worker està bé configurat)
                    full_text_images = read_files_text_images_cpu.text_extraction_from_images_from_pdf(
                        pdf_file_fullpath=pdf_path
                    )

                full_text_all += f"\n\n====== {file} - OCR ======\n{full_text_images.strip()}"

        # Guardar resultat del text
        if full_text_all.strip():
            os.makedirs(path_save_txt, exist_ok=True)
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(full_text_all)

        t = round((datetime.now() - start_time).total_seconds(),2)
        print(
            "expedient", exp,
            "status", "OK",
            "time", t,
            "documents", documents_count,
            "pages",  pages_count,
        )
        return {
            "expedient": exp,
            "status": "OK",
            "time": t,
            "documents": documents_count,
            "pages": pages_count,
        }

    except Exception as e:
        return {
            "expedient": exp,
            "status": f"Error: {e}",
            "time": None,
            "documents": documents_count,
            "pages": pages_count,
        }


def carregar_expedients_pendents(data_df, progress_path):
    """
    Llegeix el fitxer progress.csv (recull de: expedient, status, time, documents, pages)
    i, aquells que ja hi siguin, els treu de data_df per tant no els torna a fer.
    """
    if os.path.exists(progress_path):
        progress_df = pd.read_csv(progress_path)
        done = set(progress_df["expedient"])
        return data_df[~data_df["expedient"].isin(done)]
    return data_df.copy()


def append_result(result, progress_path):
    """
    Afegeix una fila al progress.csv amb el resultat d'un expedient.
    """
    file_exists = os.path.exists(progress_path)
    os.makedirs(os.path.dirname(progress_path) or ".", exist_ok=True)

    with open(progress_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["expedient", "status", "time", "documents", "pages"],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)

'''
def processar_timeboxed(
    data_df,
    path_read_files,
    path_save_txt,
    ocr,
    progress_path,
    max_workers,
    max_runtime_hours,
):
    """
    - Processa data_df amb multiprocessing.Pool (processos, no threads).
    - Deixa de llençar nous expedients quan max_runtime_hours s'ha superat,
      però deixa que acabin els que ja estaven en curs.
    - Afegeix les dades retornades al progress.csv.
    """
    start = time.time()
    max_runtime = max_runtime_hours * 3600

    results = []
    pending = list(data_df.iterrows())
    ocr_enabled = (ocr == "yes")

    # Converteix row (Series) a dict per facilitar pickling
    row_dicts = [(int(idx), row.to_dict()) for idx, row in pending]

    with Pool(
        processes=max_workers,
        initializer=init_worker,
        initargs=(ocr_enabled,),
    ) as pool:
        async_results = []
        iterator = iter(row_dicts)
        encolats = 0  # Comptador d'expedients encolats

        MAX_ENCOLATS = 5

        while True:
            elapsed = time.time() - start
            if elapsed > max_runtime:
                print("🏁 Temps màxim assolit. Parant d'enviar nous expedients.")
                break

             # Si queden menys de MAX_ENCOLATS encolats, encola un nou expedient
            if len(async_results) < MAX_ENCOLATS:
                try:
                    idx, row_dict = next(iterator)
                except StopIteration:
                    print("🎉 Tots els expedients pendents d'aquesta sessió han estat encolats al pool!")
                    break
                ar = pool.apply_async(
                    processar_expedient,
                    args=(row_dict, path_read_files, path_save_txt),
                )
                async_results.append(ar)
                encolats += 1
            else:
                # Si ja hi ha MAX_ENCOLATS, espera que s'alliberi algun worker
                time.sleep(0.1)
            # Processar resultats ja acabats per no acumular-los en memòria
            done_to_remove = []
            for ar_i in async_results:
                if ar_i.ready():
                    res = ar_i.get()
                    append_result(res, progress_path)
                    results.append(res)
                    done_to_remove.append(ar_i)

            # Esborrem els que ja hem processat
            if done_to_remove: #crec que similar a pending!!!!
                async_results = [x for x in async_results if x not in done_to_remove]

        # Esperar i processar tot el que queda pendent
        for ar in async_results:
            res = ar.get()
            append_result(res, progress_path)
            results.append(res)

    return results
'''
def processar_timeboxed(
    data_df,
    path_read_files,
    path_save_txt,
    ocr,
    progress_path,
    max_workers,
    max_runtime_hours,
):
    start = time.time()
    max_runtime = max_runtime_hours * 3600

    results = []
    pending = list(data_df.iterrows())
    ocr_enabled = (ocr == "yes")
    row_dicts = [(int(idx), row.to_dict()) for idx, row in pending]

    with Pool(
        processes=max_workers,
        initializer=init_worker,
        initargs=(ocr_enabled,),
    ) as pool:
        async_results = []
        iterator = iter(row_dicts)
        MAX_ENCOLATS = 5

        while True:
            # 1) Primer, recollim el que ja ha acabat
            done_to_remove = []
            for ar_i in async_results:
                if ar_i.ready():
                    res = ar_i.get()
                    append_result(res, progress_path)
                    results.append(res)
                    done_to_remove.append(ar_i)

            if done_to_remove:
                async_results = [x for x in async_results if x not in done_to_remove]

            # 2) Comprovem si hem exhaurit el temps
            elapsed = time.time() - start
            if elapsed > max_runtime:
                print("🏁 Temps màxim assolit. Parant d'enviar nous expedients.")
                break  # No encolarem res més, però després esperarem els pendents fora

            # 3) Si encara tenim temps i espai al "buffer", encolem més
            if len(async_results) < MAX_ENCOLATS:
                try:
                    idx, row_dict = next(iterator)
                    print("expedient encolat: ", row_dict)
                except StopIteration:
                    print("🎉 Tots els expedients pendents d'aquesta sessió han estat encolats al pool!")
                    break
                ar = pool.apply_async(
                    processar_expedient,
                    args=(row_dict, path_read_files, path_save_txt),
                )
                async_results.append(ar)
                print(
                    f"➡️ Encolat expedient {row_dict['expedient']}. "
                    f"Encolats actuals: {len(async_results)}/{MAX_ENCOLATS}"
                )

            else:
                # Massa encolats → esperem una mica
                time.sleep(0.1)

        # 4) Fora del while: esperem que acabin els que quedaven
        for ar in async_results:
            res = ar.get()
            append_result(res, progress_path)
            results.append(res)

    return results


def bucle_autorestart(
    data_df,
    path_read_files,
    path_save_txt,
    ocr,
    progress_path,
    max_workers,
    max_hours,
    cooldown_minutes,
):

    """
    Bucle que:
      - Processa els expedients pendents en sessions de max_hours hores.
      - Desa el progrés a progress.csv.
      - Descansa cooldown_minutes minuts entre sessions si encara falten expedients.
    """
    while True:
        print("──────────────────────────────────────────────")
        print("▶️  Iniciant sessió de processament…")
        print("──────────────────────────────────────────────")

        df_pendents = carregar_expedients_pendents(data_df, progress_path)
        logging.info(f"Pendents: {len(df_pendents)}")

        # Si no en queden → FINALITZA
        if len(df_pendents) == 0:
            print("🎉 TOTS ELS EXPEDIENTS ESTAN PROCESSATS!")
            print("🏆 Fi del procés. No queda res a fer.")
            return

        print(f"Queden {len(df_pendents)} expedients per processar.")
        print(f"Treballem durant un màxim de {max_hours} hores…")

        processar_timeboxed(
            df_pendents,
            path_read_files=path_read_files,
            path_save_txt=path_save_txt,
            ocr=ocr,
            progress_path=progress_path,
            max_workers=max_workers,
            max_runtime_hours=max_hours,
        )

        df_pendents_despres = carregar_expedients_pendents(data_df, progress_path)

        if len(df_pendents_despres) == 0:
            print("🎉 TOTS ELS EXPEDIENTS ESTAN PROCESSATS DURANT AQUESTA SESSIÓ!")
            print("🏆 Fi del procés. No queda res a fer.")
            return

        print("")
        print("🏁 Sessió acabada! Temps màxim assolit.")
        print(f"⏸ Esperant {cooldown_minutes} minuts abans de continuar…")
        print("")

        time.sleep(cooldown_minutes * 60)

    print("🏆 Procés completat. No queda res a fer.")

'''
if __name__ == "__main__":
    # Configurar logging en consola
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 1) Cargar el CSV de expedientes
    print("Leyendo CSV de expedients...")
    data_df = pd.read_csv(csv_path)  # ajusta sep=";" si hace falta
    print(f"Se han cargado {len(data_df)} expedients")

    # 2) Lanzar el bucle principal
    bucle_autorestart(
        data_df=data_df,
        path_read_files=path_read_files,
        path_save_txt=path_save_txt,
        ocr="no",  # o "yes" si quieres OCR
        progress_path=progress_path,
        max_workers=WORKERS,
        max_hours=WORK_TIME,
        cooldown_minutes=COOLDOWN,
    )
'''
