import pandas as pd
import json

def csv_to_instance(csv_file):
    # Leer el archivo CSV
    df = pd.read_csv("src/ejercicio4.csv")
    
    # Extraer las estaciones cabecera (asumimos que son únicas y están en las columnas 'origen' y 'destino')
    stations = list(df['origen'].unique())  # Aquí asumimos que origen y destino contienen todas las estaciones
    
    # Lista fija según el contexto
    cost_per_unit = [1, 1]
    
    # Construir el diccionario de servicios
    services = {}
    for index, row in df.iterrows():
        service_id = str(row['service id'])
        
        # Representar cada parada como un diccionario con claves explícitas
        stops = [
            {
                "time": row['hora'],       # Reemplaza con el nombre exacto de la columna para la hora
                "station": row['origen'],  # Reemplaza con el nombre exacto de la columna para la estación de origen
                "type": row['tipo']        # Reemplaza con el nombre exacto de la columna para el tipo (D o A)
            },
            {
                "time": row['hora.1'],     # Reemplaza con el nombre exacto de la columna para la hora de destino
                "station": row['destino'], # Reemplaza con el nombre exacto de la columna para la estación de destino
                "type": row['tipo.1']      # Reemplaza con el nombre exacto de la columna para el tipo de destino (D o A)
            }
        ]
        
        # La demanda sigue siendo una lista
        demand = [row['demanda']]
        
        # Construir el diccionario del servicio
        services[service_id] = {
            "stops": stops,
            "demand": demand
        }

    # Información del material rodante (asumimos valores ejemplo)
    rs_info = {
        "capacity": 100,  # Puedes cambiar este valor según tus necesidades
        "max_rs": 25
    }
    
    # Construir la instancia
    instance = {
        "stations": stations,
        "cost_per_unit": cost_per_unit,
        "services": services,
        "rs_info": rs_info
    }
    
    # Convertir a formato JSON y devolver
    return json.dumps(instance, indent=4)
