from simulator.node import Node

# maintain a graph for all links in the system
# Also keep track of shortest paths to other nodes in the system
# Send flood message containing all the link-state except incoming to neighbors
# Send correction message to sender if you got stale value

import json
MESSAGE_TYPES = {0:'LINK_UPDATE',1:'FLOOD_MESSAGE',2:"CORRECTION_MESSAGE"}

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.local_graph = {} # key: node_id ; value: {destination_id:latency}
        self.link_states = {} # key: "{source} -> {destination}" ; value: [(latency,sequence_no)]

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

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
        link = "{} -> {}".format(source,destination)
        if link in self.link_states:
            old_latency,old_sequence_number = self.link_states[link][-1]

            # A higher sequence number has arrived
            if sequence_number and sequence_number>old_sequence_number:
                self.link_states[link].append((latency,sequence_number))
            
            # A lower sequence number has arrived. ERROR!
            elif sequence_number and sequence_number<old_sequence_number:
                return False
            
            # I already have this seq number, do nothing
            elif sequence_number and sequence_number==old_sequence_number:
                pass

            # this will execute if update was received from link_has_been_updated
            else:
                self.link_states[link].append((latency,old_sequence_number+1))
        else:
            self.link_states[link] = [(latency,1)]

        return True
    def update_local_db(self,link, latency):
        source, destination = [int(i) for i in link.split(' -> ')]
        self.update_local_graph(source, destination,latency)
        self.update_link_state(source, destination,latency,None)
        self.update_link_state(destination, source,latency,None)
    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        
        self.update_local_graph(self.id,neighbor,latency)
        self.update_link_state(self.id,neighbor,latency,None)
        self.update_link_state(neighbor,self.id,latency,None)
        #self.send_flood()
        #self.send_to_neighbors(json.dumps({'type':MESSAGE_TYPES[0],'source':self.id,'destination':neighbor,'latency':latency}))
        pass
    
    def process_flood_message(self,m):
        incoming_link_state = m['data']

        new_links = []
        common_links = []
        correction_message = {}



        for link in incoming_link_state.keys():
            if link not in self.link_states:
                new_links.append(link)
            else:
                common_links.append(link)
        
        for link in new_links:
            self.update_local_db(link, incoming_link_state[link][-1][0])
        
        new_updates = False
        for link in common_links:
            my_latency,my_sequence_number = self.link_states[link][-1]
            incoming_latency,incoming_sequence_number = incoming_link_state[link][-1]

            # My sequence number is higher, send correction!
            if my_sequence_number>incoming_sequence_number:
                correction_message[link] = self.link_states[link]
            # Incoming seq is higher, time to update!
            elif incoming_sequence_number>my_sequence_number:
                new_updates = True
                self.update_local_db(link, incoming_latency)
            # do nothing if its equal
        
        if correction_message:
            # Send correction message
            self.send_to_neighbor(neighbor,json.dumps({'type':MESSAGE_TYPES[2],'source':self.id,'destination':m['source'],'data':correction_message}))

        
        if new_links or new_updates:
            # Send to all neighbors except the sender
            for neighbor in self.local_graph.keys():
                if neighbor != m['source']:
                    self.send_to_neighbor(neighbor,json.dumps({'type':MESSAGE_TYPES[1],'source':self.id,'destination':neighbor,'data':self.link_states}))
            
    def process_correction_message(self,m):
        data = m['data']

        for link in data.keys():
            self.update_local_db(link,data[link][-1][0])


    # Fill in this function
    def process_incoming_routing_message(self, m):
        print("%d receive a message at Time %d. " % (self.id,self.get_time()))
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
        
        
        pass

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):

        return -1
