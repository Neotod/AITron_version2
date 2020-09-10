from math import sqrt
from ks.models import ECell, EDirection
from time import perf_counter

class Tron:
    def __init__(self):
        self.target_passed_cycles = 0

        self.agent_state = 'normal'
        self.target_pos = ()
        self.agent_prev_pos = ()

        self.walls = {}
        self.walls_neighbors = {}

        self.reaching_path = []

        self.is_opponent_score_low = False
        self.is_opponent_near = False


    def initalize(self):
        self.walls['my'] = {}
        self.walls['opponent'] = {}
        self.walls['empty'] = {}
        self.walls['area'] = {}

    def set_requirements(self, agents, names, scores, board):
        self.agent = agents[names[0]]
        self.opponent = agents[names[1]]

        self.names = names
        self.agent_name = names[0]

        self.scores = scores

        self.board = board

    
    def find_walls_neighbors(self):
        wall_positions = list(self.walls['empty'].keys())
        for position in wall_positions:
            wall_y, wall_x = position[0], position[1]

            range_y1 = wall_y-8
            range_y2 = wall_y+8

            if range_y1 < 1:
                range_y2 += abs(range_y1)
                range_y1 = 1
            elif range_y2 > len(self.board)-2:
                range_y1 -= (range_y2 - (len(self.board)-2))
                range_y2 = len(self.board)-2

            # range_y1, range_y2 = 1, len(self.board)-2

            range_x1 = wall_x-10
            range_x2 = wall_x+10
            
            if range_x1 < 1:
                range_x2 += (abs(range_x1))
                range_x1 = 1
            elif range_x2 > len(self.board[0])-2:
                range_x1 -= (range_x2 - (len(self.board[0])-2))
                range_x2 = len(self.board[0])-2


            self.walls_neighbors[(wall_y, wall_x)] = []
            for i in range(range_y1, range_y2+1):
                for j in range(range_x1, range_x2+1):
                    if self.board[i][j] != ECell.AreaWall:
                        if (i, j) != position:
                            self.walls_neighbors[(wall_y, wall_x)].append((i, j))

    def identify_walls(self, check_awalls: bool):
        if self.agent_name == 'Blue':
            m_wall = ECell.BlueWall
            o_wall = ECell.YellowWall
        elif self.agent_name == 'Yellow':
            m_wall = ECell.YellowWall
            o_wall = ECell.BlueWall


        i_range = range(len(self.board[1:]))
        for i in i_range:
            j_range = range(len(self.board[i][1:]))
            for j in j_range:
                if self.board[i][j] == m_wall:
                    self.walls['my'][(i, j)] = 0

                elif self.board[i][j] == o_wall:
                    self.walls['opponent'][(i, j)] = 0

                elif self.board[i][j] == ECell.Empty:
                    self.walls['empty'][(i, j)] = 0

                elif self.board[i][j] == ECell.AreaWall:
                    if check_awalls:
                        y_steps = [0, 1, -1, 0]
                        x_steps = [1, 0, 0, -1]

                        neighbor_walls = []
                        area_wall_sole = False
                        for m in range(4):
                            y = i + y_steps[m]
                            x = j + x_steps[m]
    
                            if self.board[y][x] != ECell.AreaWall:
                                neighbor_walls.append((x, y))
                                area_wall_sole = True

                        if area_wall_sole:
                            self.walls['area'][(i, j)] = neighbor_walls


    def calc_wall_weight(self):
        wall_types = list(self.walls.keys())[:-1] # all walls except area walls
        for wall_type in wall_types:
            walls = self.walls[wall_type]

            for wall_pos in walls:
                wall_y, wall_x = wall_pos[0], wall_pos[1]

                agent_y, agent_x = self.agent.position.y, self.agent.position.x
                opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

                if (agent_y, agent_x) == (wall_y, wall_x):
                    continue
                if (opponent_y, opponent_x) != (wall_y, wall_x):
                    if self.agent_name == 'Blue':
                        my_wall = ECell.BlueWall
                        opponent_wall = ECell.YellowWall
                    elif self.agent_name == 'Yellow':
                        my_wall = ECell.YellowWall
                        opponent_wall = ECell.BlueWall

                    # calculating distance weight
                    y_side_agent = agent_y - wall_y
                    x_side_agent = agent_x - wall_x
                    agent_distance = sqrt(y_side_agent**2 + x_side_agent **2)

                    y_side_opponent = opponent_y - wall_y
                    x_side_opponent = opponent_x - wall_x
                    opponent_distance = sqrt(y_side_opponent**2 + x_side_opponent **2)

                    agent_d_ratio = opponent_d_ratio = 1
                    if self.agent_state == 'attack':
                        opponent_d_ratio = 3
                        if self.board[wall_y][wall_x] == opponent_wall:
                            agent_d_ratio = 10
                    
                    distance_weight = (agent_distance * agent_d_ratio) + ((1/(opponent_distance)) * opponent_d_ratio)
                    distance_weight *= 10
                    
                    # calculating wall itself weight
                    if self.agent_state == 'normal':
                        if wall_type == 'my':
                            wall_ratio = 10
                        elif wall_type == 'opponent':
                            if self.agent.wall_breaker_cooldown != 0:
                                wall_ratio = 10
                            else:
                                wall_ratio = 5

                        elif wall_type == 'empty':
                            wall_ratio = 1

                    elif self.agent_state == 'attack':
                        if wall_type == 'my':
                            wall_ratio = 10
                        elif wall_type == 'opponent':
                            wall_ratio = 1
                            
                        elif wall_type == 'empty':
                            wall_ratio = 4
                    
                    elif self.agent_state == 'defence':
                        if wall_type == 'my':
                            wall_ratio = 10
                        elif wall_type == 'opponent':
                            if self.agent.wall_breaker_cooldown != 0:
                                wall_ratio = 8
                            else:
                                wall_ratio = 5

                        elif wall_type == 'empty':
                            wall_ratio = 1


                    distance_weight *= wall_ratio

                    # check walls near the current wall
                        
                    y_steps = (0, -1, 1, 0)
                    x_steps = (-1, 0, 0, 1)
                    opponent_walls = my_walls = empty_walls = area_walls = 0
                    
                    for i in range(4):
                        y = wall_y + y_steps[i]
                        x = wall_x + x_steps[i]
                        if self.board[y][x] == ECell.AreaWall:
                            area_walls += 1

                    if area_walls == 2:
                        area_walls = 1

                    if area_walls != 0:
                        center_y, center_x = len(self.board) // 2, len(self.board[0]) // 2 
                        distance_y, distance_x = abs(center_y - wall_y), abs(center_x - wall_x)

                        area_wall_distance = sqrt(distance_y ** 2 + distance_x ** 2)
                        area_walls *= (1/area_wall_distance)


                    range_y1 = (wall_y-3) if (wall_y-3) >= 1 else 1
                    range_y2 = (wall_y+3) if (wall_y+3) <= len(self.board)-2 else len(self.board)-2

                    range_x1 = (wall_x-3) if (wall_x-3) >=1 else 1
                    range_x2 = (wall_x+3) if (wall_x+3) <= len(self.board[0])-2 else len(self.board[0])-2

                    for i in range(range_y1, range_y2+1):
                        for j in range(range_x1, range_x2+1):
                            if self.board[i][j] == opponent_wall:
                                opponent_walls += 1
                            elif self.board[i][j] == my_wall:
                                my_walls += 1
                            elif self.board[i][j] == ECell.Empty:
                                empty_walls += 1


                    if self.agent_state == 'normal':
                        ratios = [5, 15, -1, -80]
                    elif self.agent_state == 'attack':
                        ratios = [-2, 15, -1, -60]
                        if self.board[wall_y][wall_x] == opponent_wall:
                            ratios[0] += 1.5
                            ratios[2] -= 1
                            ratios[3] += 25  

                    else:
                        ratios = [20, 25, -1, -40]

                    distance_weight += (distance_weight*((opponent_walls * ratios[0])/100))
                    distance_weight += (distance_weight*((my_walls * ratios[1])/100))
                    distance_weight += (distance_weight*((empty_walls * ratios[2])/100))
                    distance_weight += (distance_weight*((area_walls * ratios[3])/100))
                    
                    weight = distance_weight
                    
                else:
                    weight = 900

                self.walls[wall_type][wall_pos] = int(weight)


    def update_state(self):
        prev_state = self.agent_state

        agent_y, agent_x = self.agent.position.y, self.agent.position.x
        opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

        y_side = opponent_y - agent_y
        x_side = opponent_x - agent_x
        distance = round(sqrt(y_side**2 + x_side **2))

        my_score, opponent_score = self.scores[self.names[0]], self.scores[self.names[1]]

        self.is_opponent_near = False
        if distance <= 4:
            self.is_opponent_near = True
            if my_score <= opponent_score:
                self.agent_state = 'defence'
            
        elif distance > 5:
            self.is_opponent_near = False
            self.agent_state = 'normal'

            if self.agent.wall_breaker_cooldown == 0:
                if my_score > opponent_score + 5:
                    self.is_opponent_score_low = True
                    self.agent_state = 'attack'
                elif my_score < opponent_score:
                    self.is_opponent_score_low = False
                    self.agent_state = 'attack'

        # emergencies
        if self.agent_state == 'attack':
            if self.agent.wall_breaker_rem_time == 2:
                self.agent_state = 'normal'

        if distance <= 3:
            if my_score < opponent_score:
                self.agent_state = 'normal'
                
                
        if prev_state != self.agent_state:
            self.find_target()

    
    def get_wall_type(self, wall_pos):
        if self.agent_name == 'Blue':
            my_wall = ECell.BlueWall
            opponent_wall = ECell.YellowWall
        elif self.agent_name == 'Yellow':
            my_wall = ECell.YellowWall
            opponent_wall = ECell.BlueWall

        pos_y, pos_x = wall_pos[0], wall_pos[1]
        if self.board[pos_y][pos_x] == my_wall:
            return 'my'
        elif self.board[pos_y][pos_x] == opponent_wall:
            return 'opponent'
        elif self.board[pos_y][pos_x] == ECell.Empty:
            return 'empty'
        elif self.board[pos_y][pos_x] == ECell.AreaWall:
            return 'area'
        
    
    def find_best_wall(self, walls):
        if self.agent_state == 'normal':
            # filter 1
            walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]

            min_weight = min(walls_weights)
            
            filter1_qualifieds = []
            for i in range(len(walls)):
                weight = walls_weights[i]
                diff = abs(weight - min_weight)

                if 0 <= diff and diff <= 10:
                    wall_pos = walls[i]
                    filter1_qualifieds.append(wall_pos)

            print('filter1: ', filter1_qualifieds)

            
            walls_distance = []
            area_walls_pos = self.walls['area']
            for wall_pos in filter1_qualifieds:
                distances = []
                for awall_pos in area_walls_pos:
                    distance_y = abs(wall_pos[0] - awall_pos[0])
                    distance_x = abs(wall_pos[1] - awall_pos[1])

                    distance = int(sqrt(distance_y**2 + distance_x**2)*1000)
                    distances.append(distance)
                
                
                min_distance = min(distances)
                index = distances.index(min_distance)
                closest_awall_pos = list(area_walls_pos.keys())[index]

                distance_y = abs(wall_pos[0] - closest_awall_pos[0])
                distance_x = abs(wall_pos[1] - closest_awall_pos[1])

                distance = sqrt(distance_y**2 + distance_x**2)
                walls_distance.append(distance)

            min_wall_distance = min(walls_distance)
            wall_index = walls_distance.index(min_wall_distance)

            print('\n\n')

            return filter1_qualifieds[wall_index]
        
        elif self.agent_state == 'attack':
            walls = list(walls.keys())
            walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
            min_weight = min(walls_weights)
            
            filter1_qualifieds = []
            for i in range(len(walls)):
                weight = walls_weights[i]
                diff = abs(weight - min_weight)

                if 0 <= diff and diff <= 100:
                    wall_pos = walls[i]
                    filter1_qualifieds.append(wall_pos)

            print('filter1: ', filter1_qualifieds)
            if len(filter1_qualifieds) == 1:
                return filter1_qualifieds[0]

            # filter 2
            agent_pos = (self.agent.position.y, self.agent.position.x)

            distances = []
            for wall_pos in filter1_qualifieds:

                distance_y, distance_x = abs(wall_pos[0] - agent_pos[0]), abs(wall_pos[1] - agent_pos[1])
                distance = sqrt(distance_y**2 + distance_x**2)
                distances.append(distance)

            min_distance, index = 100000, 0
            for i in range(len(filter1_qualifieds)):
                distance = distances[i]
                if distance < min_distance:
                    index = i
                    min_distance = distance

            return filter1_qualifieds[index]

    def find_target(self):
        if self.agent_state == 'normal':
            agent_y, agent_x = self.agent.position.y, self.agent.position.x
            curr_wall_neighbors = self.walls_neighbors[(agent_y, agent_x)]

            wall_pos = self.find_best_wall(curr_wall_neighbors)

        elif self.agent_state == 'attack':
            if self.is_opponent_score_low:
                opponent_pos = (self.opponent.position.y, self.opponent.position.x)
                wall_pos = opponent_pos

            elif self.is_opponent_near == False:
                opponent_walls = self.walls['opponent']

                wall_pos = self.find_best_wall(opponent_walls)

        elif self.agent_state == 'defence':
            opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

            range_y1 = opponent_y-4
            range_y2 = opponent_y+4
            if range_y1 <= 1:
                range_y1 = 1
                range_y2 = 8
            elif range_y2 >= len(self.board)-2:
                range_y1 = len(self.board) - 7
                range_y2 = len(self.board)
                
            range_y = range(range_y1, range_y2+1)
            
            range_x1 = opponent_x-4
            range_x2 = opponent_x+4
            if range_x1 <= 1:
                range_x1 = 1
                range_x2 = 8
            elif range_x2 >= len(self.board[0])-2:
                range_x1 = len(self.board[0]) - 9
                range_x2 = len(self.board[0])

            range_x = range(range_x1, range_x2+1)

            agent_y, agent_x = self.agent.position.y, self.agent.position.x
            curr_wall_neighbors = self.walls_neighbors[(agent_y, agent_x)]

            qual_neighbor_walls = [position for position in curr_wall_neighbors if position[0] not in range_y and position[1] not in range_x]

            neighbors_weights = [self.get_wall_weight(position) for position in qual_neighbor_walls]
            
            show_walls = {}
            for i in range(len(qual_neighbor_walls)):
                pos = qual_neighbor_walls[i]
                weight = neighbors_weights[i]
                show_walls[pos] = weight


            min_weight = min(neighbors_weights)
            weight_index = neighbors_weights.index(min_weight)
            neighbor_pos = qual_neighbor_walls[weight_index]
            
            wall_pos = neighbor_pos

        print('targes changed')
        self.target_passed_cycles = 0
        self.target_pos = wall_pos

    def find_heuristics(self, start_pos, dest_pos):
        start_y, end_y = min(start_pos[0], dest_pos[0])-10, max(start_pos[0], dest_pos[0])+10
        start_x, end_x = min(start_pos[1], dest_pos[1])-10, max(start_pos[1], dest_pos[1])+10

        start_y = 1 if start_y < 1 else start_y
        end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y

        start_x = 1 if start_x < 1 else start_x
        end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x

        heuristics = {}
        for i in range(start_y, end_y+1):
            for j in range(start_x, end_x+1):
                if self.board[i][j] != ECell.AreaWall:
                    distance = abs(i - dest_pos[0]) + abs(j - dest_pos[1])
                    heuristics[(i, j)] = distance

        return heuristics
        
    def find_costs(self, start_pos, dest_pos):
        start_y, end_y = min(start_pos[0], dest_pos[0])-10, max(start_pos[0], dest_pos[0])+10
        start_x, end_x = min(start_pos[1], dest_pos[1])-10, max(start_pos[1], dest_pos[1])+10

        start_y = 1 if start_y < 1 else start_y
        end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y

        start_x = 1 if start_x < 1 else start_x
        end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x

        costs = {}
        for i in range(start_y, end_y+1):
            for j in range(start_x, end_x+1):
                if self.board[i][j] != ECell.AreaWall:
                    for wall_type in list(self.walls.keys())[:-1]:
                        positions = self.walls[wall_type]
                        position = (i, j)
                        if position in positions:
                            costs[(i, j)] = self.walls[wall_type][position]


            for wall_pos in costs:
                y, x = wall_pos[0], wall_pos[1]

                if self.agent_name == 'Blue':
                    m_wall = ECell.BlueWall
                    o_wall = ECell.YellowWall
                elif self.agent_name == 'Yellow':
                    m_wall = ECell.YellowWall
                    o_wall = ECell.BlueWall

                wall_cost = costs[wall_pos]

                if self.agent.wall_breaker_cooldown != 0:
                    if self.board[y][x] == o_wall or self.board[y][x] == m_wall:
                        wall_cost += (wall_cost * 20/100)
                        costs[wall_pos] = int(wall_cost)

                if self.board[y][x] == m_wall:
                    wall_cost += (wall_cost * 60/100)
                    costs[wall_pos] = int(wall_cost)

                if self.agent_state == 'attack':
                    if self.board[y][x] == o_wall:
                        if self.agent.wall_breaker_rem_time < 6:
                            wall_cost -= (wall_cost * 30/100)
                        else:
                            wall_cost -= (wall_cost * 10/100)
                        costs[wall_pos] = int(wall_cost)

                if wall_cost < 0:
                    print(f'there is a negative cost here: {wall_pos} | {wall_cost}')

        return costs

    def find_best_route(self, start_pos, dest_pos):
        start_y, end_y = min(start_pos[0], dest_pos[0])-10, max(start_pos[0], dest_pos[0])+10
        start_x, end_x = min(start_pos[1], dest_pos[1])-10, max(start_pos[1], dest_pos[1])+10

        start_y = 1 if start_y < 1 else start_y
        end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y
        
        start_x = 1 if start_x < 1 else start_x
        end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x


        heuristics = self.find_heuristics(start_pos, dest_pos)
        costs = self.find_costs(start_pos, dest_pos)

        i, j = start_pos[0], start_pos[1]
        
        open_vertices = {(i, j): [0, []]}
        visited_vertices = {}
        
        cost_so_far = 0
        while True:
            next_node, min_f = (0, 0), 10000000
            for node, value in open_vertices.items():
                f = value[0]
                if f < min_f:
                    next_node = node
                    min_f = f
                elif f == min_f:
                    node_h = heuristics[node]
                    min_node_h = heuristics[next_node]
                    if node_h < min_node_h:
                        next_node = node
                        min_f = f

            current_node = next_node
            came_from = open_vertices[current_node][1]
                    
            cost_so_far = 0
            for node in came_from:
                cost_so_far += costs[node]

            open_vertices.pop(current_node)

            i, j = current_node[0], current_node[1]
            neighbors = {}
            y_steps = [0, -1, 1, 0]
            x_steps = [1, 0, 0, -1]
            for l in range(4):
                ii = i + y_steps[l]
                jj = j + x_steps[l]
                
                if ii < start_y or ii > end_y or jj < start_x or jj > end_x:
                    continue
                if self.board[ii][jj] == ECell.AreaWall:
                    continue
                if (ii, jj) == self.agent_prev_pos:
                    continue

                opponent_pos = (self.opponent.position.y, self.opponent.position.x)
                if (ii, jj) == opponent_pos:
                    continue


                node = (ii, jj)
                g = costs[node] + cost_so_far
                f = heuristics[node] + g
                
                neighbor_came_from = came_from.copy()
                neighbor_came_from.append(current_node)
                neighbors[node] = [f, neighbor_came_from]


            next_neighbors = []
            for node, value in neighbors.items():
                f = value[0]
                if node == dest_pos:
                    path = came_from
                    path.append(current_node)
                    path.append(node)

                    self.reaching_path = path
                    return

                if node in list(open_vertices.keys()):
                    visited_f = open_vertices[node][0]
                    if f > visited_f:
                        continue
                    elif f < visited_f:
                        node_value = open_vertices[node].copy()
                        del open_vertices[node]
                        open_vertices[node] = node_value

                elif node in list(visited_vertices.keys()):
                    visited_f = visited_vertices[node][0]
                    if f > visited_f:
                        continue
                else:
                    open_vertices[node] = neighbors[node].copy()

            g = cost_so_far + costs[current_node]
            f = heuristics[current_node] + g
            visited_vertices[current_node] = [f, came_from]
    
    def get_wall_weight(self, wall_pos):
        return self.walls[self.get_wall_type(wall_pos)][wall_pos]

    def is_target_cycles_exceeded(self):
        self.target_passed_cycles += 1
        if self.target_passed_cycles > 10:
            return True
        else:
            return False


    def is_target_reached(self):
        agent_pos = (self.agent.position.y, self.agent.position.x)
        if agent_pos == self.target_pos:
            return True
        else:
            return False

    def is_wallbreaker_needed(self):
        i, j = self.reaching_path[1][0], self.reaching_path[1][1]
            
        if self.board[i][j] != ECell.Empty:
            return True
        else:
            return False
            
        
    def show_banner(self):
        welcome_banner = [
            ['\n'],
            ['''
                                                    ·▪      ▄▄ 
             ▄▄·        ▌ ▐·▪  ·▄▄▄▄        ▪█▀   █ ▀████▪· █    █
            ▐█ ▌▪▪     ▪█·█▌██ ██▪ ██        ██ ·▪█  ██  █▌ ██ ·▪█
            ██ ▄▄ ▄█▀▄ ▐█▐█•▐█·▐█· ▐█▌·▪███▀  █████  ██  ██  █████
            ▐███▌▐█▌.▐▌ ███ ▐█▌██. ██            ██  ██· ██·    ██
            ·▀▀▀  ▀█▄▀▪. ▀  ▀▀▀▀▀▀▀▀•         ·▪▐██▀· ████▌· ·▪▐██▀▪▪
            '''],
            ['\n']
        ]
        for line in welcome_banner:
            print(line[0])
            
    def next_dir(self):
        agent_pos = (self.agent.position.y, self.agent.position.x)
        self.agent_prev_pos = agent_pos

        next_dir = EDirection.Right
        index = 1

        
        if agent_pos[0] == self.reaching_path[index][0]:
            if self.reaching_path[index][1] - agent_pos[1] == 1:
                next_dir = EDirection.Right
            else:
                next_dir = EDirection.Left
        else:
            if self.reaching_path[index][0] - agent_pos[0] == 1:
                next_dir = EDirection.Down
            else:
                next_dir = EDirection.Up

        return next_dir


    def show_walls_info(self):        
        print('{:<5}'.format('*'), end='')
        for i in range(len(self.board[0])):
            print('{:<5}'.format(i), end='')
        print()
        for i in range(len(self.board)):
            print('{:<3}  '.format(i), end='')
            for j in range(len(self.board[i])):
                if i == 0 or i == len(self.board)-1:
                    print('{:<5}'.format('====='), end='')
                elif j == 0 or j == len(self.board[i])-1:
                    print('{:<5}'.format('||'), end='')
                else:
                    agent_pos = (self.agent.position.y, self.agent.position.x)
                    opponent_pos = (self.opponent.position.y, self.opponent.position.x)
                    if (i, j) == agent_pos:
                        print('{:<5}'.format('M'), end='')
                    elif (i, j) == opponent_pos:
                        print('{:<5}'.format('O'), end='')
                    elif (i, j) == self.target_pos:
                        print('{:<5}'.format('T'), end='')
                    elif self.board[i][j] == ECell.AreaWall:
                        print('{:<5}'.format('+'), end='')
                    else:
                        wall_weight = self.get_wall_weight((i, j))
                        print('{:<5}'.format(wall_weight), end='')

            print()
        
        print('\n\n')
                    