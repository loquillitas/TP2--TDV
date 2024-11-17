import json
import networkx as nx
import matplotlib.pyplot as plt
import math


def extraer_paradas(data):

	# creo un diccionario vacio para almacenar las paradas
    # cada servicio va a estar formada por dos eventros, uno de llegada y otro de salida
    # en otras palabras vamos a guardar dos paradas por cada key del diccionario, ambas forman parte del mismo servicio, "comparten demanda"
    paradas = {}


    # itero sobre los servicios (que es un dic)
    for service_id, service_info in data["services"].items():
        paradas[service_id] = []

			#ayuda para ver como extraer informacion
			# print(f"\nService ID: {service_id}\service_info: {service_info}")
			# izq_hora, izq_estacion, izq_tipo = info_parada(service_info["stops"][0])
			# print(f"\nStop[0]: {service_info["stops"][0]}")


        # Recorrer cada parada (evento) en el servicio
        # como cada servicio tiene dos eventos, se recorre la lista de paradas por evento
        # for itera dos veces por servicio (una por cada evento)
        # creo demanda = 0 para cada evento
        demanda = 0
        for stop in service_info["stops"]:


            # Extraer información del evento
            tiempo = stop["time"]
            estacion = stop["station"]
            tipo = stop["type"]  # A o D

            # cada servicio tiene una demanda almacenada en una lista de un solo elemento
            # si el evento es de salida (D) entonces almaceno demanda
            # de caso contrario, almaceno el valor multiplicado por -1 --> conservacion de flujo
            if tipo == "D":
                demanda = service_info["demand"][0]
            else:
                demanda = -1 * service_info["demand"][0]

            # Almacenar la parada como un diccionario
            parada = {
                "tiempo": tiempo,
                "estacion": estacion,
                "tipo": tipo,
                "demanda": demanda
            }


            # Agregar la parada a la lista del servicio
            paradas[service_id].append(parada)

    print(f"\nParadas: {paradas}")
    return paradas


def construir_grafo(data):
    maximo_trenes = data["rs_info"]["max_rs"]
    capacidad_vagon = data["rs_info"]["capacity"]

    paradas = extraer_paradas(data)
    G = nx.DiGraph()

    # Extraigo paradas y creo los nodos
    for servicio in data["services"].values():
        nodo_origen = servicio["stops"][0]
        nodo_destino = servicio["stops"][1]
        demanda = math.ceil(servicio["demand"][0] / data["rs_info"]["capacity"])

        # Crear identificadores únicos para los nodos
        nodo_origen_id = f"{nodo_origen['station']}, {nodo_origen['time']}"
        nodo_destino_id = f"{nodo_destino['station']}, {nodo_destino['time']}"

        # Agregar nodos con demanda
        G.add_node(nodo_origen_id, demanda=demanda)
        G.add_node(nodo_destino_id, demanda=(-1) * demanda)

        # Agregar la arista que los une con la demanda correspondiente
        # 'type' es un atributo opcional; 'capacity' y otros también lo son
        G.add_edge(nodo_origen_id, nodo_destino_id, type='service', capacity=maximo_trenes, costo=0, lower=demanda, upper=maximo_trenes)
    
    
    # ######### AGREGAR ARISTAS DE TRANSBORDO Y TRASNOCHE #########
    # agrego las aristas de los servicios de trasnoche y transbordo
    # para eso, primero ordeno los servicios por estacion y tiempo

    ## ORDENO PRIMERO POR ESTACION (RETIRO O TIGRE)
    ## almaceno los dos grupos en un diccionario

    estaciones = {}

    for terminales in G.nodes:

        # extraigo la estacion del nodo (puede ser tigre o retiro)
        estacion = G.nodes[]

        estacion = G.nodes[terminales]["station"]
        if estacion not in estaciones:
            # si no esta la estacion en el diccionario, la agrego
            estaciones[estacion] = []

        # agrego el nodo a su respectiva estacion
        estaciones[estacion].append(terminales)

    ## AHORA ORDENO POR TIEMPO
    for estacion, nodos in estaciones.items():
        nodos.sort(key = lambda x: G.nodes[x]["time"])

    ### CREO LAS ARISTAS DE TRASPASO Y TRASNOCHE
    for estacion, nodos in estaciones.items():
        ##### TRASNOCHE
        nodo_origen = estaciones[estacion][-1]
        nodo_destino = estaciones[estacion][0]
        G.add_edge(nodo_origen, nodo_destino, demand=0, type='trasnoche', capacity=maximo_trenes, costo=1)

        ##### TRASPASO
        for i in range(len(nodos) - 1):
            nodo_origen = nodos[i]
            nodo_destino = nodos[i + 1]
            G.add_edge(nodo_origen, nodo_destino, demand=0, type='traspaso', capacity=maximo_trenes, costo=0)

    print(f"\nnodos: {G.nodes}\n\naristas: {G.edges}")

    return G


def cant_minima_vagones(G):

    # Calcula el flujo de costo mínimo en el grafo
    flow = nx.min_cost_flow(G)
    total_units_retiro = 0
    total_units_tigre = 0

    # Itera sobre los nodos de flujo para contar los vagones en Retiro y Tigre
    for u in flow:
        for v in flow[u]:
            # Verifica si la arista es de trasnoche (peso 1)
            if G[u][v]['costo'] == 1:
                # Suma los vagones en Retiro
                if 'Retiro' in u or 'Retiro' in v:
                    total_units_retiro += flow[u][v]
                # Suma los vagones en Tigre
                elif 'Tigre' in u or 'Tigre' in v:
                    total_units_tigre += flow[u][v]

            # Imprime el flujo en cada arista
            print(f"Flow from {u} to {v}: {flow[u][v]} units")

    print(f"Total units at Retiro: {total_units_retiro} vagones")
    print(f"Total units at Tigre: {total_units_tigre} vagones")

    return total_units_retiro, total_units_tigre

# filename = "instances/toy_instance.json"
# with open(filename) as json_file:
#         data = json.load(json_file)

# G = construir_grafo(extraer_paradas(data))
#  # ploteo el grafo
# nx.draw(G, with_labels=True)
# plt.show()

def main():
    filename = "instances/toy_instance.json"
    print("hola")
    with open(filename) as json_file:
        data = json.load(json_file)

    # test file reading
    # for service in data["services"]:
    #     print(service, data["services"][service]["stops"])

    # Creamos el grafo dirigido
    G = construir_grafo(data)

    # ploteo el grafo
    nx.draw(G, with_labels=True)
    # plt.show()

    # # Resolver el problema de flujo de costo mínimo
    print(cant_minima_vagones(G))
    

if __name__ == "__main__":
	main()
