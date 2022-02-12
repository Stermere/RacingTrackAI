import pygame # version 2.0.0
import ctypes
import os
import math
import numpy
import tensorflow as tf # version 2.5.0 last tested version
from Map_Road_Classes import Map, RoadPiece
from DeepQ_network import Agent

# pygame setup
ctypes.windll.user32.SetProcessDPIAware()
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)
pygame.init()
size = (1920, 1080)
clock = pygame.time.Clock()
screen = pygame.display.set_mode(size)
pygame.display.set_caption('deepQ race course')

# importing block image
road1 = pygame.image.load('map_pieces/Road_1.png')
road2 = pygame.image.load('map_pieces/Road_2.png')

# Map file
map_directory = 'map1.txt'


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super(Player, self).__init__()
        self.image = pygame.image.load('car.png')
        self.a = 0
        self.v = 0
        self.v_dir = 0
        self.x, self.y = find_start_loc()
        self.x -= camera.movement_offset[0]
        self.y -= camera.movement_offset[1]
        self.angle = 90
        self.angle_v = 0
        self.over = False
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.input_num = 16
        self.lines = []
        self.state = numpy.array([])
        self.state_prev = numpy.array([])
        self.outputs()

    def start(self, input_):
        action = self.inputs(input_)

        for act in action:
            if act == 0:
                self.a = 6
            if act == 3:
                self.a = -6

        self.a = self.a * 0.9

        self.calculate_angle(action)

        self.position_calculations()
        self.update_()

    def calculate_angle(self, action):
        for act in action:
            if act == 1:
                self.angle_v += 5.5
            if act == 2:
                self.angle_v -= 5.5

        self.angle_v *= 0.7
        self.angle += self.angle_v

    def inputs(self, a):
        # key = pygame.key.get_pressed()
        # action = []
        # if key[pygame.K_w]:
        #    action.append(0)
        # if key[pygame.K_a]:
        #    action.append(1)
        # if key[pygame.K_d]:
        #    action.append(2)
        # return action

        action = []
        if a == 0:
            action.append(0)
        elif a == 1:
            action.append(1)
        elif a == 2:
            action.append(2)
        elif a == 3:
            pass
            # action.append(3)
        return action

    def update_(self):
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def position_calculations(self):
        # calculate the new vector for velocity
        vector1_magnitude = self.a
        vector1_angle = self.angle
        vector2_magnitude = self.v
        vector2_angle = self.v_dir

        vector1_x = vector1_magnitude * math.cos(vector1_angle * math.pi / 180)
        vector2_x = vector2_magnitude * math.cos(vector2_angle * math.pi / 180)
        vector1_y = vector1_magnitude * math.sin(vector1_angle * math.pi / 180)
        vector2_y = vector2_magnitude * math.sin(vector2_angle * math.pi / 180)

        vector_sum_x = vector1_x + vector2_x
        vector_sum_y = vector1_y + vector2_y

        self.x += vector_sum_x
        self.y -= vector_sum_y

        vector_sum_magnitude = math.sqrt(math.pow(vector_sum_x, 2) + math.pow(vector_sum_y, 2))
        vector_sum_angle = math.atan2(vector_sum_y, vector_sum_x)
        vector_sum_angle = vector_sum_angle * (180 / math.pi)

        # update the vector
        self.v = vector_sum_magnitude * 0.8
        self.v_dir = vector_sum_angle

    def draw(self):
        if not self.over:
            rotated_surface = pygame.transform.rotate(self.image, self.angle - 90)
            (xy) = self.rotate_center(rotated_surface)
            screen.blit(rotated_surface, xy)

    def rotate_center(self, surface):
        s = pygame.Surface.get_size(surface)
        x = self.x - (s[0] / 2)
        y = self.y - (s[1] / 2)
        return x, y

    def outputs(self):
        player_point = (self.x, self.y)
        inputs = self.input_num
        angle_difference = 360 / inputs
        self.state_prev = self.state
        self.state = []
        self.lines = []

        def step_forward():
            x = int(player_point[0] + (math.cos(degree * math.pi / 180) * length))
            y = int(player_point[1] + (math.sin(degree * math.pi / 180) * length))
            return x, y

        for i in range(0, inputs):
            length = 1
            degree = (angle_difference * i) - self.angle - 90

            x, y = step_forward()
            try:
                while screen.get_at((x, y))[0] == 0 and length < 600:
                    length += 1
                    x, y = step_forward()
            except IndexError:
                pass
            dist = math.sqrt(math.pow(x - player_point[0], 2) + math.pow(y - player_point[1], 2))
            self.state.append(dist)
            self.lines.append(player_point)
            self.lines.append((x, y))
        self.state = numpy.array(self.state)
        return


# class used to provide x and y offsets from mouse movement to test the camera
class Camera:
    def __init__(self):
        self.x, self.y = pygame.mouse.get_pos()
        self.prev_x, self.prev_y = self.x, self.y
        self.movement_offset = [0, 0]

    # calculates the offset that should be returned
    def return_offset(self, speed=0.1, follow_player=True):
        x, y = 0, 0
        self.prev_x, self.prev_y = self.x, self.y
        self.x, self.y = pygame.mouse.get_pos()
        if follow_player:
            x, y = ((size[0] / 2) - player.x) * speed, ((size[1] / 2) - player.y) * speed
        # allow the user to look around if they want with this addition
        if pygame.mouse.get_pressed(num_buttons=3)[0] == 1:
            x, y = self.x - self.prev_x, self.y - self.prev_y

        self.movement_offset = self.movement_offset[0] - x, self.movement_offset[1] - y
        return x, y

    def select_block(self):
        player_x = player.x + self.movement_offset[0]
        player_y = player.y + self.movement_offset[1]
        row = player_y // block_map.BLOCK_SIZE
        column = player_x // block_map.BLOCK_SIZE
        return [row, column]


class Reward:
    def __init__(self):
        self.block1 = camera.select_block()
        block2 = self.block1[0] + 1
        self.block2 = [block2, self.block1[1]]
        self.block_dict = self.gen_block_dic()
        self.reward = 0
        self.score = 0

    # generate a dictionary of good and bad blocks based on the current block that the player is in and the previous
    # block that it was in
    def gen_block_dic(self):
        block_list = {'good': [], 'bad': []}
        options = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        for o in options:
            c = self.block1[0] + o[0]
            r = self.block1[1] + o[1]
            b = [c, r]
            if not b == self.block2:
                block_list['good'].append(b)
            c = self.block2[0] + o[0]
            r = self.block2[1] + o[1]
            b = [c, r]
            if not b == self.block1:
                block_list['bad'].append(b)
        return block_list

    # determines if the new block the player entered is good or bad and updates the reward and block dic respectively
    def reward_calc(self):
        current_block = camera.select_block()
        # logic for give a reward based on if it moved forward
        for key, value in self.block_dict.items():
            for item in value:
                if current_block == item:
                    if key == 'good':
                        self.block2 = self.block1
                        self.block1 = item
                        self.reward += 15
                        self.score += 1
                        self.block_dict = self.gen_block_dic()

                    elif key == 'bad':
                        self.block1 = self.block2
                        self.block2 = item
                        player.over = True
                        self.block_dict = self.gen_block_dic()
        # other reasons to give reward
        if player.over:
            self.reward -= 15
        return self.reward


class Editor:
    # importing block images
    ROAD1 = pygame.image.load('map_pieces/Road_1.png')
    ROAD2 = pygame.image.load('map_pieces/Road_2.png')
    BLOCK_SIZE = Map.BLOCK_SIZE

    def __init__(self):
        self.movement_offset = camera.movement_offset
        self.x, self.y = pygame.mouse.get_pos()
        self.screen_width = 1920
        self.screen_height = 1080

    def update_mouse_pos(self):
        self.x, self.y = pygame.mouse.get_pos()
        self.movement_offset = camera.movement_offset

    def select_block(self, mbe):
        global block_map
        true_x = self.x + self.movement_offset[0]
        true_y = self.y + self.movement_offset[1]
        row = true_y // Editor.BLOCK_SIZE
        column = true_x // Editor.BLOCK_SIZE

        # check if a click was registered using the mouseevent variable passed from the main function

        place_rotate_block = False
        change_block_type = False
        for item in mbe:
            if item == 3:
                place_rotate_block = True
            if item == 2:
                change_block_type = True

        # take action based on if a click was registered
        if place_rotate_block == True or change_block_type == True:
            in_list = False
            for block in block_map.block_data:
                if block.id[:2] == [row, column]:
                    in_list = True
                    block_to_edit = block
            if in_list:
                self.edit_block(block_to_edit, place_rotate_block, change_block_type)

            else:
                block_map.block_data.append(RoadPiece([row, column, 1], Map.ROAD1, 0,
                                                      column * Editor.BLOCK_SIZE - self.movement_offset[0],
                                                      row * Editor.BLOCK_SIZE - self.movement_offset[1],
                                                      Editor.BLOCK_SIZE))

    def edit_block(self, block, a, t):
        if a:
            block.rotate_block()
        if t:
            pop = block.change_type()
            if pop:
                for x, block_ in enumerate(block_map.block_data):
                    if block.id[:2] == block_.id[:2]:
                        block_map.block_data.pop(x)
        block.format_image()

    def ui_buttons(self, mbe):
        qc = 20
        sc = 30
        rc = 40
        # check if a click was registered using the mouseevent variable passed from the main function
        clicked = False
        for item in mbe:
            if item == 1:
                clicked = True

        # back button
        if self.screen_width / 2 <= self.x <= self.screen_width / 2 + 140 \
                and self.screen_height - 40 <= self.y <= self.screen_height:
            qc = 40
            # checks if a mouse is clicked
            if clicked:
                qc = 45
                return False

        # save
        elif self.screen_width / 2 - 140 <= self.x <= self.screen_width / 2 \
                and self.screen_height - 40 <= self.y <= self.screen_height:
            sc = 50
            # checks if a mouse is clicked
            if clicked:
                sc = 55
                print('Saving...')
                block_map.encode_map_file(map_directory)
                print('Saved!')
        # clear map
        elif self.screen_width / 2 - 70 <= self.x <= self.screen_width / 2 + 70\
                and self.screen_height - 80 <= self.y <= self.screen_height - 40:
            rc = 50
            # checks if a mouse is clicked
            if clicked:
                sc = 55
                block_map.block_data = []

        # draw the buttons to the screen
        # Back button
        pygame.draw.rect(screen, [qc, qc, qc], [self.screen_width / 2, self.screen_height - 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Back', True, (230, 230, 230)),
                    (self.screen_width / 2 + 35, self.screen_height - 40))
        # Save button
        pygame.draw.rect(screen, [sc, sc, sc], [self.screen_width / 2 - 140, self.screen_height - 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Save', True, (230, 230, 230)),
                    (self.screen_width / 2 - 110, self.screen_height - 40))
        # reset button
        pygame.draw.rect(screen, [rc, rc, rc], [self.screen_width / 2 - 70, self.screen_height - 80, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Reset', True, (230, 230, 230)),
                    (self.screen_width / 2 - 45, self.screen_height - 80))
        return True


# detect collisions between the car and the wall
def detect_collision():
    c = None
    for block in block_map.block_data:
        if block.id[:2] == camera.select_block():
            block.update_mask()
            player.update_()
            c = pygame.sprite.collide_mask(block, player)
    if c is None:
        return
    else:
        player.over = True


def find_start_loc():
    if len(block_map.block_data) == 0:
        block_map.block_data.append(RoadPiece([0, 0, 0], Map.ROAD1, 0, 0, 0, Map.BLOCK_SIZE))
    spawn_block = block_map.block_data[0]
    for block in block_map.block_data:
        if not block.id[2] == 0:
            spawn_block = block
            break
    block_size = block_map.BLOCK_SIZE
    block_loc = spawn_block.id[:2]
    return block_loc[1] * block_size + .5 * block_size, block_loc[0] * block_size + .7 * block_size


def restart_player():
    player.__init__()
    agent_status.__init__()


def prepare_network():
    tf.compat.v1.disable_eager_execution()
    lr = 0.00005
    n_actions = 4
    agent = Agent(lr=lr, gamma=0.99, n_actions=n_actions, epsilon=1.0, batch_size=64, input_dims=player.input_num,
                  epsilon_end=0.01, mem_size=1000000)
    return agent


def main_gameloop(load_model):
    # restart the main objects
    global camera, player, agent_status, block_map, map_directory
    camera = Camera()
    player = Player()
    block_map = Map(map_directory)
    agent_status = Reward()

    # create the agent
    agent = prepare_network()

    if load_model:
        agent.load_model()
        agent.epsilon = agent.eps_min
    # variables to store the results of each training
    score_list = []
    episode = 0

    running = True
    while running:
        mouse_button_click = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_button_click.append(event.button)
        clock.tick(90)
        screen.fill((50, 50, 50))

        # gets the next action from the network
        action = agent.choose_action(player.state)

        # reset the reward to 0
        agent_status.reward = 0

        # does the processing to make the car move to the next position
        player.start(action)
        detect_collision()

        # run the reward calculation
        r = agent_status.reward_calc()

        # draws the map
        for item in block_map.block_data:
            item.draw()

        # update the info to be given to the network on the next step. This step must be done directly after the road
        # and nothing else has been drawn to the screen
        player.outputs()

        # store the transition and teach the agent
        agent.store_transition(player.state_prev, action, r,
                               player.state, player.over)

        if not load_model:
            agent.learn()

        # print out the episode results if the player died and restart it
        if player.over:
            score_list.append(agent_status.score)
            avg_score = 0
            episode += 1
            for s in score_list:
                avg_score += s
            avg_score = avg_score / len(score_list)

            # save the model every 100 episodes
            if not load_model:
                if episode % 100 == 0:
                    agent.save_model()
                print(f'Final score: {agent_status.score} Average score: {round(avg_score, 3)} Episode: {episode}')
            # reset the player and reward objects
            restart_player()
            # reset the cameras position
            x, y = camera.return_offset(speed=.9)
            for item in block_map.block_data:
                item.adjust_xy(x, y)
            player.x += x
            player.y += y

        # logic for smooth camera
        x, y = camera.return_offset()
        for item in block_map.block_data:
            item.adjust_xy(x, y)
        player.x += x
        player.y += y

        # draw the rest of the objects
        index = 0
        for line in player.lines:
            index += 1
            if index % 2 == 0:
                pygame.draw.circle(screen, [10, 150, 10], line, 5)

        player.draw()

        # back button detector
        qc = 20
        if size[0] / 2 - 70 <= camera.x <= size[0] / 2 + 70 \
                and size[1] - 40 <= camera.y <= size[1]:
            qc = 40
            # checks if a mouse is clicked
            if mouse_button_click:
                return

        # draw back button
        pygame.draw.rect(screen, [qc, qc, qc], [size[0] / 2 - 70, size[1] - 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Back', True, (230, 230, 230)),
                    (size[0] / 2 - 50, size[1] - 40))

        # updates the display on each new frame
        pygame.display.update()


def main_editorloop():
    # restart the camera and block map
    global block_map, camera
    block_map = Map(map_directory)
    camera = Camera()
    # use the exit check to get the other events for use
    running = True
    while running:
        mouse_button_click = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_button_click.append(event.button)
        clock.tick(144)
        screen.fill((50, 50, 50))

        # logic for moving camera position
        x, y = camera.return_offset(follow_player=False)
        for item in block_map.block_data:
            item.adjust_xy(x, y)

        # draws the map in blocks
        for item in block_map.block_data:
            item.draw()

        # update the editor objects information about the mouse and draw the buttons
        running = editor.ui_buttons(mouse_button_click)
        editor.select_block(mouse_button_click)
        editor.update_mouse_pos()

        pygame.display.update()


# todo add button in the editor to clear the map
# todo add multiple save slots for maps and agents
def main():
    global size, map_directory, block_map
    running = True
    while running:
        mouse_button_click = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_button_click.append(event.button)
        # fill screen for backdrop and init variables
        screen.fill([55, 55, 55])
        c1 = 20
        c2 = 30
        c3 = 20
        c4 = 30
        c5 = 20
        c6 = 30
        c7 = 20
        loop_to_enter = None

        # check if the mouse is overtop any of the buttons and if it is clicked
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # run map 1
        if size[0] / 2 <= mouse_x <= size[0] / 2 + 140 \
                and size[1] / 2 <= mouse_y <= size[1] / 2 + 40:
            c1 = 40
            if mouse_button_click:
                map_directory = 'map1.txt'
                c1 = 45
                loop_to_enter = 1
        # edit map 1
        elif size[0] / 2 - 140 <= mouse_x <= size[0] / 2 \
                and size[1] / 2 <= mouse_y <= size[1] / 2 + 40:
            c2 = 50
            if mouse_button_click:
                map_directory = 'map1.txt'
                c2 = 55
                loop_to_enter = 2
        # run map 2
        if size[0] / 2 <= mouse_x <= size[0] / 2 + 140 \
                and size[1] / 2 + 40 <= mouse_y <= size[1] / 2 + 80:
            c3 = 40
            if mouse_button_click:
                map_directory = 'map2.txt'
                c3 = 45
                loop_to_enter = 1
        # edit map 2
        elif size[0] / 2 - 140 <= mouse_x <= size[0] / 2 \
                and size[1] / 2 + 40 <= mouse_y <= size[1] / 2 + 80:
            c4 = 50
            # checks if a mouse is clicked
            if mouse_button_click:
                map_directory = 'map2.txt'
                c4 = 55
                loop_to_enter = 2


        # quit
        elif size[0] / 2 - 70 <= mouse_x <= size[0] / 2 + 70 \
                and size[1] - 40 <= mouse_y <= size[1]:
            c7 = 40
            # checks if a mouse is clicked
            if mouse_button_click:
                c7 = 45
                running = False

        # draw buttons
        pygame.draw.rect(screen, [c1, c1, c1], [size[0] / 2, size[1] / 2, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Edit map 1', True, (230, 230, 230)),
                    (size[0] / 2 + 10, size[1] / 2))
        pygame.draw.rect(screen, [c2, c2, c2], [size[0] / 2 - 140, size[1] / 2, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Run map 1', True, (230, 230, 230)),
                    (size[0] / 2 - 130, size[1] / 2))
        pygame.draw.rect(screen, [c3, c3, c3], [size[0] / 2, size[1] / 2 + 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Edit map 2', True, (230, 230, 230)),
                    (size[0] / 2 + 10, size[1] / 2 + 40))
        pygame.draw.rect(screen, [c4, c4, c4], [size[0] / 2 - 140, size[1] / 2 + 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Run map 2', True, (230, 230, 230)),
                    (size[0] / 2 - 130, size[1] / 2 + 40))

        pygame.draw.rect(screen, [c7, c7, c7], [size[0] / 2 - 70, size[1] - 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 28).render('Quit', True, (230, 230, 230)),
                    (size[0] / 2 - 50, size[1] - 40))

        if loop_to_enter == 1:
            # call this on click of ui button and variable updates
            block_map = Map(map_directory)
            main_editorloop()

        if loop_to_enter == 2:
            block_map = Map(map_directory)
            main_gameloop(True)

        pygame.display.update()


if __name__ == '__main__':
    block_map = Map(map_directory)
    camera = Camera()
    player = Player()
    agent_status = Reward()
    editor = Editor()
    main()
