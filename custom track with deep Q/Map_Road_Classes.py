# Map class for storing, encoding, and decoding map objects
# Road class to hold individual block data and do processing on it to be displayed by pygame

# import necessary modules and do setup
import pygame

size = (1920, 1080)
screen = pygame.display.set_mode(size)


# unpacks the map file and holds data about the map
class Map:
    # importing block images
    ROAD1 = pygame.image.load('map_pieces/Road_1.png')
    ROAD2 = pygame.image.load('map_pieces/Road_2.png')
    BLOCK_SIZE = 400

    def __init__(self, map_file):
        temp_map = self.decode_map_file(map_file)
        self.block_data = self.define_road(temp_map)

    # function to decode the map file in to a list of lists of lists
    def decode_map_file(self, file):
        with open(file, 'r') as f:
            lines = f.readlines()
            temp_lines = []
            for x, line in enumerate(lines):
                line = line.replace('\n', '')
                line = line[:-1]
                line_list = line.split()
                if line_list[0] == '#':
                    lines.pop(x)
                else:
                    temp_lines.append(line)
            f.close()
        full_map = []
        for line in temp_lines:
            line = line.split('/')
            placeholder_line = []
            for item in line:
                item = item.split(',')
                item[0], item[1] = int(item[0]), int(item[1])
                placeholder_line.append(item)
            full_map.append(placeholder_line)

        return full_map

    # Encodes the map file to save to for later uses (uses the list of road objects)
    # TODO add way to get rid of any extra columns in front of actual data
    def encode_map_file(self, map_directory):
        row = 0
        column = 0
        min_row = 0
        min_column = 0
        for block in self.block_data:
            if block.id[0] > row:
                row = block.id[0]
            if block.id[1] > column:
                column = block.id[1]
            if block.id[0] < min_row:
                min_row = block.id[0]
            if block.id[1] < min_column:
                min_column = block.id[1]
        encoded_map = ''
        for r in range(min_row, row + 1):
            any_block_data = False
            row_data = ''
            for c in range(min_column, column + 1):
                block_to_add = [0, 0]
                # find the block in the corresponding position to row and column
                for block in self.block_data:
                    if block.id[:2] == [r, c]:
                        any_block_data = True
                        block_to_add = block.id
                        block_to_add = block_to_add[2:]
                        block_to_add.append(block.angle)
                row_data += f'{block_to_add[0]},{block_to_add[1]}/'
                # add the row to the main string
            if any_block_data:
                encoded_map += row_data + '\n'
        print(encoded_map)
        with open(map_directory, 'w') as t:
            t.write(encoded_map)
            t.close()

    # function that takes the list of values from decoding the map file and returns a list of RoadPiece objects
    def define_road(self, values):
        row_ = 0
        road_piece_list = []
        for row in values:
            column = 0
            for block in row:
                if block[0] == 1:
                    x, y = self.getxy(Map.BLOCK_SIZE, row_, column)
                    road_piece_list.append(RoadPiece([row_, column, 1], Map.ROAD1, block[1], x, y, Map.BLOCK_SIZE))
                elif block[0] == 2:
                    x, y = self.getxy(Map.BLOCK_SIZE, row_, column)
                    road_piece_list.append(RoadPiece([row_, column, 2], Map.ROAD2, block[1], x, y, Map.BLOCK_SIZE))
                column += 1
            row_ += 1

        return road_piece_list

    # calculates the x and y values for a given block
    def getxy(self, b, r, c):
        y = b * r
        x = b * c
        return x, y


# class that holds defines a block and provides all the necessary functions to interact with them
class RoadPiece:
    def __init__(self, id, image, angle, x, y, size_, start_road=False):
        self.start_road = start_road
        self.image_non_rotated = image
        self.image = None
        self.image_size = size_
        self.angle = angle
        self.x = x
        self.y = y
        self.rect = None
        self.mask = None
        self.format_image()
        # id is in the format [row, column, block type]
        self.id = id

    # rotate the original block image and set the image to draw to the rotated version
    def rotate_block(self, angle=90):
        self.angle += angle
        if self.angle == 360:
            self.angle = 0

    def change_type(self):
        if self.id[2] == 1:
            self.id[2] = 2
            self.image_non_rotated = Map.ROAD2
        else:
            return True

    # scales and rotates the image according to the blocks data
    def format_image(self):
        self.image = pygame.transform.scale(self.image_non_rotated, (self.image_size, self.image_size))
        self.image = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)
        self.mask.invert()

    def update_mask(self):
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)
        self.mask.invert()

    # draws the block to the screen
    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    # changes the blocks x and y when given a offset value. Used to control the camera
    def adjust_xy(self, x_dif, y_dif):
        self.x += x_dif
        self.y += y_dif
