from simulator.node import Node

# maintain a graph for all links in the system
# Also keep track of shortest paths to other nodes in the system
import json
MESSAGE_TYPES = {0:'LINK_UPDATE'}

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.local_graph = {}
        self.link_states = {}

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"
    def update_local_graph(self,source,destination, latency):
        # add
        # update
        # delete
        if destination not in self.local_graph:
                self.local_graph[destination] = {}
        if source not in self.local_graph:
            self.local_graph[source] = {}
        if latency!=-1:
            
            self.local_graph[source][destination] = latency
            self.local_graph[destination][source] = latency
        else:
            if destination in self.local_graph[source]:
                del self.local_graph[source][destination]
            if source in self.local_graph[destination]:
                del self.local_graph[destination][source]
            
            if not self.local_graph[source]:
                del self.local_graph[source]
            if not self.local_graph[destination]:
                del self.local_graph[destination]
        #print("Node: ",self.id,"says: ",self.local_graph,"Time:",self.get_time())
    def update_link_state(self,source,destination,latency):
        link = "{} -> {}".format(source,destination)
        if link in self.link_states:
            old_latency,seq_number = self.link_states[link][-1]
            if old_latency!=latency:
                self.link_states[link].append((latency,seq_number+1))
        else:
            self.link_states[link] = [(latency,1)]
        print("Node: ",self.id,"says: My link state",self.link_states,"Time:",self.get_time())

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        
        self.update_local_graph(self.id,neighbor,latency)
        self.update_link_state(self.id,neighbor,latency)
        self.update_link_state(neighbor,self.id,latency)

        #self.send_to_neighbors(json.dumps({'type':MESSAGE_TYPES[0],'source':self.id,'destination':neighbor,'latency':latency}))
        pass

    # Fill in this function
    def process_incoming_routing_message(self, m):
        print("%d receive a message at Time %d. " % (self.id,self.get_time()))
        data = json.loads(m)

        if data['type']==MESSAGE_TYPES[0]:
            self.update_local_graph(data['source'],data['destination'],data['latency'])

        pass

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):

        return -1
