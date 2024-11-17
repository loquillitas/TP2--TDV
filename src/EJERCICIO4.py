import csv
import random
import json
import copy
import pandas as pd

def convertir_json(filename,capacity,max_rs):
    
    # instancio las componentes de mi instancia
    instance = {}
    instance['services'] = {}
    instance['stations'] = []
    instance['cost_per_unit'] = {}
    instance['rs_info'] = {capacity: capacity, max_rs: max_rs}


    df = pd.read_csv(filename + '.csv')
    for index, row in df.iterrows():
        
        service_id = index
    # # creo los servicios
    # with open(filename + '.csv') as csvfile:

    #     csvreader = csv.reader(csvfile)
    #     next(csvreader)
        
        # for row in csvreader:
        #     service_id = row[0]

        stops = [
            ((row[1]), row[2], row[3]),
            ((row[4]), row[5], row[6])
        ]

        demand = [int(row[7])]

        instance['services'][service_id] = {
            "stops": stops,
            "demand": demand }
        
        if row[2] not in instance['stations']:
            instance['stations'].append(row[2])
        if row[5] not in instance['stations']:
            instance['stations'].append(row[5])
        service_id = row[0]

        stops:tuple = [
            # service id_0,
            ## hora_1,origen_2,tipo_3,
            ## hora_4,destino_5,tipo_6,
            ### demanda_7
            (int(row[1]), row[2], row[3]),
            (int(row[4]), row[5], row[6])
        ]

        demand = [int(row[7])]

        instance['services'][service_id] = {
            "stops": stops,
            "demand": demand }
        
        if row[2] not in instance['stations']:
            instance['stations'].append(row[2])
        if row[5] not in instance['stations']:
            instance['stations'].append(row[5])

    instance['rs_info'] = {'capacity': capacity, 'max_rs': max_rs}
    for station in instance['stations']:
        instance['cost_per_unit'][station] = 1

    with open(filename + '.json', 'w') as jsonfile:
        json.dump(instance, jsonfile, indent=4)

    return instance

# "stations": ["Tigre", "Retiro"], 
# "cost_per_unit": {"Tigre": 1.0, "Retiro": 1.0}, 
# "rs_info": {"capacity": 100, "max_rs": 25}

# def generar_csv(filename, cantidad_servicios, horario_min, horario_max, estacion_1, estacion_2, demanda_min, demanda_max):
#     horarios_unicos = set()

#     while len(horarios_unicos) < 2 * cantidad_servicios: 
#         horario = random.randint(horario_min, horario_max)
#         horarios_unicos.add(horario)

#     horarios = sorted(list(horarios_unicos))

#     with open(filename, mode='w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(["service id", "hora", "origen", "tipo", "hora", "destino", "tipo", "demanda (pax)"])

#         for i in range(1, cantidad_servicios + 1):
#             hora_origen = horarios.pop(0)
#             hora_destino = horarios.pop(0)

#             origen = random.choice([estacion_1, estacion_2])
#             destino = estacion_2 if origen == estacion_1 else estacion_1

#             demanda = random.randint(demanda_min, demanda_max)

#             writer.writerow([i, hora_origen, origen, "D", hora_destino, destino, "A", demanda])

filename = "src/ejercicio4"

capacity = 100
max_rs = 5

# if capacity * max_rs < demanda_max: ## CHEQUEAR BIEN ESTO NO SE COMO ES
#     raise ValueError("El valor de max_rs es demasiado pequeño para manejar la demanda total.")

# generar_csv(filename, cantidad_servicios, horario_min, horario_max, estacion_1, estacion_2, demanda_min, demanda_max)
convertir_json(filename,capacity,max_rs)