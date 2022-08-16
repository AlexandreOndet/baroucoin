import altair as alt
import pandas as pd
import streamlit as st
from typing import Tuple

from FullNode import *

class ChartsRenderer():
    """Renders the charts and simulation data in real-time."""
    def __init__(self):
        super(ChartsRenderer, self).__init__()
        self.df_nodes = pd.DataFrame(columns=['nodeId', 'height', 'balance', 'epoch'])
        self.epoch = 0
        
        self.chart_title = st
        self.height_chart_display = st
        self.balance_chart_display = st		
        
        self.log_display = st
        self.log_title = st
        
        self.live_data_display = st
        self.live_data_title = st

        self.metrics_container = st
        self.previous_mining_epoch_rate = 0
        self.previous_mining_time_rate = 0

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
        
        # Keep only synced nodes for updating data
        nodes = [n for n in data['nodes'] if n.isNodeSynced()]
        self._updateData(nodes)

        # Charts
        self.chart_title = self.chart_title.markdown("### Charts")
        self.height_chart_display = self.height_chart_display.altair_chart(self._get_blockchain_height_chart())
        self.balance_chart_display = self.balance_chart_display.altair_chart(self._get_peers_balance_chart())

        # Live data text
        self.live_data_title = self.live_data_title.markdown("### Live data")
        
        (mining_epoch_rate, mining_time_rate) = self._get_block_mining_rate(data['epochTime'])
        (mining_epoch_rate, mining_time_rate) = (round(mining_epoch_rate, 2), round(mining_time_rate, 2))
        
        live_data_text = "Connected peers: " + " | ".join([n.id for n in nodes]) + f" ({len(nodes)}/{data['maxNodes']} nodes)\n"
        live_data_text += "Mining difficulty: " + str(data['miningDifficulty']) + "\n"
        self.live_data_display = self.live_data_display.text(live_data_text)

        # Metrics
        if not type(self.metrics_container) is list:
            self.metrics_container = self.metrics_container.columns(2)

        self.metrics_container[0] = self.metrics_container[0].metric(
            "Average blocks per second", 
            mining_time_rate, 
            delta=round(mining_time_rate - self.previous_mining_time_rate, 2), 
        )
        self.previous_mining_time_rate = mining_time_rate

        self.metrics_container[1] = self.metrics_container[1].metric(
            "Average blocks per epoch", 
            mining_epoch_rate, 
            delta=round(mining_epoch_rate - self.previous_mining_epoch_rate, 2), 
        )
        self.previous_mining_epoch_rate = mining_epoch_rate

    def _get_block_mining_rate(self, epochTime: int) -> Tuple[float, float]:
        """Returns the average number of blocks mined per epoch and per seconds."""
        max_height = self.df_nodes[self.df_nodes.epoch == self.epoch]['height'].max()
        return (max_height/self.epoch, epochTime * max_height/self.epoch/1000)

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
        return alt.Chart(self.df_nodes).mark_bar().encode(
            x=alt.X('nodeId:N'),
            y=alt.Y('max(balance):Q', axis=alt.Axis(tickMinStep=1)),
            color=alt.Color('nodeId:N', legend=alt.Legend()),
        ).properties(
            title="Live peers balances",
            width=700,
            height=600,
        )

    def _updateData(self, nodes: list):
        self.epoch += 1
        for node in nodes:
            self.df_nodes.loc[len(self.df_nodes)] = [node.id, node.blockchain.currentHeight, node.wallet.balance, self.epoch]