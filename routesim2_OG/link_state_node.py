from simulator.node import Node

# maintain a graph for all links in the system
# Also keep track of shortest paths to other nodes in the system
# Send flood message containing all the link-state except incoming to neighbors
# Send correction message to sender if you got stale value

import json
MESSAGE_TYPES = {0:'LINK_UPDATE',1:'FLOOD_MESSAGE',2:"CORRECTION_MESSAGE",3:"TEST"}

class Graph():
    def __init__(self):
        self.edges = {}
        self.weights = {}
    
    def add_edge(self, from_node, to_node, weight):
        if from_node not in self.edges:
            self.edges[from_node] = []
        if to_node not in self.edges:
            self.edges[to_node] = []
        
        self.edges[from_node].append(to_node)
        self.edges[to_node].append(from_node)
        self.weights[(from_node, to_node)] = weight
        self.weights[(to_node, from_node)] = weight

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.local_graph = {} # key: node_id ; value: {destination_id:latency}
        self.link_states = {} # key: "{source} -> {destination}" ; value: [(latency,sequence_no)]

    # Return a string
    def __str__(self):
        print("NODE: %d database"%(self.id))
        print(self.local_graph)
        print(self.link_states)
        return "END of node: %d \n\n"%(self.id)
    
    def dijsktra(self,graph, initial, end):
        # shortest paths is a dict of nodes
        # whose value is a tuple of (previous node, weight)
        shortest_paths = {initial: (None, 0)}
        current_node = initial
        visited = set()
        
        while current_node != end:
            visited.add(current_node)
            destinations = graph.edges[current_node]
            weight_to_current_node = shortest_paths[current_node][1]

            for next_node in destinations:
                weight = graph.weights[(current_node, next_node)] + weight_to_current_node
                if next_node not in shortest_paths:
                    shortest_paths[next_node] = (current_node, weight)
                else:
                    current_shortest_weight = shortest_paths[next_node][1]
                    if current_shortest_weight > weight:
                        shortest_paths[next_node] = (current_node, weight)
            
            next_destinations = {node: shortest_paths[node] for node in shortest_paths if node not in visited}
            if not next_destinations:
                return -1
            # next node is the destination with the lowest weight
            current_node = min(next_destinations, key=lambda k: next_destinations[k][1])
        
        # Work back through destinations in shortest path
        path = []
        while current_node is not None:
            path.append(current_node)
            next_node = shortest_paths[current_node][0]
            current_node = next_node
        # Reverse path
        path = path[::-1]
        return path
    
    def generate_shortest_path_graph(self,destination):
        if self.id not in self.local_graph:
            return -1
        neighbors = [n for n in self.local_graph[self.id].keys()]
        if not neighbors:
            return -1
        
        edges = []
        visited = []
        for s in self.local_graph.keys():
            for d in self.local_graph[s].keys():
                source_destination = sorted([s,d])
                if source_destination in visited:
                    continue
                visited.append(source_destination)
                edges.append((s,d,self.local_graph[s][d]))
        graph = Graph()
        for e in edges:
            graph.add_edge(*e)
        path = self.dijsktra(graph,self.id,destination)
        return path

    def update_local_graph(self,source,destination, latency):
        # add
        # update
        # delete

        # if source or destination not in graph, init them
        if destination not in self.local_graph:
            self.local_graph[destination] = {}
        if source not in self.local_graph:
            self.local_graph[source] = {}

        # Handle add or update calls
        if latency!=-1:
            self.local_graph[source][destination] = latency
            self.local_graph[destination][source] = latency
        
        # Handle delete calls
        else:
            if destination in self.local_graph[source]:
                del self.local_graph[source][destination]
            if source in self.local_graph[destination]:
                del self.local_graph[destination][source]
            # Delete node from graph if it has no links
            if not self.local_graph[source]:
                del self.local_graph[source]
            if not self.local_graph[destination]:
                del self.local_graph[destination]

    def update_link_state(self,source,destination,latency, sequence_number=None):
        # Overwrite existing value if you see a higher sequence number!!!
        source,destination = sorted([source,destination])
        link = "{} -> {}".format(source,destination)
        if link in self.link_states:
            old_latency,old_sequence_number = self.link_states[link][-1]

            # A higher sequence number has arrived
            if sequence_number and sequence_number>old_sequence_number:
                self.link_states[link].append((latency,sequence_number))
            
            # A lower sequence number has arrived. ERROR! or I already have this seq number, do nothing
            elif sequence_number and sequence_number<=old_sequence_number:
                return False

            # this will execute if update was received from link_has_been_updated
            elif not sequence_number:
                self.link_states[link].append((latency,old_sequence_number+1))
        else:
            self.link_states[link] = [(latency,1)]

        return True
    def update_local_db(self,link, latency,sequence_number = None):
        source, destination = [int(i) for i in link.split(' -> ')]
        self.update_local_graph(source, destination,latency)
        self.update_link_state(source, destination,latency,sequence_number)
        #self.update_link_state(destination, source,latency,sequence_number)
    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        
        self.update_local_graph(self.id,neighbor,latency)
        self.update_link_state(self.id,neighbor,latency,None)
        #self.update_link_state(neighbor,self.id,latency,None)
        source,destination = sorted([self.id,neighbor])
        link = "{} -> {}".format(source,destination)
        self.send_to_neighbors(json.dumps({'type':MESSAGE_TYPES[1],'source':self.id,'destination':neighbor,'data':self.link_states}))
        pass
    
    def process_flood_message(self,m):
        incoming_link_state = m['data']

        new_links = []
        common_links = []
        correction_message = {}
        new_updates = {}

        for link in incoming_link_state.keys():
            if link not in self.link_states:
                new_links.append(link)
            else:
                common_links.append(link)
        
        for link in new_links:
            self.update_local_db(link, incoming_link_state[link][-1][0],incoming_link_state[link][-1][1])
            new_updates[link] = self.link_states[link]

        
        
        for link in common_links:
            my_latency,my_sequence_number = self.link_states[link][-1]
            incoming_latency,incoming_sequence_number = incoming_link_state[link][-1]

            # My sequence number is higher, send correction!
            if my_sequence_number>incoming_sequence_number and incoming_latency!=my_latency:
                correction_message[link] = self.link_states[link]
            elif incoming_sequence_number>my_sequence_number and my_latency==incoming_latency:
                self.update_local_db(link, incoming_latency,incoming_sequence_number)
            # Incoming seq is higher, time to update!
            elif incoming_sequence_number>my_sequence_number and my_latency!=incoming_latency:
                self.update_local_db(link, incoming_latency,incoming_sequence_number)
                new_updates[link] = self.link_states[link]

            # do nothing if its equal
        
        if correction_message:
            # Send correction message
            self.send_to_neighbor(m['source'],json.dumps({'type':MESSAGE_TYPES[2],'source':self.id,'destination':m['source'],'data':correction_message}))

        source_neighbors = [n for n in self.local_graph[m['source']].keys()]
        if new_links or new_updates:
            # Send to all neighbors except the sender
            for neighbor in self.local_graph[self.id].keys():
                if neighbor != m['source']:
                    self.send_to_neighbor(neighbor,json.dumps({'type':MESSAGE_TYPES[1],'source':self.id,'destination':neighbor,'data':new_updates}))
            
    def process_correction_message(self,m):
        
        data = m['data']

        for link in data.keys():
            self.update_local_db(link,data[link][-1][0],data[link][-1][1])
        
        # source_neighbors = [n for n in self.local_graph[m['source']].keys()]

        # for neighbor in self.local_graph[self.id].keys():
        #     if neighbor != m['source']:
        #         self.send_to_neighbor(neighbor,json.dumps({'type':MESSAGE_TYPES[1],'source':self.id,'destination':neighbor,'data':self.link_states}))

    # Fill in this function
    def process_incoming_routing_message(self, m):
        message = json.loads(m)
        m_type = message['type']
        data = message['data']
        sender = message['source']

        #Flood message
        if m_type==MESSAGE_TYPES[1]:
            self.process_flood_message(message)
        # Correction message
        elif m_type==MESSAGE_TYPES[2]:
            self.process_correction_message(message)
        elif m_type==MESSAGE_TYPES[3]:
            print("%d got message from %d at %d" %(self.id,sender,self.get_time()))
        
        pass

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        # print("Source: %d Destination: %d"%(self.id,destination))
        # print(self.local_graph)
        complete_path  = self.generate_shortest_path_graph(destination)
        if complete_path==-1:

            return -1
        else:
            return complete_path[1]
