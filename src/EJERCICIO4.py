import csv
import random
import json
import copy
import pandas as pd

def convertir_json(filename, capacity, max_rs):
    # Instancio las componentes de mi instancia
    instance = {}
    instance['services'] = {}
    instance['stations'] = []
    instance['cost_per_unit'] = {}
    instance['rs_info'] = {'capacity': capacity, 'max_rs': max_rs}

    # Leer el archivo CSV
    df = pd.read_csv(filename + '.csv')
    for index, row in df.iterrows():
        # ID del servicio
        service_id = str(index)

        # Crear las paradas (stops) como diccionarios etiquetados
        stops = [
            {
                "time": int(row[1]),       # Hora de salida
                "station": row[2],         # Estación de origen
                "type": row[3]             # Tipo de evento (D o A)
            },
            {
                "time": int(row[4]),       # Hora de llegada
                "station": row[5],         # Estación de destino
                "type": row[6]             # Tipo de evento (D o A)
            }
        ]

        # Extraer la demanda
        demand = [int(row[7])]

        # Agregar el servicio a la instancia
        instance['services'][service_id] = {
            "stops": stops,
            "demand": demand
        }

        # Agregar las estaciones si no están ya en la lista
        if row[2] not in instance['stations']:
            instance['stations'].append(row[2])
        if row[5] not in instance['stations']:
            instance['stations'].append(row[5])

    # Asignar costos por unidad para cada estación
    for station in instance['stations']:
        instance['cost_per_unit'][station] = 1

    # Guardar el archivo JSON
    with open(filename + '.json', 'w') as jsonfile:
        json.dump(instance, jsonfile, indent=4)

    return instance



filename = "src/ejercicio4"

capacity = 100
max_rs = 5

convertir_json(filename,capacity,max_rs)