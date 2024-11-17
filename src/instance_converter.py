import pandas as pd
import json

def csv_to_instance(csv_file):
    # Leer el archivo CSV
    df = pd.read_csv("src/nueva_instancia.csv")
    
    # Extraer las estaciones cabecera (asumimos que son únicas y están en las columnas 'origen' y 'destino')
    stations = list(df['origen'].unique())  # Aquí asumimos que origen y destino contienen todas las estaciones
    
    # Lista fija según el contexto
    cost_per_unit = [1, 1]
    
    # Construir el diccionario de servicios
    services = {}
    for index, row in df.iterrows():
        service_id = str(row['service id'])
        
        stops = [
            (row['hora'], row['origen'], row['tipo']),
            (row['hora.1'], row['destino'], row['tipo.1'])  # Asumiendo 'hora.1', 'destino', 'tipo.1' existen para el segundo evento
        ]
        demand = [row['demanda']]
        
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
