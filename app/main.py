import logging
from dotenv import load_dotenv
from pathlib import Path
from streamlit.scriptrunner import add_script_run_ctx
from threading import Thread

from app.ChartsRenderer import *
from app.Orchestrator import *

load_dotenv()
app_dir = Path(__file__).parent

def handle_input(simulation):
    run = True
    while run:
        user_input = ""
        while (user_input.lower() not in ['q', 'a', 'd', 's']):
            user_input = input()

            if (user_input.lower() == 'q'):
                run = False
            elif (user_input.lower() == 'a'):
                simulation.addNewNode()
            elif (user_input.lower() == 'd'):
                simulation.removeLastNode()
            elif (user_input.lower() == 's'):
                simulation.syncAllNodes()

    simulation.stop()


if __name__ == "__main__":
    # logging.disable(logging.INFO) # Use this to disable debug and print infos
    file_handler = logging.FileHandler(app_dir / "simulation.log", mode='w')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    logging.basicConfig(
        handlers=[file_handler, console_handler],
        level=logging.DEBUG,
        format='T+%(relativeCreated)d\t%(levelname)s %(message)s'
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
        t = Thread(target=handle_input, args=(simulation,))
        
        add_script_run_ctx(simulation)
        add_script_run_ctx(t)
            
        simulation.start()
        t.start()
        
        simulation.join()