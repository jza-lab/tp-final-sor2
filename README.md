# Proyecto Final SOR2 - Análisis de Vulnerabilidades y Machine Learning

Este proyecto implementa un pipeline automatizado para el procesamiento de escaneos de seguridad de red (Nmap), el etiquetado de vulnerabilidades mediante la consulta a la base de datos de la NVD (National Vulnerability Database) y la clasificación de criticidad utilizando un modelo de Machine Learning (Random Forest).

---

## 🛠️ Requisitos Previos y Configuración

Antes de ejecutar los scripts, asegúrese de contar con las librerías necesarias instaladas en su entorno de Python:

```bash
pip install pandas scikit-learn requests
```

### Configuración de la API Key de la NVD
La API de la NVD restringe severamente las consultas sin credenciales. Se recomienda obtener una API Key gratuita y exportarla temporalmente como variable de entorno en su terminal antes de correr el etiquetador:

```bash
export NVD_KEY=<TU_API_KEY_AQUI>
```

---

## 🚀 Guía de Uso y Detalle de los Programas

El código está estructurado de forma modular dentro del directorio `src/`. A continuación, se detalla el funcionamiento, parámetros y ejemplos exactos de ejecución para cada script.

### 1. Parseo de Escaneos (`src/parser.py`)
Este script lee un archivo de reporte en formato XML generado por Nmap, filtra únicamente los puertos que se encuentran abiertos (`open`) y extrae características clave (IP, Puerto, Protocolo, Servicio y Versión Completa) para consolidarlas en un archivo estructurado CSV.

**Sintaxis de ejecución:**
```bash
python src/parser.py -i <RUTA_XML_ENTRADA> [-o <RUTA_CSV_SALIDA>]
```

**Parámetros:**
*   `-i`, `--input` (**Obligatorio**): Ruta del archivo XML de Nmap (ej. `../data/dataset.xml`).
*   `-o`, `--output` (Opcional): Ruta del archivo CSV de salida. Por defecto genera `hallazgos_nmap.csv`.
*   `-h`, `--help`: Muestra la descripción detallada de cada parámetro por terminal.

**Ejemplo Práctico:**
```bash
python src/parser.py -i ../data/dataset.xml
```

### 2. Etiquetado Automático con NVD (`src/etiquetador_nvd.py`)
Toma el CSV con los hallazgos de Nmap y consulta de forma automatizada la API REST 2.0 de la NVD utilizando la cadena de búsqueda de cada servicio y versión detectados. 

El script extrae el identificador del CVE, el puntaje CVSS (priorizando la métrica v3.1, luego v3.0 y finalmente v2) y asigna una etiqueta de criticidad (INFO, BAJO, MEDIO, ALTO o CRÍTICO) basada en dicho puntaje. Si una versión tiene múltiples vulnerabilidades asociadas, el script desdobla la información generando una fila por cada CVE en el dataset resultante. Incorpora un delay de 0.6 segundos por petición para respetar la cuota del Rate Limit de la API.

**Sintaxis de ejecución:**
```bash
python src/etiquetador_nvd.py -i <CSV_ENTRADA> -k <API_KEY> [-o <CSV_SALIDA>]
```

**Parámetros:**
*   `-i`, `--input` (**Obligatorio**): Archivo CSV de entrada generado previamente por el parser (ej. `hallazgos_nmap.csv`).
*   `-k`, `--key` (**Obligatorio**): API Key válida de la NVD para autorizar las consultas.
*   `-o`, `--output` (Opcional): Ruta del archivo CSV de salida enriquecido. Por defecto genera `dataset_final.csv`.

**Ejemplo Práctico:**
```bash
python src/etiquetador_nvd.py -i hallazgos_nmap.csv -o dataset_final.csv -k $NVD_KEY
```

### 3. Pipeline de Machine Learning (`src/modelo.py`)
Este programa ejecuta el ciclo completo de entrenamiento, evaluación interna y pruebas comparativas de un clasificador basado en el algoritmo Random Forest. No requiere parámetros por consola ya que lee las rutas estáticas predefinidas en el directorio `data/`.

**Sintaxis de ejecución:**
```bash
python src/modelo.py
```

**Etapas del Proceso Interno:**
*   **Codificación de Vocabulario:** Utiliza `LabelEncoder` entrenado con el dataset completo (`dataset_final.csv`) para prevenir errores de etiquetas no vistas (*unseen labels*) al procesar servicios poco frecuentes.
*   **Evaluación Cruzada (Stratified K-Fold):** Aplica una división de 5 splits sobre el archivo `dataset_entrenamiento.csv` para obtener un F1-Score macro promedio y un reporte de clasificación realista y libre de sobreajuste (*data leakage*).
*   **Entrenamiento Final:** Ajusta el modelo definitivo utilizando hiperparámetros balanceados (`class_weight='balanced'`) para mitigar el desbalance de clases.
*   **Comparativa contra Baseline:** Evalúa el modelo entrenado sobre las 50 filas del archivo `baseline_manual.csv` y calcula los porcentajes de precisión del modelo y del criterio manual (Joaquín) tomando como árbitro la criticidad oficial de la NVD.
*   **Casos de Estudio:** Imprime de manera automatizada las discrepancias encontradas en servicios específicos como `bindshell`, `exec` y `ajp13`.

### 4. Entorno de Comparación Manual (`src/comparador.py`)
Es una versión simplificada del pipeline enfocada exclusivamente en analizar y mostrar en formato tabular los resultados detallados del baseline manual frente al modelo predictivo. Tampoco requiere argumentos por consola.

**Sintaxis de ejecución:**
```bash
python src/comparador.py
```

**Salida en Consola:**
*   Imprime una tabla completa que alinea puerto, servicio, versión y las tres clasificaciones en paralelo: `Criticidad_NVD`, `Criticidad_Joaquin` y `Criticidad_Modelo`.
*   Calcula y muestra el total de aciertos absolutos (sobre 50) y el porcentaje de eficacia tanto del analista humano como del modelo de Machine Learning.

---

## 🔄 Flujo de Trabajo Recomendado

Para reproducir el experimento completo desde cero, siga el orden secuencial de los comandos:

1. **Parsear el XML original:**
   ```bash
   python src/parser.py -i ../data/dataset.xml -o hallazgos_nmap.csv
   ```

2. **Etiquetar con la API:**
   ```bash
   python src/etiquetador_nvd.py -i hallazgos_nmap.csv -o dataset_final.csv -k $NVD_KEY
   ```

3. **Ejecutar el pipeline de Machine Learning y ver métricas:**
   ```bash
   python src/modelo.py
   ```

4. **Inspeccionar la tabla comparativa de aciertos:**
   ```bash
   python src/comparador.py
   ```
````</CSV_SALIDA></API_KEY></CSV_ENTRADA></RUTA_CSV_SALIDA></RUTA_XML_ENTRADA>
