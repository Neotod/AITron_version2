from ks.models import ECell, EDirection
from math import sqrt

def set_walls(self):
    self.walls['my'] = []
    self.walls['opponent'] = []
    self.walls['empty'] = []
    self.walls['side_area'] = []
    self.walls['mid_area'] = []

def set_requirements(self, agents, names, scores, board, curr_cycle, crash_score):
    self.agent = agents[names[0]]
    self.opponent = agents[names[1]]

    self.names = names
    self.agent_name = names[0]

    self.scores = scores

    self.board = board

    self.curr_cycle = curr_cycle
    self.area_wall_crash_score = crash_score
    self.agent_pos = (self.agent.position.y, self.agent.position.x)

def find_walls_neighbors(self):
    wall_positions = self.walls['empty'].copy()
    for wall_pos in wall_positions:
        self.walls_neighbors[wall_pos] = {}
        self.walls_awall_neighbors[wall_pos] = {}
        val = 1
        while val < 6:
            awall_neighbors = []
            neighbors = []
            pos_1 = (wall_pos[0]-val, wall_pos[1]-val)
            pos_2 = (wall_pos[0]+val, wall_pos[1]+val)

            check_points = [
                    (pos_1[0], pos_1[1]),
                    (pos_1[0], pos_2[1]),
                    (pos_2[0], pos_2[1]),
                    (pos_2[0], pos_1[1]),
                    (pos_1[0], pos_1[1])
            ]

            itr = 1
            i = check_points[0][0]
            j = check_points[0][1]

            if (i < 1 or i > len(self.board)-2 or j < 1 or j > len(self.board[0])) == False:
                if self.board[i][j] != ECell.AreaWall:
                    neighbors.append((i, j))
                else:
                    awall_neighbors.append((i, j))

            i_steps = (0, 1, 0, -1)
            j_steps = (1, 0, -1, 0)
            l = 0
            while itr <= 4:
                i += i_steps[l]
                j += j_steps[l]

                wall_valid = True
                if i < 1 or i > len(self.board)-2 or j < 1 or j > len(self.board[0])-2:
                    wall_valid = False

                if wall_valid:
                    if self.board[i][j] != ECell.AreaWall:
                        if(i, j) not in neighbors and (i, j) != wall_pos:
                            neighbors.append((i, j))
                    else:
                        if(i, j) not in awall_neighbors and (i, j) != wall_pos:
                            awall_neighbors.append((i, j))

                if (i, j) == check_points[itr]:
                    i = check_points[itr][0]
                    j = check_points[itr][1]

                    itr += 1
                    l += 1
                    continue

            self.walls_neighbors[wall_pos][val] = neighbors
            self.walls_awall_neighbors[wall_pos][val] = awall_neighbors
            val += 1

def find_closest_area_wall(self):
    area_walls_pos = self.walls['mid_area'] + self.walls['side_area']

    wall_types = list(self.walls.keys())[:-2].copy()
    for wall_type in wall_types:
        walls = self.walls[wall_type].copy()

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

            self.walls_closest_awall[wall_pos] = closest_awall_pos