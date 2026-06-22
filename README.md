# 🔍 Pipeline VulnLabel — Clasificación automática de vulnerabilidades con ML

> Pipeline de Machine Learning para clasificar y priorizar automáticamente la criticidad de vulnerabilidades detectadas en escaneos de red con Nmap.

---

## 📋 Descripción

Este proyecto automatiza la clasificación de riesgos en auditorías de seguridad informática utilizando Machine Learning. Dado el output crudo de Nmap (XML), el sistema predice automáticamente la criticidad de cada hallazgo en categorías estándar de la industria (`CRÍTICO / ALTO / MEDIO / BAJO / INFO`) sin intervención manual.

**Problema que resuelve:** la priorización manual de vulnerabilidades es lenta y subjetiva. En 2025 se publicaron más de 42.000 nuevas vulnerabilidades (CVEs), lo que equivale a más de 115 por día. Con este volumen, resulta inviable que un analista clasifique manualmente cada hallazgo de un escaneo de red.

---

## 🏗️ Arquitectura del Pipeline

```
Escaneo Nmap (XML)
        │
        ▼
  [parser.py]              → Extrae features: puerto, protocolo, servicio, versión
        │
        ▼
[etiquetador_nvd.py]       → Consulta NVD API → obtiene CVSS score → asigna etiqueta
        │
        ▼
   [modelo.py]             → Entrena Random Forest → predice criticidad
        │
        ▼
  [comparador.py]          → Evalúa modelo vs clasificación manual del analista
        │
        ▼
 Reporte priorizado por criticidad
```

---

## 📦 Contribuciones originales

### 1. Pipeline VulnLabel
Sistema automático y reproducible compuesto por cuatro módulos:

| Módulo | Función |
|--------|---------|
| `parser.py` | Parsea XML de Nmap y extrae features por puerto abierto |
| `etiquetador_nvd.py` | Consulta la NVD API para obtener puntajes CVSS y construir el ground truth |
| `modelo.py` | Entrena, valida y evalúa el clasificador Random Forest |
| `comparador.py` | Compara el rendimiento del modelo vs la clasificación manual del analista |

### 2. Dataset NmapVuln-622
Dataset original de **622 hallazgos de seguridad** etiquetados por criticidad CVSS, generado sobre 5 targets heterogéneos (Linux y Windows):

| Target | Archivo |
|--------|---------|
| Metasploitable 2 | `data/Metasploitable2/dataset_Metasploitable2.xml` |
| OWASP BWA | `data/OWASPBWA/dataset_owaspbwa.xml` |
| BasicPentesting1 | `data/BasicPentesting1/dataset_basicpentesting1.xml` |
| Windows 7 | `data/Windows7/dataset_windows7.xml` |
| Windows 8 | `data/Windows8/dataset_windows8.xml` |

---

## 🗂️ Estructura del repositorio

```
tp-final-sor2/
├── README.md
├── requirements.txt
├── data/
│   ├── BasicPentesting1/
│   │   └── dataset_basicpentesting1.xml
│   ├── Metasploitable2/
│   │   └── dataset_Metasploitable2.xml
│   ├── OWASPBWA/
│   │   └── dataset_owaspbwa.xml
│   ├── Windows7/
│   │   └── dataset_windows7.xml
│   ├── Windows8/
│   │   └── dataset_windows8.xml
│   ├── dataset.xml                  # XML combinado de todos los targets
│   ├── dataset_entrenamiento.csv    # Subset usado para entrenar el modelo
│   ├── dataset_final.csv            # Dataset completo etiquetado (NmapVuln-622)
│   └── baseline_manual.csv          # Clasificación manual del analista (50 hallazgos)
├── results/
│   ├── ejecucion_parser.png
│   ├── ejecucion_etiquetador.png
│   ├── resultado_etiquetador.png
│   ├── ejecucion_modelo.png
│   ├── ejecucion_comparadorP1.png
│   └── ejecucion_comparadorP2png
└── src/
    ├── parser.py
    ├── etiquetador_nvd.py
    ├── modelo.py
    ├── comparador.py
    └── hallazgos_nmap.csv           # Output intermedio generado por parser.py
```

---

## 🛠️ Instalación

### Requisitos previos
- Python 3.8+
- Nmap instalado (`sudo apt install nmap`)
- API Key de la NVD ([registrarse aquí](https://nvd.nist.gov/developers/request-an-api-key))

### Instalación de dependencias

```bash
git clone https://github.com/jza-lab/tp-final-sor2
cd tp-final-sor2
```

---

## 🚀 Uso

### Paso 1 — Escanear los targets con Nmap

```bash
sudo nmap -p- -sV -sC -oX data/dataset.xml <IP_TARGET>
```

**Flags utilizados:**
- `-p-` → escanea los 65.535 puertos TCP (evita sesgo de los top 1000)
- `-sV` → detección de versiones mediante banner grabbing
- `-sC` → scripts NSE por defecto para metadatos adicionales
- `-oX` → exporta en XML para ingesta automatizada

### Paso 2 — Parsear el XML y extraer features

```bash
python src/parser.py -i data/dataset.xml
```

Genera `src/hallazgos_nmap.csv` con columnas: `IP, Puerto, Protocolo, Servicio, Version_Completa`

### Paso 3 — Etiquetar con la NVD API

```bash
python src/etiquetador_nvd.py -i src/hallazgos_nmap.csv -k $NVD_KEY
```

Genera `data/dataset_final.csv` con columnas adicionales: `CVE, CVSS_Score, Criticidad`

**Lógica de etiquetado:**

| CVSS Score | Criticidad |
|------------|------------|
| Sin CVE | INFO |
| < 4.0 | BAJO |
| 4.0 – 6.9 | MEDIO |
| 7.0 – 8.9 | ALTO |
| ≥ 9.0 | CRÍTICO |

### Paso 4 — Entrenar y evaluar el modelo

```bash
python src/modelo.py
```

### Paso 5 — Comparar modelo vs analista humano

```bash
python src/comparador.py
```

---

## 🤖 Decisiones técnicas

### Modelo: Random Forest (Balanced)
Se eligió Random Forest frente a Gradient Boosting y SVM por:
- **Robustez** ante variables heterogéneas (numéricas y categóricas)
- **Interpretabilidad** de los resultados
- **Mitigación de desbalance** vía `class_weight='balanced'` de forma nativa

### Ground Truth: NVD API
Se usa el puntaje CVSS oficial de la National Vulnerability Database como etiqueta de verdad absoluta por ser el estándar universal de la industria.

**Limitación identificada:** la NVD clasifica según CVEs documentados e ignora la peligrosidad contextual. Servicios extremadamente peligrosos sin CVE registrado (como una shell de root expuesta en el puerto 1524) son catalogados como `INFO`.

### Validación: Stratified K-Fold (k=5)
Se utiliza validación cruzada estratificada para mitigar el sobreajuste dado el tamaño reducido del dataset, preservando la proporción de clases en cada pliegue.

---

## 📊 Resultados

### Validación cruzada (K-Fold, k=5)

| Métrica | Valor |
|---------|-------|
| F1-score macro promedio | **0.978** |
| Desviación estándar | ± 0.023 |

**Reporte por clase:**

| Clase | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| ALTO | 0.99 | 1.00 | 0.99 | 142 |
| BAJO | 1.00 | 0.96 | 0.98 | 24 |
| CRÍTICO | 1.00 | 0.94 | 0.97 | 52 |
| INFO | 0.86 | 1.00 | 0.92 | 12 |
| MEDIO | 1.00 | 1.00 | 1.00 | 287 |

### Comparativa vs baseline manual

| Clasificador | Aciertos vs NVD |
|---|---|
| Analista humano (con contexto) | 3/50 (6%) |
| **Modelo de ML** | **48/50 (96%)** |

**Hallazgo clave:** la brecha no indica falla del analista, sino una limitación estructural de la NVD. El analista clasificó correctamente como `CRÍTICO` servicios como `bindshell` (puerto 1524), `exec` (puerto 512) y `ajp13` (puerto 8009), que la NVD etiqueta como `INFO` por carecer de CVE registrado.

### Casos de estudio — Discrepancia de criterios

| Puerto | Servicio | Criticidad NVD | Criticidad Analista | Criticidad Modelo |
|--------|----------|----------------|---------------------|-------------------|
| 1524 | bindshell | INFO | CRÍTICO | INFO |
| 512 | exec | INFO | CRÍTICO | INFO |
| 8009 | ajp13 | INFO | CRÍTICO | INFO |

---

## 🔬 Capas OSI involucradas

| Capa | Función | Amenaza | Mitigación |
|------|---------|---------|------------|
| **Capa 3 (Red)** | Descubrimiento de hosts | Filtrado de ICMP por firewall | Uso de `-Pn` para forzar resolución |
| **Capa 4 (Transporte)** | Estado de los 65.535 puertos TCP/UDP | Rate-limiting del host | Parámetro `-T4` para balance velocidad/fidelidad |
| **Capa 7 (Aplicación)** | Extracción de banners y versiones | Banner grabbing alterado (ofuscación) | Scripts heurísticos NSE para verificar identidad real |

---

## ⚠️ Limitaciones conocidas

1. **Sesgo del ground truth (NVD):** el modelo hereda las limitaciones de la NVD al no reconocer servicios peligrosos sin CVE documentado.
2. **Desbalance de clases:** el entorno experimental concentra hallazgos en `INFO` y `MEDIO`, lo que limita la representatividad de clases como `CRÍTICO` o `BAJO`.

---

## 🔮 Trabajo a futuro

1. **Corrección heurística del ground truth:** módulo de post-procesamiento que aplique reglas expertas para reclasificar servicios peligrosos catalogados como `INFO` (backdoors, shells expuestas, puertos críticos sin CVE).
2. **Ingesta multifuente:** incorporar reportes de Nikto (Capa 7) y OpenVAS para enriquecer el vector de características.
3. **Validación en infraestructura real:** despliegue pasivo en redes de producción para evaluar rendimiento ante ruido de red, firewalls e IDS/IPS.

---

## 📚 Referencias

- Tiwari, H. (2025). *Advancing Vulnerability Classification with BERT: A Multi-Objective Learning Model.* arXiv. https://arxiv.org/abs/2503.20831
- Choi et al. (2025). *Vulnerability2VEC: A Graph-Embedding approach for enhancing vulnerability classification.* CMES, 144(3).
- Roy, A. et al. (2026). *AI-Driven Supervised Classification Algorithm for website Vulnerability detection using MITRE NVD CVE scores.* Preprints.org.
- Saklani, S. & Kalia, A. (2025). *Severity prediction of software vulnerabilities using CNNs.* Information and Computer Security, 33(4).
- Nowak et al. (2023). *Support for the vulnerability management process using conversion CVSS base score 2.0 to 3.x.* Sensors, 23(4).
- Greig, J. (2026). *NIST to limit work on CVE entries as submissions surge.* The Record.

---

## 🏫 Contexto académico

Trabajo Final — Sistemas Operativos y Redes 2 (Primer Semestre 2026)  
Universidad Nacional de General Sarmiento — Instituto de Industria  
Licenciatura en Sistemas
