import logging
from dotenv import load_dotenv
from pathlib import Path
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
    global simulation
    run = True
    while run:
        user_input = ""
        while (user_input.lower() not in ['q', 'a', 'd', 's', '+', '-']):
            user_input = input()

            if (user_input.lower() == 'q'):
                run = False
            elif (user_input.lower() == 'a'):
                simulation.addNewNode()
            elif (user_input.lower() == 'd'):
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
        format='T+%(relativeCreated)d\t%(levelname)s %(message)s'
    )

    logging.addLevelName(logging.DEBUG, '[DEBUG]')
    logging.addLevelName(logging.INFO, '[*]')
    logging.addLevelName(logging.WARNING, '[!]')
    logging.addLevelName(logging.ERROR, '[ERROR]')
    logging.addLevelName(logging.CRITICAL, '[CRITICAL]')

    simulation = Orchestrator()
    renderer = ChartsRenderer(simulation=simulation)
    t = Thread(target=handle_input)
    
    simulation.start()
    t.start()

    a = animation.FuncAnimation(renderer.fig, renderer.render, interval=simulation.epoch_time, blit=True)
    plt.show()