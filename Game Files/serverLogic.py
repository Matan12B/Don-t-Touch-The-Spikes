import queue
import threading
from ServerComm import ServerComm
import Protocol
from objects import Bird
import time
from random import randint

def register_user(comm, ip, data):
    """
    Registers a user and creates a bird object for them.
    :param comm: Server communication object
    :param ip: The client's IP
    :return: None
    """
    global game_start_time, is_countdown, start, xSpeed
    if start:
        comm.send_msg(ip, Protocol.build_msg('e', "game already started"))
    print(f"Registering user from {ip}")  # Debugging print
    length = len(birds_players)
    # Max 4 players
    # or tick = 60 sec
    max_players = 4
    min_players = 2
    if length <= max_players-1 and not start:
        height = 70
        width = 70
        y = 300 - length * (height + 5)
        # (screen width - bird width)/2
        x = (800-width)/2
        xSpeed = 15 * (length*1.5)
        xDirection = True if length % 2 == 0 else False
        yDirection = False
        bird = Bird([f"p{length+1}", x, y, height, width, xSpeed, xDirection, yDirection])
        birds_players[bird.name] = (bird, ip)
        print(ip, "added")
        comm.send_msg(ip, Protocol.build_msg('n', bird.name))
        if length == min_players-1:  # when minimum player joins
            game_start_time = time.time()  # start the countdown
            is_countdown = True
        elif length == max_players-1 and not start:
            for p in list(birds_players.values()):
                p[0].xSpeed= xSpeed
            start_game(comm)
            is_countdown = False
    else:
        comm.send_msg(ip, Protocol.build_msg('e', "cant join game"))

def check_hit_spike(comm, bird):
    """
    Checks if a bird has hit a spike or the top/bottom boundaries.
    """
    global spike_pos, last_spike_update, spike_cooldown
    flag = False
    if bird.y >= 530 or bird.y <= 30:
        flag = True
    else:
        if time.time() - last_spike_update < spike_cooldown:
            flag = False
        else:
            # Check for collision with either left or right side spikes
            if bird.x <= 10 or bird.x>= wall - bird.width:
                for spike_y in spike_pos:
                    if bird.y + bird.height - 5 > spike_y and bird.y + 5 < spike_y + 10:
                        flag = True
                        break
    return flag

def send_all_current_birds(comm):
    """
    broadcast all the players in the game to everyone that connected
    :return:
    """
    for b in list(birds_players.values()):
        data = str(b[0].create_bird_data())
        if data:
            msg = Protocol.build_msg('b', data)
            comm.broadcast(msg)
        else:
            print(f"no bird data to send")

def generate_spikes_pos():
    """
    create a list of spike positions
    :return:
    """
    global spike_pos
    spike_pos = [0] * 11
    for i in range(7):
        random_y = randint(0, 10)
        spike_pos[random_y] = random_y * 60
    return spike_pos

def update_spikes_positions(comm, force_update=False): # added force update parameter
    """
    Broadcasts new spike positions to all clients.
    """
    global last_spike_update
    if force_update or time.time() - last_spike_update >= 1.5:  # Check if 2 seconds have passed or force update
        new_spikes = generate_spikes_pos()
        comm.broadcast(Protocol.build_msg('o', new_spikes))
        last_spike_update = time.time()

def start_game(comm):
    """
    inform all players that the game is starting
    :return:
    """
    global start, jump
    send_all_current_birds(comm)
    comm.broadcast(Protocol.build_msg('s', ""))
    # wait so the players have a change to see who they are playing
    time.sleep(3)
    jump = True
    start = True

def update_birds_positions(comm):
    """
    Periodically update the positions of all birds and send to all clients.
    :param comm: The server communication object
    :return: None
    """
    global wall_collision_triggered, allow_jump
    for bird, ip in list(birds_players.values()):
        if bird.jumped and allow_jump:
            bird.y += bird.ySpeed  # apply the jump.
            bird.jumped = False

        # Store the collision result to avoid multiple calls.
        if check_hit_spike(comm, bird):
            # dead
            bird.alive = False
            # new speed after birds die
            new_speed = bird.xSpeed/1.5
            for b, _ in list(birds_players.values()):
                b.xSpeed = new_speed
        # Check wall collision and update spikes only once per wall contact.
        if bird.x <= 0 or bird.x >= wall - bird.width:
            if not wall_collision_triggered:
                update_spikes_positions(comm)
                wall_collision_triggered = True  # Set the flag as spike update triggered.
        else:
            wall_collision_triggered = False  # Reset flag when the bird is away from the wall.

        bird.moveX([0, 800])
        bird.moveY([0, 600])
    # Send the updated positions to all connected clients
    for bird in list(birds_players.values()):
        msg = Protocol.build_msg('u', [bird[0].x, bird[0].y, bird[0].name, bird[0].xDirection,
                                       bird[0].alive, bird[0].score])
        time.sleep(0.02)
        comm.broadcast(msg)
        if not bird[0].alive:
            disconnect_player(comm, bird[1], bird[0].name)
            print(f"{bird[0].name} disconnected.")
            continue

def disconnect_player(comm, ip, name):
    """
    disconnect player
    :return:
    """
    if name in birds_players.keys():
        del birds_players[name]
        comm.close_client(ip)

def handle_jump(comm, ip, name):
    """
    handle jump request
    :param data:
    :return:
    """
    if name in list(birds_players.keys()):
        birds_players[name][0].jump()
        bird = birds_players[name][0]
        msg = Protocol.build_msg('u', [bird.x, bird.y, bird.name, bird.xDirection, bird.alive])
        comm.broadcast(msg)

def handle_disconnect(comm, ip, name):
    """
    Handle client disconnection.
    """
    if name in birds_players:
        _, ip = birds_players[name]
        disconnect_player(comm, ip, name)
        print(f"{name} disconnected.")

def handle_msgs(comm, recvQ):
    """
    Handle incoming messages from clients.
    :param comm: Server communication object
    :param recvQ: Queue to receive messages
    :return: None
    """
    while True:
        ip, msg = recvQ.get()
        opcode, data = Protocol.unpack(msg)
        if opcode in commands.keys():
            commands[opcode](comm, ip, data)
        else:
            print(f"Unknown opcode received: {opcode}")


allow_jump = False
xSpeed = 20
countdown_duration = 5
# Command handlers
commands = {}
wall = 800
birds_players = {}
start = False
spike_pos = []
last_spike_update = 0
spike_cooldown = 1.2  # seconds of safe period after wall contact
wall_collision_triggered = False
is_countdown = False
game_start_time = 0
commands['d'] = handle_disconnect
commands['r'] = register_user
commands['j'] = handle_jump
if __name__ == "__main__":
    msgsQ = queue.Queue()
    myServer = ServerComm(1234, msgsQ)
    threading.Thread(target=handle_msgs, args=(myServer, msgsQ)).start()
    print("waiting to start...")
    last_countdown_update = 0
    while True:
        if not start:
            if is_countdown:
                current_time = time.time()
                elapsed = current_time - game_start_time
                remaining = int(countdown_duration - elapsed)
                print(remaining)
                if remaining <= 0 and not start:
                    for p in list(birds_players.values()):
                        p[0].xSpeed = xSpeed
                    start_game(myServer)
                    is_countdown = False
                elif last_countdown_update != current_time:
                    last_countdown_update = current_time
            time.sleep(0.1)
            continue
        else:
            alive_birds = [bird for bird, _ in list(birds_players.values()) if bird.alive]
            if len(alive_birds) == 1:
                winning_bird = alive_birds[0]
                msg = Protocol.build_msg('w', "")
                print(winning_bird.name, "wins!")
                myServer.send_msg(birds_players[winning_bird.name][1], msg)
                print("Resetting game...")
                # Reset game variables
                xSpeed = 20
                birds_players = {}
                start = False
                spike_pos = []
                last_spike_update = 0
                spike_cooldown = 1.2  # seconds of safe period after wall contact
                wall_collision_triggered = False
                is_countdown = False
                continue
            else:
                update_birds_positions(myServer)
