from simulator.node import Node
import json

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.main_dv_table = self.get_routing_table(self.id) # {{ node : { route : [ROUTE-INFO], cost : COST }}
        self.main_neighbor_list = []
        self.neighbors_dv_table = {} # {node_id : { node : { route : [ROUTE INFO], cost : COST }}}
        self.neighbors_last_message_time = {} # { node : time }
        self.link_list = {} # { node : latency/cost}
        self.seq_number = 0

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    def get_routing_table(self, node):
        return {str(node): {"route": [None], "cost": 0}}
    

    def update_neighbors(self, dv_table):
        if self.main_dv_table != dv_table:
            self.seq_number += 1
            self.main_dv_table = dv_table

            message = {
                "sender_id": self.id,
                "dv_info": dv_table,
                "time_seq": self.seq_number
            }
            dv_message = json.dumps({"dv": message})
            self.send_to_neighbors(dv_message) 


    def get_nodes(self):
        dv = {str(self.id): {"route": [None], "cost": 0}}
        nodes = [str(self.id)]

        for neighbor in self.main_neighbor_list:
            for node in self.neighbors_dv_table[neighbor]:
                if node not in nodes:
                    nodes.append(node)

        return dv, nodes


    def dv_link_update(self):
        # Bellman-Ford's Algorithm - Reference: https://www.javatpoint.com/bellman-ford-algorithm
        dv, nodes = self.get_nodes()

        for node in nodes:
            if self.id != int(node):
                min_cost = float("inf")
                min_hops = [-1]
            else:
                min_cost = 0
                min_hops = [None]
            node = str(node)

            for neighbor, neighbor_dv in self.neighbors_dv_table.items():
                if node in neighbor_dv:
                    neighbor_route = neighbor_dv[node]["route"]
                    if self.id not in neighbor_route:
                        temp = neighbor_dv[node]["cost"] + self.link_list[neighbor]
                        if temp <= min_cost:
                            min_cost = temp
                            min_hops = [neighbor] + neighbor_route

            dv[str(node)] = {"cost": min_cost, "route": min_hops}

        self.update_neighbors(dv)


    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if neighbor in self.main_neighbor_list:
            if latency == -1:
                self.main_neighbor_list.remove(neighbor)
                del self.neighbors_dv_table[neighbor]
                del self.neighbors_last_message_time[neighbor]
                del self.link_list[neighbor]
            else:
                self.link_list[neighbor] = latency
        else:
            self.main_neighbor_list.append(neighbor)
            self.neighbors_last_message_time[neighbor] = 0
            self.link_list[neighbor] = latency
            self.neighbors_dv_table[neighbor] = self.get_routing_table(neighbor)

        self.dv_link_update()


    def update_dv_table(self):
        # Bellman-Ford's  - Reference https://www.javatpoint.com/bellman-ford-algorithm
        dv, nodes = self.get_nodes()

        for node in nodes:
            if self.id != int(node):
                min_cost = float("inf")
                min_hops = [-1]
                node = str(node)

                for neighbor, neighbor_dv in self.neighbors_dv_table.items():
                    if node in neighbor_dv:
                        if neighbor in self.link_list:
                            neighbor_route = neighbor_dv[node]["route"]
                            if self.id not in neighbor_route:
                                temp = neighbor_dv[node]["cost"] + self.link_list[neighbor]
                                if temp < min_cost:
                                    min_cost = temp
                                    min_hops = [neighbor] + neighbor_route
            else:
                min_cost = 0
                min_hops = [None]

            dv[str(node)] = {"cost": min_cost, "route": min_hops}

        self.update_neighbors(dv)


    # Fill in this function
    def process_incoming_routing_message(self, m):
        data = json.loads(m)
        message = data["dv"]
        m_sender = message["sender_id"]
        m_time = message["time_seq"]
        m_dv = message["dv_info"]

        if m_sender in self.neighbors_last_message_time:
            if m_time > self.neighbors_last_message_time[m_sender]:
                self.neighbors_last_message_time[m_sender] = m_time
                self.neighbors_dv_table[m_sender] = m_dv
                self.update_dv_table()


    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        # return -1
        route = self.main_dv_table[str(destination)]["route"]
        if route is not None:
            return int(route[0])
        return -1
