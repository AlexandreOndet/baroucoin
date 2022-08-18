import altair as alt
import pandas as pd
import psutil
import streamlit as st
from typing import Tuple

from FullNode import *

class ChartsRenderer():
    """Renders the charts and simulation data in real-time."""
    def __init__(self):
        super(ChartsRenderer, self).__init__()
        self.df_nodes = pd.DataFrame(columns=['nodeId', 'height', 'balance', 'epoch'])
        self.epoch = 0

        self.numberOfForks = 0
        self.fork_tracker = {} # Maps a block height to its miner
        self.forkedNodes = [] # Keeps track of nodes in a forked state
        
        self.chart_title = st
        self.height_chart_display = st
        self.balance_chart_display = st		
        
        self.log_display = st
        self.log_title = st
        
        self.live_data_display = st
        self.live_data_title = st

        self.metrics_container = st
        self.previous_mining_epoch_rate = 0
        self.previous_cpu_usage = 0.
        self.total_cpu_usage = 0.

    def filter(self, record):
        """Peers log event filter used to extract information from the simulation."""
        def extract_from_key(msg: str, key: str):
            """Extract a value from a JSON string in log message (doesn't work for last key element)."""
            key_index = msg.index("'" + key + "':")
            return msg[key_index + len(key) + 4 : msg.index(',', key_index)]

        def get_node_id(msg: str):
            return msg[msg.index(':[') + 2 : msg.index(':[') + 8] # Node id is always 6 characters long

        msg = record.getMessage()

        # Track forks by looking at the height and miner of newly validated blocks and comparing to first miner who found it
        if "Received 'newBlock'" in msg:
            node_id = get_node_id(msg)
            msg_height = extract_from_key(msg, "height")
            msg_miner = extract_from_key(msg, "miner")

            if not node_id in self.forkedNodes:
                if msg_height in self.fork_tracker and msg_miner != self.fork_tracker[msg_height]:
                    self.forkedNodes.append(node_id)
                    self.numberOfForks += 1
                else:
                    self.fork_tracker[msg_height] = msg_miner
        elif "Finished sync" in msg:
            node_id = get_node_id(msg)
            if node_id in self.forkedNodes:
                self.forkedNodes.remove(node_id) # Node is now in sync with main chain

        return True

    def log(self, level: str, msg: str):
        self.log_title = self.log_title.markdown("### Log")
        if "success" in msg:
            self.log_display = self.log_display.success(msg)
        elif level == "info":
            self.log_display = self.log_display.info(msg)
        elif level == "warning":
            self.log_display = self.log_display.warning(msg)
        elif level == "error":
            self.log_display = self.log_display.error(msg)

    def render(self, data: dict):
        """Refreshes the web page view using the latest data provided by the simulation.

        :param data: a dict containing the simulation's starting parameters and current peers.
        """
        nodes = data['nodes']
        self._updateData(nodes)

        # Charts
        self.chart_title = self.chart_title.markdown("### Charts")
        self.height_chart_display = self.height_chart_display.altair_chart(self._get_blockchain_height_chart())
        self.balance_chart_display = self.balance_chart_display.altair_chart(self._get_peers_balance_chart())

        # Live data text
        self.live_data_title = self.live_data_title.markdown("### Live data")
        
        mining_epoch_rate = self._get_block_mining_rate()
        mining_epoch_rate = round(mining_epoch_rate, 2)
        
        live_data_text = "Connected peers: " + " | ".join([n.id for n in nodes]) + f" ({len(nodes)}/{data['maxNodes']} nodes)\n"
        live_data_text += "Mining difficulty: " + str(data['miningDifficulty']) + "\n"
        live_data_text += "Number of forks recorded: " + str(self.numberOfForks) + "\n"
        self.live_data_display = self.live_data_display.text(live_data_text)

        # Metrics
        if not type(self.metrics_container) is list:
            self.metrics_container = self.metrics_container.columns(2)

        self.metrics_container[0] = self.metrics_container[0].metric(
            "Average blocks per epoch", 
            mining_epoch_rate, 
            delta=round(mining_epoch_rate - self.previous_mining_epoch_rate, 2), 
        )
        self.previous_mining_epoch_rate = mining_epoch_rate

        self.total_cpu_usage += psutil.cpu_percent()
        self.metrics_container[1] = self.metrics_container[1].metric(
            "Average CPU usage", 
            round(self.total_cpu_usage / self.epoch, 2), 
            delta=round((self.total_cpu_usage / self.epoch) - (self.previous_cpu_usage / (self.epoch - 1)) if self.epoch > 1 else 0 , 2), 
        )
        self.previous_cpu_usage = self.total_cpu_usage

    def _get_block_mining_rate(self) -> Tuple[float, float]:
        """Returns the average number of blocks mined per epoch and per seconds."""
        max_height = self.df_nodes[self.df_nodes.epoch == self.epoch]['height'].max()
        return max_height/self.epoch

    def _get_blockchain_height_chart(self):
        return alt.Chart(self.df_nodes).mark_line().encode(
            x=alt.X('epoch:Q', axis=alt.Axis(tickMinStep=1)), 
            y=alt.Y('height:Q', axis=alt.Axis(tickMinStep=1)),
            color=alt.Color('nodeId:N', legend=alt.Legend(title="Peers", orient='top')),
        ).properties(
            title="Blockchain height for each peer over time",
            width=700,
            height=600,
        )

    def _get_peers_balance_chart(self):
        return alt.Chart(self.df_nodes).mark_bar().transform_filter(
            alt.datum.epoch == self.epoch
        ).encode(
            x=alt.X('balance:Q', axis=alt.Axis(tickMinStep=1)),
            y=alt.Y('nodeId:N'),
            color=alt.Color('nodeId:N', legend=None),
        ).properties(
            title="Live peers balances",
            width=700,
            height=600,
        )

    def _updateData(self, nodes: list):
        self.epoch += 1
        for node in nodes:
            self.df_nodes.loc[len(self.df_nodes)] = [node.id, node.blockchain.currentHeight, node.wallet.balance, self.epoch]