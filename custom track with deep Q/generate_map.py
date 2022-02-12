import pygame
import ctypes
import os
import win32api
from Map_Road_Classes import Map, RoadPiece

if __name__ == '__main__':
    # pygame setup
    ctypes.windll.user32.SetProcessDPIAware()
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)
    pygame.init()
    pygame.display.set_caption('Track render')
    clock = pygame.time.Clock()
    # importing block image
    road1 = pygame.image.load('map_pieces/Road_1.png')
    road2 = pygame.image.load('map_pieces/Road_2.png')

    # placeholder map file
    map_directory = 'map_file_example&test'

size = (1920, 1080)
screen = pygame.display.set_mode(size)

# class used to provide x and y offsets from mouse movement to test the camera
class TestCamera:
    def __init__(self):
        self.x, self.y = pygame.mouse.get_pos()
        self.prev_x, self.prev_y = self.x, self.y

    # calculates the offset that should be returned
    def return_offset(self):
        x, y = 0, 0
        self.prev_x, self.prev_y = self.x, self.y
        self.x, self.y = pygame.mouse.get_pos()
        # only return an offset if left mouse button is pressed down
        if pygame.mouse.get_pressed(num_buttons=3)[0] == 1:
            x, y = self.x - self.prev_x, self.y - self.prev_y
            # update the Editor object offsets to properly calculate the block being selected
            editor.movement_offset = editor.movement_offset[0] - x, editor.movement_offset[1] - y
        return x, y


class Editor:
    # importing block images
    ROAD1 = pygame.image.load('map_pieces/Road_1.png')
    ROAD2 = pygame.image.load('map_pieces/Road_2.png')
    BLOCK_SIZE = Map.BLOCK_SIZE

    def __init__(self):
        self.movement_offset = [0, 0]
        self.x, self.y = pygame.mouse.get_pos()
        self.screen_width = 1920
        self.screen_height = 1080

    def update_mouse_pos(self):
        self.x, self.y = pygame.mouse.get_pos()

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
                # get data needed to change the block and edit it : needs to be implemented
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
        qc = 30
        sc = 40
        # check if a click was registered using the mouseevent variable passed from the main function
        clicked = False
        for item in mbe:
            if item == 1:
                clicked = True

        # quit
        if self.screen_width / 2 <= self.x <= self.screen_width / 2 + 140 \
                and self.screen_height - 40 <= self.y <= self.screen_height:
            qc = 35
            # checks if a mouse is clicked
            if clicked:
                qc = 40
                return False

        # save
        elif self.screen_width / 2 - 210 <= self.x <= self.screen_width / 2 \
                and self.screen_height - 40 <= self.y <= self.screen_height:
            sc = 45
            # checks if a mouse is clicked
            if clicked:
                sc = 50
                print('Saving...')
                block_map.encode_map_file()
                print('Saved!')

        # draw the buttons to the screen
        # Quit button
        pygame.draw.rect(screen, [qc, qc, qc], [self.screen_width / 2, self.screen_height - 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 35).render('Quit', True, (230, 230, 230)),
                    (self.screen_width / 2 + 35, self.screen_height - 40))
        # Save button
        pygame.draw.rect(screen, [sc, sc, sc], [self.screen_width / 2 - 140, self.screen_height - 40, 140, 40])
        screen.blit(pygame.font.SysFont('Corbel', 35).render('Save', True, (230, 230, 230)),
                    (self.screen_width / 2 - 110, self.screen_height - 40))
        return True


def main():
    running = True
    while running:

        # use the exit check to get the other events for use
        mouse_button_click = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_button_click.append(event.button)
        clock.tick(144)
        screen.fill((50, 50, 50))

        # logic for moving camera position
        x, y = camera.return_offset()
        for item in block_map.block_data:
            item.adjust_xy(x, y)

        # draws the map in blocks
        for item in block_map.block_data:
            item.draw()

        # update the editor objects information about the mouse and draw the buttons
        editor.ui_buttons(mouse_button_click)
        editor.select_block(mouse_button_click)
        editor.update_mouse_pos()

        # update the screen
        pygame.display.update()


if __name__ == '__main__':
    block_map = Map('map_generator_output')
    camera = TestCamera()
    editor = Editor()
    main()
