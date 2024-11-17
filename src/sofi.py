import json
import networkx as nx
import matplotlib.pyplot as plt
import math


def info_parada(stop):
    """info de cada una de las paradas"""
    return stop["time"], stop["station"], stop["type"]

def nuevo_nodo(G, hora, estacion, tipo, demanda):
    """agregar nodo al grafo"""
    G.add_node(
        f"{hora}_{estacion}_{tipo}",
        time=hora,
        station=estacion,
        type=tipo,
        demanda=demanda,
    )

def Grafo(data):
    """armar el grafo"""

    G = nx.DiGraph()
    cost_per_unit = data["cost_per_unit"]
    # si existe capacidad maxima para las aristas de trasnoche:
    max_night_capacity = data.get("max_night_capacity", {})

    # para cada servicio independiente de que tipo
    for service_id, service_info in data["services"].items():

        # info de las dos cabeceras
        izq_hora, izq_estacion, izq_tipo = info_parada(service_info["stops"][0])
        der_hora, der_estacion, der_tipo = info_parada(service_info["stops"][1])

        # redondeo para arriba por las dudas que no sea divisible por capacity
        demanda_vagones = math.ceil(service_info["demand"][0] / data["rs_info"]["capacity"])

        # maximo vagones que pueden asignarse a un servicio
        maximo_trenes = data["rs_info"]["max_rs"]

        # izq (D) --> der (A)
        if izq_tipo == "D":
            nuevo_nodo(G, izq_hora, izq_estacion, izq_tipo, demanda_vagones)
            nuevo_nodo(G, der_hora, der_estacion, der_tipo, -demanda_vagones)

            G.add_edge(
                f"{izq_hora}_{izq_estacion}_{izq_tipo}",
                f"{der_hora}_{der_estacion}_{der_tipo}",
                tipo="viaje",
                capacidad=maximo_trenes - demanda_vagones,
                costo=0,
            )
        
        # izq (A) <-- der (D)
        else:
            nuevo_nodo(G, izq_hora, izq_estacion, izq_tipo, -demanda_vagones)
            nuevo_nodo(G, der_hora, der_estacion, der_tipo, demanda_vagones)

            G.add_edge(
                f"{der_hora}_{der_estacion}_{der_tipo}",
                f"{izq_hora}_{izq_estacion}_{izq_tipo}",
                tipo="viaje",
                capacidad=maximo_trenes - demanda_vagones,
                costo=0,
            )
    estaciones = {}

    # nodos por estacion
    for cabecera in G.nodes:
        estacion = G.nodes[cabecera]["station"]
        if estacion not in estaciones:
            estaciones[estacion] = []
        estaciones[estacion].append(cabecera)

    # por cada estacion, ordena segun tiempo
    for estacion, cabeceras in estaciones.items():

        # ordena por tiempo

        nodos_ordenados = sorted(cabeceras, key=lambda nodo: G.nodes[nodo]["time"])

        for i in range(len(nodos_ordenados) - 1):
            G.add_edge(

                # nodos consecutivos
                nodos_ordenados[i], nodos_ordenados[i + 1],
                tipo="traspaso",
                capacidad=float("inf"),
                costo=0,
            )

        costo_trasnoche = cost_per_unit[estacion] 
        cap = max_night_capacity.get(estacion,float("inf"))

        G.add_edge(

            # primer y ultimo nodo
            nodos_ordenados[-1], nodos_ordenados[0],
            tipo="trasnoche",
            capacidad=cap,
            costo=costo_trasnoche,
        )

    return G


def minimocosto(G,ajustar):
    """flujo de costo minimo"""

    flow = nx.min_cost_flow(G, "demanda", "capacidad", "costo")

    # si queremos ajustar el flujo dejamos en True
    if ajustar==True:
    # para las aristas de viaje
        for u, v in G.edges:
            if G.edges[u, v]["tipo"] == "viaje":

                # incrementa el flujo en la cantidad de la demanda
                flow[u][v] += G.nodes[u]["demanda"]

    return flow


def vagones(G, flow_dict, estaciones):
    """cantidad de vagones en cada estacion que provienen de los tramos de trasnoche"""

    flujo_estacion_a = 0
    flujo_estacion_b = 0

    # para las aristas de trasnoche
    for u, v in G.edges:
        if G.edges[u, v]["tipo"] == "trasnoche":

            # actualiza flujos
            if estaciones[0] in u: # primera estacion es origen
                flujo_estacion_a += ( # sumo flujo de arista u --> v
                    flow_dict[u][v] if u in flow_dict and v in flow_dict[u] else 0
                )
            elif estaciones[1] in u: # segunda estacion es origen
                flujo_estacion_b += ( # sumo flujo de arista u --> v
                    flow_dict[u][v] if u in flow_dict and v in flow_dict[u] else 0
                )

    print(f"{estaciones[0]}: {flujo_estacion_a} vagones")
    print(f"{estaciones[1]}: {flujo_estacion_b} vagones")
    print("Vagones total usados:",flujo_estacion_a+flujo_estacion_b)
    return("Vagones total usados:",flujo_estacion_a+flujo_estacion_b)


def plotear(G, flow_dict, estaciones, solucion):

    # posicion de los nodos
    pos = {}

    # divide a nodos depende de la estacion y los ordena
    izq_nodes = [n for n in G.nodes if G.nodes[n]["station"] == estaciones[0]]
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
    plt.title(vagones(G, flow_dict, estaciones))
    # nodos
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color="azure")

    # aristas para VIAJES
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[(u, v) for u, v, d in G.edges(data=True) if d["tipo"] == "viaje"],
    )

    # aristas para TRASPASO
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[(u, v) for u, v, d in G.edges(data=True) if d["tipo"] == "traspaso"],
    )

    # aristas para TRASNOCHE (lado izquierdo)
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[
            (u, v)
            for u, v, d in G.edges(data=True)
            if d["tipo"] == "trasnoche" and (G.nodes[u]["station"] == estaciones[0])
        ],
        connectionstyle="arc3,rad=-0.5",
    )

    # aristas para TRASNOCHE (lado derecho)
    nx.draw_networkx_edges( G, pos, node_size=800,
        edgelist=[
            (u, v)
            for u, v, d in G.edges(data=True)
            if d["tipo"] == "trasnoche" and (G.nodes[u]["station"] == estaciones[1])
        ],
        connectionstyle="arc3,rad=0.5",
    )

    # etiquetas nodos
    node_labels = {node: node.split("_")[0] for node in G.nodes}
    nx.draw_networkx_labels(G, pos, node_labels, font_size=10)

    edge_labels = {}
    edge_labels_intra = {}

    if solucion == True: # grafo + sol
        tras = []
        # etiquetas aristas
        for u, v, d in G.edges(data=True):
            flujo = flow_dict[u][v] if u in flow_dict and v in flow_dict[u] else 0
            etiqueta = G.edges[(u, v)]["capacidad"]
            
            # estaciones distintas
            if not set(u.split("_")) & set(v.split("_")):
                edge_labels[(u, v)] = f"{flujo}/25"

            # estaciones iguales
            else:
                edge_labels_intra[(u, v)] = f"{flujo}"
                
                if d["tipo"] == "trasnoche":
                    tras.append (f"{flujo}")

        pos_labels = {
            "C Trasnoche A":(0.805,-24),
            "C Trasnoche B": (2.168,-24),
        }

        nx.draw_networkx_labels(G, pos_labels, labels={"C Trasnoche A":tras[0],"C Trasnoche B":tras[1]},font_size=10)

    else:
        for u,v, d in G.edges(data=True):
            if d["tipo"] == "viaje":
                edge_labels[(u, v)] = f"viaje"
            if d["tipo"] == "traspaso":
                edge_labels[(u, v)] = f"traspaso"

        pos_labels = {
                "Tras A": (0.84,-14.57),
                "Noche A": (0.84,-16.57),
                "Tras B": (2.165,-14.57),
                "Noche B": (2.165,-16.57),
        }
        nx.draw_networkx_labels(G, pos_labels, labels={"Tras A":"tras", "Noche A":"noche","Tras B":"tras","Noche B":"noche"},font_size=10)
    
    pos_estaciones = {
        "Estacion A": (1.01, 3.5), 
        "Estacion B": (2, 3.5), 
    }
    
    nx.draw_networkx_labels(G, pos_estaciones, labels={"Estacion A": estaciones[0], "Estacion B": estaciones[1]})

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_intra, rotate=False)


    plt.show()


def main():

    filename = "instances/toy_instance.json"
    with open(filename) as json_file:
        data = json.load(json_file)

    # armo grafo
    G = Grafo(data)


    # costo minimo
    flow_dict = minimocosto(G,ajustar=True)

    # nombre estaciones
    estaciones = data.get("stations", [])

    vagones(G, flow_dict, estaciones)

    plotear(G, flow_dict, estaciones,solucion=True) # solucion = False para solo grafo, solucion = True para grafo con sol

    print(flow_dict)

if __name__ == "__main__":
    main()
