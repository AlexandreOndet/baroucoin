import altair as alt
import pandas as pd
import streamlit as st

class ChartsRenderer():
    """Renders the charts in real-time."""
    def __init__(self):
        super(ChartsRenderer, self).__init__()
        self.df_nodes = pd.DataFrame(columns=['nodeId', 'height', 'epoch'])
        self.epoch = 0
        self.dataframe_display = None
        self.chart_display = None
        self.log_display = None
        self.nodes_display = None

    def log(self, msg: str):
        if not self.log_display:
            self.log_display = st
        self.log_display = self.log_display.info(msg)

    def render(self, nodes: list):
        self._updateData(nodes)

        # if not self.dataframe_display:
        # 	self.dataframe_display = st
        # self.dataframe_display = self.dataframe_display.dataframe(self.df_nodes)

        if not self.chart_display:
            self.chart_display = st
        self.chart_display = self.chart_display.altair_chart(self._plot())

        if not self.nodes_display:
            self.nodes_display = st
        self.nodes_display = self.nodes_display.text('Live peers: ' + ' | '.join([n.id for n in nodes]))

    def _plot(self):
        return alt.Chart(self.df_nodes).mark_line().encode(
            x=alt.X('epoch:Q', axis=alt.Axis(tickMinStep=1)), 
            y=alt.Y('height:Q', axis=alt.Axis(tickMinStep=1)), 
            color=alt.Color('nodeId:N', legend=alt.Legend(orient='top')),
        ).properties(
            width=700,
            height=600,
        )

    def _updateData(self, nodes: list):
        self.epoch += 1
        for node in nodes:
            self.df_nodes.loc[len(self.df_nodes)] = [node.id, node.blockchain.currentHeight, self.epoch]