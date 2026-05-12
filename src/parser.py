import xml.etree.ElementTree as ET
import csv
import argparse

def parse_nmap_xml(xml_file, output_csv):
	# Cargamos y parseamos el archivo XML
	try:
		tree = ET.parse(xml_file)
		root = tree.getroot()
	except FileNotFoundError:
		print(f"Error: No se encontro el archivo {xml_file}")
		return

	# Abrimos el archivo CSV de salida en modo escritura
	with open(output_csv, mode='w', newline='', encoding='utf-8') as csv_file:
		writer = csv.writer(csv_file)

		# Escribimos los encabezados de las columnas (las features)
		writer.writerow(['IP', 'Puerto', 'Protocolo', 'Servicio', 'Version_Completa'])

		hallazgos = 0

		# Iteramos sobre cada host escaneado
		for host in root.findall('host'):
			ip_address = 'Desconocida'

			# Extraemos la direccion IPv4
			for address in host.findall('address'):
				if address.get('addrtype') == 'ipv4':
					ip_address = address.get('addr')
					break

			# Buscamos la seccion de puertos
			ports_section = host.find('ports')
			if ports_section is not None:
				for port in ports_section.findall('port'):
					state = port.find('state')

					# Filtramos solo los puertos que esten "open"
					if state is not None and state.get('state') == 'open':
						port_id = port.get('portid')
						protocol = port.get('protocol')

						service = port.find('service')
						service_name = "desconocido"
						service_version = "desconocido"

						if service is not None:
							service_name = service.get('name', 'desconocido')
							product = service.get('product', '')
							version = service.get('version', '')
							extrainfo = service.get('extrainfo', '')

							# Concatenamos producto, version e info extra para tener el feature completo
							version_full = f"{product} {version} {extrainfo}".strip()

							if version_full:
								service_version = version_full

						# Escribimos la fila del hallazgo en el CSV
						writer.writerow([ip_address, port_id, protocol, service_name, service_version])
						hallazgos += 1

	print(f"¡Exito! Se genero el archivo '{output_csv}' con {hallazgos} puertos/servicios detectados.")

# Bloque para leer el archivo pasado por parametros
if __name__ == '__main__':
	# Configuramos el parser de la terminal
	parser = argparse.ArgumentParser(description="Parsea un archivo XML de Nmap y extrae features a un CSV.")

	# Definimos la flag -i para el XML
	parser.add_argument('-i', '--input', required=True, help="Ruta del archivo XML de Nmap (ej: ../data/dataset.xml)")

	# Definimos la flag -o para el CSV
	parser.add_argument('-o', '--output', default="hallazgos_nmap.csv", help="Ruta del archivo CSV de salida")

	# Leemos los argumentos pasados por consola
	args = parser.parse_args()

	# Ejecutamos la funcion pasandole los argumentos
	parse_nmap_xml(args.input, args.output)

