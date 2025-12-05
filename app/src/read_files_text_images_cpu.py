import sys
sys.path.append("")
from pathlib import Path
import os

import numpy as np
import pymupdf
import cv2
from pdf2image import convert_from_path

#from utils import print_utils

from paddleocr import PaddleOCR


def pymupdf_pixmap_to_numpy(pixmap):
    """Convertir pymupdf.Pixmap a un array (compatible como input para PaddleOCR)."""
    img_array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.h, pixmap.w, pixmap.n)

    # Convertir a RGB si es necesario
    if pixmap.n == 4:  # RGBA / CMYK asimilado
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
    elif pixmap.n == 1:  # Escala de grises
        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)

    return img_array


def text_extraction_from_images_from_pdf(pdf_file_fullpath, ocr: PaddleOCR | None = None):
    """
    Extrae texto de las imágenes embebidas en un PDF usando PaddleOCR.

    Parámetros
    ----------
    pdf_file_fullpath : str | Path
        Ruta completa al PDF.
    ocr : PaddleOCR | None
        Instancia ya inicializada de PaddleOCR.
        - Si se pasa (recomendado para multiprocessing), se reutiliza.
        - Si es None, se crea una instancia local para este PDF.
    """
    dims_duple_NoTextImages_l = []  # (width, height) de imágenes donde no se ha extraído texto
    pix_d = {}

    pdf_file_fullpath = str(pdf_file_fullpath)
    doc = pymupdf.open(pdf_file_fullpath)

    # -------------------------------------------------------------------------
    # 1) Extraer todas las imágenes (como Pixmap) por página
    # -------------------------------------------------------------------------
    for i_page, page in enumerate(doc.pages()):
        pix_d[f"{i_page}"] = {}
        for image_index, img in enumerate(page.get_images(), start=1):
            xref = img[0]
            pix = pymupdf.Pixmap(doc, xref)

            if pix.colorspace is not None:
                # TODO: diferenciar RGB/GRAY/CMYK si quisieras afinar más
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            else:
                # Caso "mask" sin colorspace -> usar extract_image
                base_image = doc.extract_image(xref)
                if base_image["colorspace"] == 1:
                    pix = pymupdf.Pixmap(pymupdf.csGRAY, pymupdf.Pixmap(base_image["image"]))
                else:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.Pixmap(base_image["image"]))

            pix_d[f"{i_page}"][f"{image_index}"] = pix

    # -------------------------------------------------------------------------
    # 2) Inicializar OCR (una sola vez por llamada, o reutilizar el pasado)
    # -------------------------------------------------------------------------
    if ocr is None:
        print("Inicializando PaddleOCR (instancia local para este PDF)...")
        ocr_instance = PaddleOCR(use_angle_cls=True, lang="es", cpu_threads=4)
    else:
        ocr_instance = ocr

    # -------------------------------------------------------------------------
    # 3) Ejecutar OCR sobre las imágenes
    # -------------------------------------------------------------------------
    extractedTextFromImages_wholeDoc = (
        " -------------------------------- Inicio de Documento "
        "(Texto extraido de imágenes) ------------------------------------- \n"
    )

    for i_page in pix_d.keys():
        extractedText_wholeDoc = ""

        # Caso con muchas imágenes -> probablemente página escaneada
        if len(pix_d[i_page]) >= 10:
            #print(f"{print_utils.strYellow('Posible página escaneada! (Num images>=10)')} page: {i_page}")
            print("Convirtiendo la página a imagen... ")
            try:
                '''
                images = convert_from_path(
                    pdf_file_fullpath,
                    poppler_path=os.path.join("poppler-24.08.0", "Library", "bin"),
                )
                '''



                # Ruta absoluta a la raíz del repositorio:
                # .../GITHUB-CPU-OCR/app/src/read_files_text_images_cpu.py
                # parents[0] = src
                # parents[1] = app
                # parents[2] = GITHUB-CPU-OCR (arrel del repo)
                PROJECT_ROOT = Path(__file__).resolve().parents[2]

                POPPLER_BIN = PROJECT_ROOT / "poppler-24.08.0" / "Library" / "bin"


                images = convert_from_path(
                pdf_file_fullpath,
                poppler_path=str(POPPLER_BIN),
)
                png_filename = f'{Path(pdf_file_fullpath).with_suffix("")}_PAGE{i_page}.png'
                images[int(i_page)].save(png_filename, format="PNG")

                image_doc = pymupdf.open(png_filename)
                pix = image_doc[0].get_pixmap()
                pix_d[f"{i_page}"] = {}
                pix_d[f"{i_page}"][f"0_PageToImg"] = pix

                os.remove(png_filename)
            except Exception as e:
                print(f"Error convirtiendo la pagina {i_page} a imagen")
                print(e)

        # Imágenes de la página (metadatos / contenido embebido)
        extractText_ByPage = ""
        for pix_image_index, pix_v in pix_d[f"{i_page}"].items():
            print(
                f"\n ---- Page: {i_page} -- # images: {len(pix_d[f'{i_page}'])}, "
                f"({pix_v.width}, {pix_v.height})"
            )
            print(f"listado dimensiones a no comprobar: {dims_duple_NoTextImages_l}")

            if (pix_v.width >= 100 or pix_v.height >= 100) and (
                (pix_v.width, pix_v.height) not in dims_duple_NoTextImages_l
            ):
                img = pymupdf_pixmap_to_numpy(pix_v)
                print("Se inicia OCR... ")

                result = ocr_instance.ocr(img, cls=True)

                # Manejo robusto de result
                if result and result[0] is not None:
                    found_words_l = [line[1][0] for line in result[0]]
                    if found_words_l:
                        for w in found_words_l:
                            extractText_ByPage += f" {w}"
                            extractedText_wholeDoc += f" {w}"
                    else:
                        print(f"page_{i_page}-image_{pix_image_index}.png: Sin coincidencias!")
                        dims_duple_NoTextImages_l.append((pix_v.width, pix_v.height))
                else:
                    print("Sin palabras!")
                    dims_duple_NoTextImages_l.append((pix_v.width, pix_v.height))

        extractedTextFromImages_wholeDoc += extractedText_wholeDoc
        extractedTextFromImages_wholeDoc += (
            f"\n\n-------------------------------- Fin Página {i_page} ------------------------------------- \n"
        )

    return extractedTextFromImages_wholeDoc


def plaintext_extraction_from_pdf(pdf_file_fullpath):
    """
    Extracción de texto plano de un PDF (sin OCR, solo texto embebido).
    """
    doc = pymupdf.open(pdf_file_fullpath)
    plain_text = ""

    for page in doc.pages():
        page_text = page.get_text()
        page_text = page_text.replace("\n", " ")
        plain_text += page_text

    return plain_text
