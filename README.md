# 📄 CPU-OCR Processor

Aplicació per processar expedients mitjançant **OCR**, lectura de PDFs i
generació automàtica de fitxers `.txt`, amb **threading**, control de
progrés i **autorestart** per evitar saturació de CPU o tancaments
inesperats.

## 📁 Estructura del projecte

    github-cpu-ocr/
    │
    ├── app/
    │   ├── data/
    │   │   ├── input_csv/
    │   │   │   └── expedients.csv
    │   │   ├── pdf_docs/
    │   │   ├── txt_results/
    │   │   └── progress.csv (es genera al inicialitzar)
    │   ├── src/
    │   │   ├── processing_cpu.py
    │   │   └── read_files_text_images_cpu.py
    │   ├── utils/
    │   └── main.py
    │
    ├── poppler-24.08.0/
    ├── requirements.txt
    ├── dockerfile
    └── README.md

## 🚀 Funcionalitats principals

-   Llegeix un CSV amb una columna d'expedients.
-   Normalitza automàticament els noms dels expedients.
-   Llegeix carpetes amb PDFs.
-   Aplica OCR (`yes` / `no`).
-   Desa resultats `.txt`.
-   Manté un `progress.csv` per continuar el processament si es
    reinicia.
-   Utilitza **multithreading**.
-   Sistema d'**autorestart** amb límit horari i cooldown programat.

## 🔧 Instal·lació

### 1. Instal·lar dependències

    pip install -r requirements.txt

### 2. Poppler (necessari per a PDF → imatge)

**Windows:** inclòs al projecte (`poppler-24.08.0/`)

**Linux/Mac:**

    sudo apt install poppler-utils

## ▶️ Ús

### Executar amb valors predeterminats

    python app/main.py

### Executar amb paràmetres personalitzats

    python app/main.py     --csv-path ruta/al/csv.csv     --read-pdfs ruta/als/pdfs     --save-txt ruta/resultats     --progress-path ruta/progres.csv     --ocr yes     --max-workers 5     --max-hours 1.5     --cooldown-minutes 10

## ⚙️ Arguments disponibles

  ------------------------------------------------------------------------------
  Argument               Descripció            Valor per defecte
  ---------------------- --------------------- ---------------------------------
  `--csv-path`           CSV amb columna       `data/input_csv/expedients_cpu.csv`
                         `expedient`           

  `--read-pdfs`          Carpeta amb PDFs      `data/pdf_docs/`

  `--save-txt`           Carpeta resultats TXT `data/txt_results/`

  `--progress-path`      Fitxer de progrés     `data/progress.csv`

  `--ocr`                Activa o desactiva    `yes`
                         OCR                   

  `--max-workers`        Nº de threads         `5`

  `--max-hours`          Hores màximes per     `7.0`
                         sessió                

  `--cooldown-minutes`   Minuts de pausa       `30.0`
  ------------------------------------------------------------------------------

## 🔁 Funcionament del bucle d'autorestart

1.  Processa expedients durant `max-hours`.
2.  Desa progrés al `progress.csv`.
3.  Fa una pausa (`cooldown-minutes`).
4.  Reinicia el procés i continua pels expedients pendents.

## 🐳 Docker

### Build

    docker build -t cpu-ocr .

### Run

    docker run -it cpu-ocr

## 👩‍💻 Desenvolupament

-   `main.py`: entrada principal, gestió de paràmetres i configuració.
-   `processing_cpu.py`: processament multithread i autorestart.
-   `read_files_text_images_cpu.py`: lectura de PDFs, imatges i OCR.
-   `utils/`: funcions auxiliars.