import csv
import requests
import time
import urllib.parse
import argparse

def obtener_criticidad(cvss_score):
    """Devuelve la etiqueta de criticidad en base al puntaje CVSS."""
    if cvss_score == 0.0:
        return "INFO"
    elif cvss_score < 4.0:
        return "BAJO"
    elif cvss_score < 7.0:
        return "MEDIO"
    elif cvss_score < 9.0:
        return "ALTO"
    else:
        return "CRÍTICO"

def etiquetar_dataset(input_csv, output_csv, api_key):
    # Endpoint de la API REST 2.0 de la NVD
    url_base = "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch="
    headers = {"apiKey": api_key}
    
    filas_procesadas = 0
    nuevas_filas = 0

    with open(input_csv, mode='r', encoding='utf-8') as f_in, \
         open(output_csv, mode='w', newline='', encoding='utf-8') as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        # Leer encabezados y agregar las nuevas columnas para el modelo
        headers_csv = next(reader)
        writer.writerow(headers_csv + ['CVE', 'CVSS_Score', 'Criticidad'])
        
        for row in reader:
            filas_procesadas += 1
            ip, puerto, protocolo, servicio, version = row
            
            # Si no tenemos versión exacta, lo marcamos como INFO y seguimos
            if version.lower() == "desconocido" or not version.strip():
                writer.writerow(row + ['Ninguno', 0.0, 'INFO'])
                nuevas_filas += 1
                continue
            
            print(f"[*] Consultando NVD para: {servicio} {version} (Puerto {puerto})...")
            
            # Codificamos la cadena de búsqueda para la URL
            search_query = urllib.parse.quote(f"{servicio} {version}")
            url = f"{url_base}{search_query}"
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilidades = data.get('vulnerabilities', [])
                    
                    if not vulnerabilidades:
                        # No hay CVEs conocidos para esta versión exacta
                        writer.writerow(row + ['Ninguno', 0.0, 'INFO'])
                        nuevas_filas += 1
                    else:
                        # Si encontramos vulnerabilidades, creamos una fila por cada CVE
                        for vuln in vulnerabilidades:
                            cve_id = vuln['cve']['id']
                            metrics = vuln['cve'].get('metrics', {})
                            
                            # Extraer CVSS (Priorizamos v3.1 > v3.0 > v2)
                            cvss_score = 0.0
                            if 'cvssMetricV31' in metrics:
                                cvss_score = metrics['cvssMetricV31'][0]['cvssData']['baseScore']
                            elif 'cvssMetricV30' in metrics:
                                cvss_score = metrics['cvssMetricV30'][0]['cvssData']['baseScore']
                            elif 'cvssMetricV2' in metrics:
                                cvss_score = metrics['cvssMetricV2'][0]['cvssData']['baseScore']
                            
                            criticidad = obtener_criticidad(cvss_score)
                            
                            # Escribimos la nueva fila desdoblada en el dataset
                            writer.writerow(row + [cve_id, cvss_score, criticidad])
                            nuevas_filas += 1
                            
                else:
                    print(f"[!] Error de API {response.status_code} al buscar {version}")
                    writer.writerow(row + ['Error_API', 0.0, 'INFO'])
                    nuevas_filas += 1

            except Exception as e:
                print(f"[!] Error de conexión: {e}")
                writer.writerow(row + ['Error_Conexion', 0.0, 'INFO'])
                nuevas_filas += 1
            
            # Control de Rate Limit: La NVD con API Key permite aprox 50 requests / 30 seg.
            # Metemos un pequeño delay de 0.6 segundos por iteración para cuidar la cuota.
            time.sleep(0.6)

    print("\n" + "="*50)
    print(f"¡Etiquetado finalizado!")
    print(f"Puertos analizados: {filas_procesadas}")
    print(f"Filas resultantes en el dataset: {nuevas_filas}")
    print(f"Dataset final guardado en: {output_csv}")
    print("="*50)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Consulta NVD API y etiqueta dataset.")
    parser.add_argument('-i', '--input', required=True, help="CSV de entrada generado por Nmap")
    parser.add_argument('-o', '--output', default="dataset_final.csv", help="CSV etiquetado de salida")
    parser.add_argument('-k', '--key', required=True, help="API Key de la NVD")
    
    args = parser.parse_args()
    etiquetar_dataset(args.input, args.output, args.key)