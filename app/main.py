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
    """
    Handles the console input for the simulation (commands are case-insensitive).

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

    start_btn_container = st.empty()
    start_btn = start_btn_container.button("Start simulation", key='1')
    if start_btn:
        start_btn = start_btn_container.button("Start simulation", disabled=True, key='2')

        renderer = ChartsRenderer()
        simulation = Orchestrator(renderer=renderer)
        t = Thread(target=handle_input)

        logging.info("--- Enter simulation commands here ---")
        # Disable message logging for console before starting the simulation
        console_handler.setLevel(logging.ERROR)
        
        add_script_run_ctx(simulation)
        add_script_run_ctx(t)

        simulation.start()
        t.start()

        simulation.join()