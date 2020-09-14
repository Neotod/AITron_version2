from ks.models import ECell, EDirection
from math import sqrt

def set_walls(self):
    self.walls['my'] = {}
    self.walls['opponent'] = {}
    self.walls['empty'] = {}
    self.walls['side_area'] = []
    self.walls['mid_area'] = []

def set_requirements(self, agents, names, scores, board, curr_cycle):
    self.agent = agents[names[0]]
    self.opponent = agents[names[1]]

    self.names = names
    self.agent_name = names[0]

    self.scores = scores

    self.board = board

    self.curr_cycle = curr_cycle

def find_walls_neighbors(self):
    wall_positions = list(self.walls['empty'].keys())
    for position in wall_positions:
        wall_y, wall_x = position[0], position[1]

        range_y1 = wall_y-5
        range_y2 = wall_y+5

        
        if range_y1 < 1:
            range_y1 = 1
        elif range_y2 > len(self.board)-2:
            range_y2 = len(self.board)-2

        range_x1 = wall_x-8
        range_x2 = wall_x+8
        if range_x1 < 1:
            range_x1 = 1
        elif range_x2 > len(self.board[0])-2:
            range_x2 = len(self.board[0])-2


        self.walls_neighbors[(wall_y, wall_x)] = []
        for i in range(range_y1, range_y2+1):
            for j in range(range_x1, range_x2+1):
                if self.board[i][j] != ECell.AreaWall:
                    if (i, j) != position:
                        self.walls_neighbors[(wall_y, wall_x)].append((i, j))

def find_closest_area_wall(self):
    area_walls_pos = self.walls['mid_area'] + self.walls['side_area']

    wall_types = list(self.walls.keys())[:-2].copy()
    for wall_type in wall_types:
        walls = list(self.walls[wall_type].keys()).copy()

        for wall_pos in walls:
            # distance from the closest area wall from the wall
            distances = []
            for awall_pos in area_walls_pos:
                distance_y = abs(wall_pos[0] - awall_pos[0])
                distance_x = abs(wall_pos[1] - awall_pos[1])

                distance = round((sqrt(distance_y**2 + distance_x**2))*10)
                distances.append(distance)
            
            min_distance = min(distances)
            index = distances.index(min_distance)
            closest_awall_pos = area_walls_pos[index]

            self.walls_closest_awalls[wall_pos] = closest_awall_pos