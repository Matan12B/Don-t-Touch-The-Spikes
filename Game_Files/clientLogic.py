import pygame
import queue
import threading
import sys
from ClientComm import ClientComm
import Protocol
from objects import PygameBird, Spike
import time


def display_image(image_path, txt=""):
    """
    show image from image_path
    :param image_path: path to image file
    :param title: name for pygame display
    :return: None
    """
    start_image = pygame.image.load(image_path)
    start_rect = start_image.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(start_image, start_rect)
    if txt:
        font = pygame.font.Font(None, 55)
        text = font.render(txt, True, (57, 39, 30))
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 2 + 250))
    pygame.display.flip()


def get_error(comm, ip, error):
    """
    Print the error and disconnect
    :param comm: The server communication object
    :param ip: The client's IP
    :param error: The error message
    :return: None
    """
    print("server error:", error)
    comm.close_client()
    sys.exit("error")


def get_all_birds(comm, ip, birds_data):
    """
    Create a list of all the pygame birds from the server data
    :param comm: Client communication object
    :param ip: IP of the client
    :param birds: List of bird data
    :param screen: Pygame screen
    :return: None
    """
    global players
    bird = create_bird_from_data(birds_data)
    if bird:
        players[bird.name] = bird
    else:
        print("no data to create bird")

def create_bird_from_data(bird_data):
    global my_name
    ret = None
    if len(bird_data) == 8:
        bird_name = bird_data[0]
        # If this is MY bird, use bluebird. If it's someone else, use purple
        is_self = bird_name == my_name
        color = 0 if is_self else 1
        if color == 0:
            if bird_data[6]:
                image_path = "images/bluebird.png"
            else:
                image_path = "images/bluebird_left.png"
        # purple
        else:
            if bird_data[6]:
                image_path = "images/purpleBird.png"
            else:
                image_path = "images/purpleBird_left.png"
        ret = PygameBird(bird_data, image_path, color)
    return ret


def try_register_user(comm, ip):
    """
    Register the user by sending a message to the server.
    :param comm: Client communication object
    :return: None
    """
    flag = False
    if comm.open:
        if comm.send_msg(Protocol.build_msg('r', ip)):
            print("Sending register request...")
            flag = True
        else:
            print("Failed to send register request.")
    return flag

def update_birds_positions(comm, ip, data):
    """
    Update the bird's position on the client side.
    """
    global players
    data = list(data)
    if len(data) == 6 and data[2] in players.keys():
        players[data[2]].update(data[0], data[1], data[3], data[4], data[5])
        # print(f"Bird position updated: {data[0]}, {data[1]} alive: {data[4]}")


def start_game(comm, ip="", data=""):
    """
    Handle the start game signal from the server.
    :param comm: Client communication object
    :param ip: IP of the client
    :param data: Additional data (if any)
    :return: None
    """
    global start
    start = True  # Set start to True when the server signals the game start
    print("Game has started!")


def get_spikes(comm, ip, spike_list):
    """
    Get the new spikes and start the animation.
    """
    global spikes, animation_playing, animation_offset, animation_start_time
    spikes = spike_list
    animation_playing = True
    animation_offset = -60  # Start fully inside the wall (off-screen)
    animation_start_time = pygame.time.get_ticks()


def get_my_name(comm, ip, name):
    """
    set my name to the birds name
    :return: None
    """
    global my_name
    my_name = name
    print("waiting for players...")


def disconnect_player(bird):
    """
    remove player from list
    :param bird:
    :return:
    """
    if bird.name in players.keys():
        del players[bird.name]


def game_loop(comm, ):
    """
    main game loop
    :param comm: Client communication object
    :return:
    """
    global players, animation_playing, animation_offset, animation_direction, running, won 
    # pygame.init()
    pygame.mixer.init()
    screen_width = 800
    screen_height = 600
    # screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    jump_sound = pygame.mixer.Sound("sounds/jump.wav")
    wall_hit_sound = pygame.mixer.Sound("sounds/point.wav")
    death_sound = pygame.mixer.Sound("sounds/dead.wav")
    # Main game loop
    spike = Spike(50, 35)  # Green Up Spike
    font = pygame.font.Font(None, 250)
    score = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if comm.open:
                    if comm.send_msg(Protocol.build_msg('d', my_name)):
                        pass
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # jump
                    if comm.open:
                        if comm.send_msg(Protocol.build_msg('j', my_name)):
                            pass
                    jump_sound.play()
                elif event.key == pygame.K_ESCAPE:
                    # exit game
                    pygame.quit()
                    sys.exit("exiting...")
        # Fill the screen with a background color
        screen.fill((212, 210, 210))  # grey background
        pygame.draw.circle(screen, (255, 255, 255), [400, 300], 150)# score circle
        if my_name in players.keys():
            if players[my_name].score < 10:
                score = f"0{players[my_name].score}"
            else:
                score = str(players[my_name].score)
        else:
            break
        score_text = font.render(score, True, (212, 210, 210))  # Black text
        score_rect = score_text.get_rect()
        # Position the text in the middle of the screen
        score_rect.center = (screen_width // 2, screen_height // 2)
        # Blit the text to the screen
        screen.blit(score_text, score_rect)
        if my_name in players.keys() and players[my_name].alive:  # check if my_index is valid, and the player is alive.            running = False
            for i in range(1, 13):
                spike.draw_up(screen, [i*60+10, 570])
                spike.draw_down(screen, [i*60+10, 30])
            current_time = pygame.time.get_ticks()

            # Calculate animation progress (0.0 to 1.0)
            if animation_playing:
                elapsed = current_time - animation_start_time
                progress = min(elapsed / animation_duration, 1.0)
                animation_offset = int(-60 * (1 - progress))  # from -60 to 0

                if progress >= 1.0:
                    animation_playing = False

            # Draw spikes with animated offset
            for i in spikes:
                if i != 0:
                    # Draw left spike (animate X)
                    spike.draw_side_spike(screen, [0 + animation_offset, i])
                    # Draw right spike
                    spike.draw_side_spike(screen, [screen_width - animation_offset, i])
            for p in list(players.values()):
                if p.alive:
                    p.sprite.draw(screen)
                else:
                    disconnect_player(p)
            # check left and right wall collision.
            if running:
                x_wall_collide = players[my_name].x + players[my_name].sprite.rect.width
                if players[my_name].x <= 0 or x_wall_collide >= screen_width:
                    wall_hit_sound.play()
                pygame.display.update()
                clock.tick(60)
        else:
            death_sound.play()
            font = pygame.font.Font(None, 74)
            text = font.render("YOU DIED", True, (255, 0, 0))
            screen.blit(text, (screen.get_width() // 2 - text.get_width() //
                               2, 200 // 2))
            pygame.display.update()
            time.sleep(3)
            running = False
    if won:
        print("You Won!")
        display_image("images/win.png")
        time.sleep(3)
    return score


def handle_msgs(comm, recvQ):
    """
    Handle incoming messages from the server.
    :param comm: Client communication object
    :param recvQ: Queue to receive messages
    :return: None
    """
    while True:
        msg = recvQ.get()
        opcode, data = Protocol.unpack(msg)
        # print("opcode", opcode, "data",data)
        if opcode in commands.keys():
            commands[opcode](comm, ip, data)

def win(comm, ip, data):
    """

    :param comm:
    :param ip:
    :param data:
    :return:
    """
    global running, won
    won = True
    running = False   # game loop exit

def wait_for_start():
    """
    wait for game to start.
    :return: None
    """
    while not start:
        display_image("images/wait.png")
        time.sleep(0.2)

def wait_for_enter():
    """
    wait for enter to be pressed
    :return: None
    """
    wait = True
    while wait:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                wait = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                display_image("images/inst.png","press enter to start")

commands = {'u': update_birds_positions, 's': start_game, 'b': get_all_birds, 'e': get_error, 'o': get_spikes,
            'n': get_my_name, 'w': win}
my_name = ""
running = False
players = {}
start = False  # To track if the game has started
spikes = []
animation_playing = False  # Flag to track animation state
animation_offset = 0
animation_direction = 1  # 1 for moving in, -1 for moving out
animation_start_time = 0
animation_duration = 200  # milliseconds (adjust for speed)
won = False


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Don't Touch The Spikes")
    display_image("images/start.png", "Press Enter to start or i for instruction's")

    msgsQ = queue.Queue()
    ip = "10.0.0.16"
    wait_for_enter()

    myClient = ClientComm(ip, 1234, msgsQ)
    time.sleep(0.5)
    threading.Thread(target=handle_msgs, args=(myClient, msgsQ)).start()


    if not try_register_user(myClient, ip):
        display_image("images/error.png", "Server error")
        time.sleep(4)
        pygame.quit()
        myClient.close_client()
        sys.exit("exiting...")
    wait_for_start()
    while True:

        score = game_loop(myClient)
        # After game ends, wait for retry
        display_image("images/again.png", "press i for instruction's")
        wait_for_enter()
        myClient = ClientComm(ip, 1234, msgsQ)
        time.sleep(0.5)
        won = False
        spikes = []
        animation_playing = False
        animation_offset = 0
        players = {}
        # RE-REGISTER for new round
        if not try_register_user(myClient, ip):
            display_image("images/error.png", "Server error")
            print("server error")
            time.sleep(3)
            break
        start = False  # reset start flag
        wait_for_start()
    #pygame.quit()
    # sys.exit("bye bye")

