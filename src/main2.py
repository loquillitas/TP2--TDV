import json
import networkx as nx
import matplotlib.pyplot as plt
import math


def extraer_paradas(data):

    # Creo un diccionario vacío para almacenar las paradas
    # Cada servicio va a estar formado por dos eventos, uno de llegada y otro de salida
    # En otras palabras, vamos a guardar dos paradas por cada key del diccionario, ambas forman parte del mismo servicio y "comparten demanda"
    paradas = {}

    # Itero sobre los servicios (que es un diccionario)
    for service_id, service_info in data["services"].items():
        paradas[service_id] = []

        # Recorre cada parada (evento) en el servicio
        # Como cada servicio tiene dos eventos, se recorre la lista de paradas por evento
        demanda = 0
        for stop in service_info["stops"]:
            # print("#########################################################3")
            # print(f"\nStop: {stop}, tipo: {stop['type']}")
            # Extraer información del evento
            tiempo = stop["time"]
            estacion = stop["station"]
            tipo = stop["type"]  # "A" o "D"
            # inicializo la demanda
            demanda = service_info["demand"][0]
 

            # Asigna la demanda de acuerdo al tipo de parada (llegada o salida)
            if not stop["type"] == "D":
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

    # Extrae paradas y crea los nodos
    for key, servicio in paradas.items():
        nodo_origen = f"{servicio[0]['estacion']}_{servicio[0]['tiempo']}_{key}"
        nodo_destino = f"{servicio[1]['estacion']}_{servicio[1]['tiempo']}_{key}"
        
        # Redondeo la demanda para arriba --> si necesito 4.2 trenes --> entonces necesito 5 trenes
        demanda = math.ceil(servicio[0]['demanda'] / 100)

        # Agregar los nodos
        G.add_node(nodo_origen, station=servicio[0]['estacion'], demand=demanda, time=servicio[0]['tiempo'], type=servicio[0]['tipo'])
        G.add_node(nodo_destino, station=servicio[1]['estacion'],demand= (-1)*demanda, time=servicio[1]['tiempo'], type=servicio[1]['tipo'])

        # Agregar la arista que une los nodos con la demanda correspondiente
        # Tipo: "service" para indicar que es una arista de servicio
        G.add_edge(nodo_origen, nodo_destino, demand=demanda, type='service', capacity=maximo_trenes-demanda, costo=0) 
        ######################################################################capacity=maximo_trenes-demanda ???? --> si no lo pongo me da negative cycle with infinite capacity found --> preguntar por que
        
    ###### AGREGAR ARISTAS DE TRANSBORDO Y TRASNOCHE ######
    # Para eso, primero ordeno los servicios por estación y tiempo

    # Almacena los nodos agrupados por estación
    estaciones = {}

    for terminales in G.nodes:

        # Extrae la estación del nodo (puede ser Tigre o Retiro)
        estacion = G.nodes[terminales]["station"]
        if estacion not in estaciones:
            estaciones[estacion] = []  # Si no está en el diccionario, la agrego

        # Agrega el nodo a su respectiva estación
        estaciones[estacion].append(terminales)

    ###### ORDENAR LOS NODOS POR TIEMPO ######
    for estacion, nodos in estaciones.items():
        nodos.sort(key=lambda x: G.nodes[x]["time"])

    ###### CREAR LAS ARISTAS DE TRASPASO Y TRASNOCHE ######
    for estacion, nodos in estaciones.items():
        ##### TRASNOCHE
        nodo_origen = estaciones[estacion][-1]
        nodo_destino = estaciones[estacion][0]
        G.add_edge(nodo_origen, nodo_destino, demand=0, type='trasnoche', capacity=float("inf"), costo=1)

        ##### TRASPASO
        for i in range(len(nodos) - 1):
            nodo_origen = nodos[i]
            nodo_destino = nodos[i + 1]
            G.add_edge(nodo_origen, nodo_destino, demand=0, type='traspaso', capacity=float("inf"), costo=0)

    print(f"\nNodos: {G.nodes}\n\nAristas: {G.edges}")
    return G

def cant_minima_vagones(G):
    # Imprimir demandas de los nodos
    for nodo, data in G.nodes(data=True):
        print(f"Nodo: {nodo}, Demanda: {data.get('demand', 0)}")

    # Calcula el flujo de costo mínimo en el grafo
    try:
        flow = nx.min_cost_flow(G)
    except nx.NetworkXUnfeasible:
        print("No se puede satisfacer la demanda del grafo; flujo no es factible.")
        return 0, 0

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


def main():
    filename = "instances/toy_instance.json"
    print("hola")
    with open(filename) as json_file:
        data = json.load(json_file)

    # Crea el grafo dirigido
    G = construir_grafo(data)

    # #imprimo las aristas y su contenido entero
    # for u, v, data in G.edges(data=True):
    #     print(f"Arista de {u} a {v}: {data}")

    # #imprimo las paradas 
    # for nodo, data in G.nodes(data=True):
    #     print(f"Nodo: {nodo}, Data: {data}")
    
    # Dibuja el grafo
    nx.draw(G, with_labels=True)
    plt.show()

    # Resolver el problema de flujo de costo mínimo
    print(cant_minima_vagones(G))



    # conservacion de flujo --> sumo todas las demdandas de los nodos y deberia dar 0 
    total_demanda = 0
    for nodo, data in G.nodes(data=True):
        total_demanda += data.get('demand', 0)
    # print(total_demanda)


    # Verificar capacidades y costos en las aristas
    # for u, v, data in G.edges(data=True):
        # print(f"Arista de {u} a {v}, Capacidad: {data.get('capacity', 'No definida')}, Costo: {data.get('cost', 'No definido')}")




if __name__ == "__main__":
    main()
