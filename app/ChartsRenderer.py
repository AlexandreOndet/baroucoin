import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd

class ChartsRenderer():
    """docstring for ChartsRenderer"""
    def __init__(self, simulation):
        super(ChartsRenderer, self).__init__()
        self.simulation = simulation
        self.df_nodes = pd.DataFrame(columns=['nodeId', 'height', 'epoch']).astype({'nodeId': 'string', 'height': 'int', 'epoch': 'int'})
        self.plots = {}
        self.x_limit = 20
        self.y_limit = 30
        self.fig = plt.figure()
        self.fig.set_size_inches(12, 8)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.set_xlim(0, self.x_limit)
        self.ax.set_ylim(0, self.y_limit)

    def render(self, frame):
        for node in self.simulation.nodes:
            node_id = node.id
            if node_id not in self.plots:
                self.plots[node_id] = self.ax.plot([], [])[0]
            self.df_nodes.loc[len(self.df_nodes)] = [node_id, node.blockchain.currentHeight, frame]
            
            df = self.df_nodes[self.df_nodes['nodeId'] == node_id]
            self.plots[node_id].set_data(df['epoch'], df['height'])

        max_height = self.df_nodes['height'].max()
        update_axis = (frame > 1 and frame % self.x_limit == 0) or (not pd.isna(max_height) and max_height > 1 and max_height % self.y_limit == 0)
        if update_axis:
            self.x_limit += self.x_limit
            self.y_limit += self.y_limit
            self.ax.set_xlim(0, self.x_limit)
            self.ax.set_ylim(0, self.y_limit)
            self.ax.figure.canvas.draw()

        return self.plots.values()