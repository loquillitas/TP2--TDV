import json
import networkx as nx
import matplotlib.pyplot as plt
import math

def extraer_estaciones(data):
    return data["stations"]


def extraer_paradas(data):
    """
    esta funcion fue creada primero para entender como estan estructurados los datos
    luego se construyo la funcion construir_grafo a partir de la data reordenada por esta funcion
    si bien agrega un paso extra, es mas facil de entender y trabajar con la data de esta forma

    input: data
    res: paradas:dict
    """
    
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

    # print(f"\nParadas: {paradas}")
    return paradas


def construir_grafo(data):
    """
    Crea un grafo dirigido con NetworkX --> tambien agrega aristas de trasbordo y trasnoche
    input: data
    res: G
    type(res): nx.DiGraph
    """


    maximo_trenes = data["rs_info"]["max_rs"]
    capacidad_vagon = data["rs_info"]["capacity"]

    paradas = extraer_paradas(data)
    G = nx.DiGraph()

    # Extrae paradas y crea los nodos
    for key, servicio in paradas.items():
        nodo_origen = f"{servicio[0]['estacion']}_{servicio[0]['tiempo']}_{key}"
        nodo_destino = f"{servicio[1]['estacion']}_{servicio[1]['tiempo']}_{key}"
        
        # Redondeo la demanda para arriba --> si necesito 4.2 trenes --> entonces necesito 5 trenes
        demanda = math.ceil(servicio[0]['demanda'] / capacidad_vagon)        


        # Agregar los NODOS
        G.add_node(nodo_origen, station=servicio[0]['estacion'], demand=demanda, time=servicio[0]['tiempo'], type=servicio[0]['tipo'])
        G.add_node(nodo_destino, station=servicio[1]['estacion'],demand= (-1)*demanda, time=servicio[1]['tiempo'], type=servicio[1]['tipo'])

        # Agregar la ARISTA que une los nodos con la demanda correspondiente
        # Tipo: "service" para indicar que es una arista de servicio
        G.add_edge(nodo_origen, nodo_destino, demand=demanda, type='servicio', capacity=maximo_trenes-demanda, costo=0, min=demanda, max=maximo_trenes) #
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
        G.add_edge(nodo_origen, nodo_destino, demand=0, type='trasnoche', capacity=float("inf"), costo=1, min=0, max=maximo_trenes)

        ##### TRASPASO
        for i in range(len(nodos) - 1):
            nodo_origen = nodos[i]
            nodo_destino = nodos[i + 1]
            G.add_edge(nodo_origen, nodo_destino, demand=0, type='traspaso', capacity=float("inf"), costo=0, min=0, max=maximo_trenes)

    # print(f"\nNodos: {G.nodes}\n\nAristas: {G.edges}")
    return G

def mincosto(G):
    """
    Calcula el flujo de costo mínimo en un grafo dirigido.
    flujo de costo minimo --> busca reflejar las demandas de los nodos 

    input: G
    res: flujo de costo minimo 
    type(res): dict
    """

    flow = nx.min_cost_flow(G, "demand", "capacity", "costo")

    for u, v in G.edges:

        if G.edges[u, v]["type"] == "servicio":
            # incrementa el flujo en la demanda
            flow[u][v] += G.nodes[u]["demand"]

    return flow


def cant_minima_vagones(G, estaciones):
    """
    Calcula la cantidad mínima de vagones necesarios para cada estación terminal.

    input:
        G: Un grafo dirigido que representa el problema.
        estaciones: Lista de nombres de estaciones terminales.

    res:
        Un diccionario con la cantidad total de vagones en cada estación terminal.
    """

    # Inicializa un diccionario para almacenar los totales por estación
    total_units = {estacion: 0 for estacion in estaciones}

    # Calcula el flujo de costo mínimo en el grafo
    try:
        flow = nx.min_cost_flow(G)
    except nx.NetworkXUnfeasible:
        print("No se puede satisfacer la demanda del grafo; flujo no es factible.")
        return total_units

    # Itera sobre los nodos de flujo para contar los vagones en cada estación terminal
    for u in flow:
        for v in flow[u]:
            # Verifica si la arista es de trasnoche (peso 1)
            if G[u][v]['costo'] == 1:
                # Suma los vagones en las estaciones terminales
                for estacion in estaciones:
                    if estacion in u or estacion in v:
                        total_units[estacion] += flow[u][v]

    # # Imprime el resultado por estación
    # for estacion, total in total_units.items():
    #     print(f"Total units at {estacion}: {total} vagones")

    return total_units


def grafico(G, flow_dict, estaciones):
    """
    Grafica el grafo dirigido con NetworkX.
    """

    # posicion de los nodos
    pos = {}

    # divide a nodos depende de la estacion y los ordena
    izq_nodes = [n for n in G.nodes if G.nodes[n]["station"] == estaciones[0]]
                                                  #"] == estaciones[0]]
    der_nodes = [n for n in G.nodes if G.nodes[n]["station"] == estaciones[1]]
    izq_nodes.sort(key=lambda x: G.nodes[x]["time"])
    der_nodes.sort(key=lambda x: G.nodes[x]["time"])

    escala_horarios = 5

    # asignar posiciones
    for i, node in enumerate(izq_nodes):
        pos[node] = (1, -i * escala_horarios * 2)
    for i, node in enumerate(der_nodes):
        pos[node] = (2, -i * escala_horarios * 2)

    plt.figure()  
    # sumo los values de cant_minima_vagones para obtener la cantidad total de vagones
    total = sum(cant_minima_vagones(G, estaciones).values())
    plt.title(f"Cant total de vagones: {total}")

    
    # nodos
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color="azure")

    # aristas para VIAJES
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[(u, v) for u, v, d in G.edges(data=True) if d["type"] == "servicio"],
    )

    # aristas para TRASPASO
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[(u, v) for u, v, d in G.edges(data=True) if d["type"] == "traspaso"],
    )

    # aristas para TRASNOCHE (lado izquierdo)
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[
            (u, v)
            for u, v, d in G.edges(data=True)
            if d["type"] == "trasnoche" and (G.nodes[u]["station"] == estaciones[0])
        ],
        connectionstyle="arc3,rad=-0.5",
    )

    # aristas para TRASNOCHE (lado derecho)
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[
            (u, v)
            for u, v, d in G.edges(data=True)
            if d["type"] == "trasnoche" and (G.nodes[u]["station"] == estaciones[1])
        ],
        connectionstyle="arc3,rad=0.5",
    )

    # etiquetas nodos
    node_labels = {node: node.split("_")[0] for node in G.nodes}
    nx.draw_networkx_labels(G, pos, node_labels, font_size=10)

    edge_labels = {}
    edge_labels_intra = {}

    tras = []
    # etiquetas aristas
    for u, v, d in G.edges(data=True):
        flujo = flow_dict[u][v] if u in flow_dict and v in flow_dict[u] else 0
        # estaciones distintas
        if not set(u.split("_")) & set(v.split("_")):
            edge_labels[(u, v)] = f"{flujo}/25"

        # estaciones iguales
        else:
            edge_labels_intra[(u, v)] = f"{flujo}"
            
            if d["type"] == "trasnoche":
                tras.append (f"{flujo}")

    pos_labels = {
        "C Trasnoche A":(0.805,-24),
        "C Trasnoche B": (2.168,-24),
    }

    nx.draw_networkx_labels(G, pos_labels, labels={"C Trasnoche A":tras[0],"C Trasnoche B":tras[1]},font_size=10)


    pos_estaciones = {
        "Estacion A": (1.01, 3.5), 
        "Estacion B": (2, 3.5), 
    }
    
    nx.draw_networkx_labels(G, pos_estaciones, labels={"Estacion A": estaciones[0], "Estacion B": estaciones[1]})

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_intra, rotate=False)


    plt.show()


import json

def combinar_json(json1, json2):
    """
    junta dos instancias JSON en una única instancia.

    in: json1 + json2  
    res: dict: JSON combinado.
    """

    combinado = {
        "services": {},
        "stations": [],
        "cost_per_unit": {},
        "rs_info": {
            "capacity": max(json1["rs_info"]["capacity"], json2["rs_info"]["capacity"]),
            "max_rs": max(json1["rs_info"]["max_rs"], json2["rs_info"]["max_rs"]),
        }
    }

    # Combinar los servicios
    combinado["services"].update(json1["services"])
    combinado["services"].update(json2["services"])

    # Combinar las estaciones (sin duplicados)
    combinado["stations"] = list(set(json1["stations"] + json2["stations"]))

    # Combinar los costos por unidad (promediamos si hay duplicados)
    for estacion in combinado["stations"]:
        costo1 = json1["cost_per_unit"].get(estacion, 0)
        costo2 = json2["cost_per_unit"].get(estacion, 0)
        combinado["cost_per_unit"][estacion] = max(costo1, costo2)

    return combinado


def main():

    filename = "instances/retiro-tigre-semana.json"

    with open(filename, "r") as json_file:
        data = json.load(json_file)

    estaciones = extraer_estaciones(data) # nos sirve para graficar --> parametro de la funcion grafico
    # NOTAR que data ser transforma despues, por lo que es importante extraer la informacion antes de transformarla

    # Crea el grafo dirigido
    G = construir_grafo(data)

    ###### VERIFICO ######
    # conservacion de flujo --> sumo todas las demdandas de los nodos y deberia dar 0 
    total_demanda = 0
    for nodo, data in G.nodes(data=True):
        total_demanda += data.get('demand', 0)

    if total_demanda == 0:
        # si la demanda total es 0, entonces se conserva el flujo
        print(f"total_demanda: {total_demanda} --> OK")

        # Resolver el problema de flujo de costo mínimo
        print(cant_minima_vagones(G, estaciones))
    else:
        print(f"total_demanda: {total_demanda} --> NO OK: no se conserva el flujo")


    # Plotear el grafo
    flow_dict = mincosto(G)  
    # grafico(G, flow_dict, estaciones)



    ### EJERCICIO 5 ###
    # Combinar dos instancias JSON
    # Cargo los archivos JSON
    with open('instances/cardales-victoria-semana.json', 'r') as file1:
        json1 = json.load(file1)

    with open('instances/retiro-tigre-semana.json', 'r') as file2:
        json2 = json.load(file2)

    # Junto los .json
    json_combinado = combinar_json(json1, json2)

    # los guardo en un nuevo archivo :P
    with open('instancia_combinada.json', 'w') as outfile:
        json.dump(json_combinado, outfile, indent=4)


    # Veo la cantidad total si corro por separado los dos ramales
    estacionesRetiroTigre = extraer_estaciones(json1)
    G1 = construir_grafo(json1)
    vagonesRetiroTigre = cant_minima_vagones(G1, estacionesRetiroTigre)

    estacionesCardalesVictoria = extraer_estaciones(json2)
    G2 = construir_grafo(json2)
    vagonesCardalesVictoria = cant_minima_vagones(G2, estacionesCardalesVictoria)

    # Veo la cantidad total si corro los dos ramales juntos
    estacionesCombinado = extraer_estaciones(json_combinado) 
    GComb = construir_grafo(json_combinado)
    vagonesCombinado = cant_minima_vagones(GComb, estacionesCombinado)

    print(f"\nVagones totales por separado:\n - Retiro-Tigre: {vagonesRetiroTigre}\n - Cardales-Victoria: {vagonesCardalesVictoria}")
    print(f"\nVagones totales combinados: \n - {vagonesCombinado}\n")

if __name__ == "__main__":
    main()
