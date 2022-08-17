import logging
from dotenv import load_dotenv
from pathlib import Path
from streamlit.scriptrunner import add_script_run_ctx
from threading import Thread

from app.ChartsRenderer import *
from app.Orchestrator import *

load_dotenv()
app_dir = Path(__file__).parent

def handle_input():
    """Handles the console input for the simulation (commands are case-insensitive).

    The commands are:
    - 'q/Q': Quit the simulation
    - 'a/A': Add a new peer (up to the maximum peer capacity of the simulation)
    - 'd/D': Remove the last added peer from the simulation (can be added back with a/A)
    - 's/S': Synchronize all peers to the highest blockchain
    - '+': Increase mining difficulty
    - '-': Decrease mining difficulty
    """

    st.markdown("### Usage\n"
        "Run the commands in the console (press a key then <kbd>ENTER</kbd>).\n\n"
        "Availables commands (case insensitive):\n"
        "- <kbd>q</kbd> Quit the simulation\n"
        "- <kbd>a</kbd> Add a new peer (up to the maximum peer capacity of the simulation)\n"
        "- <kbd>r</kbd> Remove the last added peer from the simulation (can be added back with a/A)\n"
        "- <kbd>s</kbd> Synchronize all peers to the highest blockchain\n"
        "- <kbd>+</kbd> Increase mining difficulty\n"
        "- <kbd>-</kbd> Decrease mining difficulty\n", 
        unsafe_allow_html=True
    )

    global simulation
    run = True
    while run:
        user_input = ""
        while (user_input.lower() not in ['q', 'a', 'r', 's', '+', '-']):
            user_input = input()

            if (user_input.lower() == 'q'):
                run = False
            elif (user_input.lower() == 'a'):
                simulation.addNewNode()
            elif (user_input.lower() == 'r'):
                simulation.removeLastNode()
            elif (user_input.lower() == 's'):
                simulation.syncAllNodes()
            elif (user_input.lower() == '+'):
                simulation.increaseDifficulty()
            elif (user_input.lower() == '-'):
                simulation.decreaseDifficulty()

    simulation.stop()


if __name__ == "__main__":
    # logging.disable(logging.INFO) # Use this to disable debug and print infos
    file_handler = logging.FileHandler(app_dir / "simulation.log", mode='w')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    logging.basicConfig(
        handlers=[file_handler, console_handler],
        level=logging.DEBUG,
        format='T+%(relativeCreated)d\t%(levelname)s %(message)s',
        force=True
    )

    logging.addLevelName(logging.DEBUG, '[DEBUG]')
    logging.addLevelName(logging.INFO, '[*]')
    logging.addLevelName(logging.WARNING, '[!]')
    logging.addLevelName(logging.ERROR, '[ERROR]')
    logging.addLevelName(logging.CRITICAL, '[CRITICAL]')
    
    inputs_empty = st.empty() # Used to clear out the inputs after the simulation starts
    inputs_container = inputs_empty.container()
    
    # Simulation parameters
    consensus_input = inputs_container.selectbox("Consensus algorithm", ("PoW (Proof-Of-Work)", "PoS (Proof-Of-Stake)"))
    max_nodes_input = inputs_container.number_input("Maximum number of nodes", 2, 10, value=5)
    starting_nodes_input = inputs_container.number_input("Number of starting nodes", 2, int(max_nodes_input), value=3)
    epoch_time_input = inputs_container.number_input("Epoch duration (in milliseconds)", 100, 1000*60*60, value=1000, step=100)
    if consensus_input[:3] == "PoW":
        mining_difficulty_input = inputs_container.number_input("Mining difficulty", 0., 15., value=5., step=0.5)
    elif consensus_input[:3] == "PoS":
        mining_difficulty_input = inputs_container.number_input("Mining difficulty", 0, 10_000_000, value=100_000, step=1)

    # Random events parameters
    transaction_frequency_input = inputs_container.slider("Transaction frequency", 0., 1., value=.3, format="%f")
    disconnect_frequency_input = inputs_container.slider("Disconnect frequency", 0., 1., value=.01, format="%f")
    new_peer_frequency_input = inputs_container.slider("New peer frequency", 0., 1., value=.02, format="%f")

    # Tokenomics parameters
    initial_supply_input = inputs_container.number_input("Initial coin supply", 1, 2**32, value=100_000, step=1)
    initial_transfer_amount_input = inputs_container.number_input("Initial balance of starting nodes", 1, 2**32, value=50, step=1)

    start_btn_container = st.empty()
    start_btn = start_btn_container.button("Start simulation", key='1')
    if start_btn:
        inputs_empty.empty()
        start_btn = start_btn_container.button("Start simulation", key='2', disabled=True)

        renderer = ChartsRenderer()
        # Makes all log messages pass through the renderer log filter for extracting informations
        #file_handler.addFilter(renderer.filter)

        simulation = Orchestrator(renderer=renderer)
        simulation.setup(
            starting_nodes_input,
            max_nodes_input,
            epoch_time_input,
            mining_difficulty_input,
            transaction_frequency_input,
            disconnect_frequency_input,
            new_peer_frequency_input,
            consensus_input[:3],
            initial_supply_input,
            initial_transfer_amount_input
        )

        t = Thread(target=handle_input)
        logging.info("--- Enter simulation commands here ---")
        # Disable message logging for console before starting the simulation
        console_handler.setLevel(logging.ERROR)
        
        add_script_run_ctx(simulation)
        add_script_run_ctx(t)

        simulation.start()
        t.start()

        simulation.join()
        st.markdown("# Reload the page to start a new simulation")