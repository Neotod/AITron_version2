from math import sqrt
from ks.models import ECell, EDirection
from time import perf_counter
from random import choice


class Tron:
    def __init__(self):
        self.target_passed_cycles = 0
        self.opponent_distance = 0

        self.agent_state = 'normal'
        self.target_pos = ()
        self.agent_prev_pos = ()

        self.walls = {}
        self.walls_neighbors = {}
        self.walls_closest_awalls = {}

        self.reaching_path = []

    def initalize(self):
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

    def identify_walls(self, check_awalls: bool):
        if self.agent_name == 'Blue':
            m_wall = ECell.BlueWall
            o_wall = ECell.YellowWall
        elif self.agent_name == 'Yellow':
            m_wall = ECell.YellowWall
            o_wall = ECell.BlueWall


        i_range = range(len(self.board))
        for i in i_range:
            j_range = range(len(self.board[i]))
            for j in j_range:
                if self.board[i][j] == m_wall:
                    self.walls['my'][(i, j)] = {}

                elif self.board[i][j] == o_wall:
                    self.walls['opponent'][(i, j)] = {}

                elif self.board[i][j] == ECell.Empty:
                    self.walls['empty'][(i, j)] = {}

                elif self.board[i][j] == ECell.AreaWall:
                    if check_awalls:
                        if i == 0 or i == (len(self.board)-1) or j == 0 or j == (len(self.board[0])-1):
                            self.walls['side_area'].append((i, j))

                        else:
                            y_steps = [0, 1, -1, 0]
                            x_steps = [1, 0, 0, -1]

                            area_wall_sole = False
                            for m in range(4):
                                y = i + y_steps[m]
                                x = j + x_steps[m]
        
                                if self.board[y][x] != ECell.AreaWall:
                                    area_wall_sole = True

                            if area_wall_sole:
                                self.walls['mid_area'].append((i, j))

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

    def find_walls_info(self):
        wall_types = list(self.walls.keys())[:-2] # all walls except area walls
        for wall_type in wall_types:
            walls = list(self.walls[wall_type].keys()).copy()

            for wall_pos in walls:
                wall_info = {}
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
                    y_distance_agent = agent_y - wall_y
                    x_distance_agent = agent_x - wall_x
                    agent_distance = sqrt(y_distance_agent**2 + x_distance_agent **2)

                    y_distance_opponent = opponent_y - wall_y
                    x_distance_opponent = opponent_x - wall_x
                    opponent_distance = sqrt(y_distance_opponent**2 + x_distance_opponent **2)


                    wall_info['agent_d'] = agent_distance
                    wall_info['opponent_d'] = opponent_distance


                    # check walls near the current wall
                    opponent_walls = my_walls = empty_walls = area_walls = 0

                    y_steps = (0, -1, 1, 0)
                    x_steps = (-1, 0, 0, 1)
                    for i in range(4):
                        y = wall_y + y_steps[i]
                        x = wall_x + x_steps[i]
                        if self.board[y][x] == ECell.AreaWall:
                            area_walls += 1
                    
                    if area_walls == 2:
                        if ((wall_y == 1 and wall_x == 1) or (wall_y == 1 and wall_x == len(self.board[0])-2) or 
                            (wall_y == len(self.board)-2 and wall_x == 1) or (wall_y == len(self.board)-2 and wall_x == len(self.board[0])-2)):
                            area_walls = 1

                    range_y1 = (wall_y-4) if (wall_y-4) >= 1 else 1
                    range_y2 = (wall_y+4) if (wall_y+4) <= len(self.board)-2 else len(self.board)-2
                    range_y = range(range_y1, range_y2+1)

                    range_x1 = (wall_x-4) if (wall_x-4) >=1 else 1
                    range_x2 = (wall_x+4) if (wall_x+4) <= len(self.board[0])-2 else len(self.board[0])-2
                    range_x = range(range_x1, range_x2+1)

                    for i in range_y:
                        for j in range_x:
                            if self.board[i][j] == opponent_wall:
                                opponent_walls += 1
                            elif self.board[i][j] == my_wall:
                                my_walls += 1
                            elif self.board[i][j] == ECell.Empty:
                                empty_walls += 1

                    wall_info['nears'] = (opponent_walls, my_walls, empty_walls, area_walls)

                self.walls[wall_type][wall_pos] = wall_info
        
    def get_wall_weight(self, wall_pos):
        wall_y, wall_x = wall_pos[0], wall_pos[1]

        agent_y, agent_x = self.agent.position.y, self.agent.position.x
        opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

        if (agent_y, agent_x) == (wall_y, wall_x):
            return 100000
        if (opponent_y, opponent_x) != (wall_y, wall_x):
            wall_type = self.get_wall_type(wall_pos)
            wall_info = self.walls[wall_type][wall_pos]

            if self.agent_name == 'Blue':
                my_wall = ECell.BlueWall
                opponent_wall = ECell.YellowWall
            elif self.agent_name == 'Yellow':
                my_wall = ECell.YellowWall
                opponent_wall = ECell.BlueWall

            # calculating distance weight
            agent_distance = wall_info['agent_d']
            opponent_distance = wall_info['opponent_d']
            
            agent_d_ratio = opponent_d_ratio = 1
            distance_weight = (agent_distance * agent_d_ratio) + ((1/(opponent_distance)) * opponent_d_ratio)
            distance_weight *= 25
            distance_weight = round(distance_weight)


            closest_awall_pos = self.walls_closest_awalls[wall_pos]

            distance_y = abs(wall_pos[0] - closest_awall_pos[0])
            distance_x = abs(wall_pos[1] - closest_awall_pos[1])

            awall_distance = round(sqrt(distance_y**2 + distance_x**2)*10)
            distance_weight = distance_weight*(1+(awall_distance/100))


            weight = distance_weight


            wall_ratio = 1
            # calculating wall itself weight
            if self.agent_state == 'normal':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    if self.agent.wall_breaker_cooldown != 0:
                        wall_ratio = 3
                    else:
                        wall_ratio = 1

                elif wall_type == 'empty':
                    wall_ratio = 1

            elif self.agent_state == 'attack' or self.agent_state == 'brutal':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    wall_ratio = 1
                    
                elif wall_type == 'empty':
                    wall_ratio = 1
            
            elif self.agent_state == 'defence':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    if self.agent.wall_breaker_cooldown != 0:
                        wall_ratio = 7
                    else:
                        wall_ratio = 4

                elif wall_type == 'empty':
                    wall_ratio = 1

            weight *= wall_ratio


            # check walls near the current wall
            near_walls = wall_info['nears']
            opponent_walls = near_walls[0]
            my_walls = near_walls[1]
            empty_walls = near_walls[2]
            area_walls = near_walls[3]

            if self.agent_state == 'normal':
                ratios = [5, 10, -0.5, -30]
                if self.board[wall_y][wall_x] == ECell.Empty:
                    ratios[1] += -10

            elif self.agent_state == 'attack' or self.agent_state == 'brutal':
                ratios = [-2, 10, -0.5, -10]
                if self.get_wall_type(wall_pos) == 'opponent':
                    ratios[2] += -0.2
            elif self.agent_state == 'defence':
                ratios = [7, 10, -0.5, 0]
                if self.board[wall_y][wall_x] == ECell.Empty:
                    ratios[1] += -10


            weight += (weight*((opponent_walls * ratios[0])/100))
            weight += (weight*((my_walls * ratios[1])/100))
            weight += (weight*((empty_walls * ratios[2])/100))
            weight += (weight*((area_walls * ratios[3])/100))


            # a different situation
            if (self.agent_state == 'attack' or self.agent_state == 'brutal') and self.board[wall_y][wall_x] == opponent_wall:
                my_walls = opponent_walls = empty_walls = area_walls = 0
                y_steps = [1, 0, 0, -1]
                x_steps = [0, 1, -1, 0]
                for i in range(4):
                    y = wall_y + y_steps[i]
                    x = wall_x + x_steps[i]

                    if self.board[y][x] == my_wall:
                        my_walls += 1
                    elif self.board[y][x] == opponent_wall:
                        opponent_walls += 1
                    elif self.board[y][x] == ECell.Empty:
                        empty_walls += 1
                    elif self.board[y][x] == ECell.AreaWall:
                        area_walls += 1
                
                attack_ratios = (20, -10, -5, -2)

                weight += (weight*((my_walls * attack_ratios[0])/100))
                weight += (weight*((opponent_walls * attack_ratios[1])/100))
                weight += (weight*((empty_walls * attack_ratios[2])/100))
                weight += (weight*((area_walls * attack_ratios[3])/100))
            
        else:
            weight = 10000

        return round(weight)

    def update_state(self):
        prev_state = self.agent_state

        agent_y, agent_x = self.agent.position.y, self.agent.position.x
        opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

        y_side = opponent_y - agent_y
        x_side = opponent_x - agent_x
        distance = round(sqrt(y_side**2 + x_side **2))
        self.opponent_distance = distance

        my_score, opponent_score = self.scores[self.names[0]], self.scores[self.names[1]]

        if self.opponent_distance <= 4:
            if my_score <= opponent_score:
                self.agent_state = 'defence'

            elif my_score > opponent_score + 3:
                if self.opponent_distance <= 2:
                    self.agent_state = 'brutal'
                    
            
        elif self.opponent_distance > 5:
            self.agent_state = 'normal'

            if self.agent.wall_breaker_cooldown == 0:
                if my_score > opponent_score + 10:
                    self.agent_state = 'brutal'
                    
                elif my_score < opponent_score:
                    self.agent_state = 'attack'
                
                elif my_score == opponent_score and self.curr_cycle >= 10:
                    self.agent_state = 'attack'


        # emergencies
        if self.agent.wall_breaker_rem_time > 1:
            self.agent_state = 'attack'

        elif self.agent.wall_breaker_rem_time == 1:
            self.agent_state = 'normal'

        if self.agent_state == 'defence':
            if distance <= 2:
                self.find_target()
                
        print('state: ', self.agent_state)
        if prev_state != self.agent_state:
            self.find_target()

    def give_best_route(self, routes):
        opponent_walls = my_walls = empty_walls = 0
        routes_weight = {}
        for target in routes:
            weight = 100
            route = routes[target]

            for wall_pos in route:
                wall_type = self.get_wall_type(wall_pos)

                if wall_type == 'opponent':
                    opponent_walls += 1
                    
                elif wall_type == 'my':
                    my_walls += 1

                elif wall_type == 'empty':
                    empty_walls += 1
            
            ratios = [4, 20, -3]
            if self.agent_state == 'normal':
                if self.agent.wall_breaker_cooldown != 0:
                    ratios[1] += 30
                    ratios[0] += 30

            elif self.agent_state == 'attack':
                ratios[0] = -5
                ratios[1] += 30
            
            
            change_percentage = (opponent_walls * ratios[0]) + (my_walls * ratios[1]) + (empty_walls * ratios[2])
            weight += weight*(change_percentage/100)

            routes_weight[target] = weight

        min_weight = min(list(routes_weight.values()))
        index = list(routes_weight.values()).index(min_weight)
        target = list(routes.keys())[index]
        
        return {target: routes[target]}
    
    def find_best_wall(self, walls):
        if self.agent_state == 'normal':
            qualified_targets = []

            walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
            min_weight = min(walls_weights)
            
            walls_to_remove = []
            for i in range(len(walls)):
                weight = walls_weights[i]
                diff = abs(weight - min_weight)

                accepted_range = range(0, 101)
                if diff not in accepted_range:
                    walls_to_remove.append(walls[i])

            for wall_pos in walls_to_remove:
                walls.remove(wall_pos)


            walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
            min_weight = min(walls_weights)
            index = walls_weights.index(min_weight)

            qualified_targets.append(walls[index])
            walls.pop(index)
            
            walls_agent_d = [self.walls[self.get_wall_type(wall_pos)][wall_pos]['agent_d'] for wall_pos in walls]
            min_distance = min(walls_agent_d)
            index1 = walls_agent_d.index(min_distance)

            max_distance = max(walls_agent_d)
            index2 = walls_agent_d.index(max_distance)

            qualified_targets.append(walls[index1])
            qualified_targets.append(walls[index2])

            targets_route = {}
            for target in qualified_targets:
                agent_pos = (self.agent.position.y, self.agent.position.x)
                
                route = self.find_best_route(agent_pos, target)
                targets_route[target] = route

            best_route = self.give_best_route(targets_route)
            wall_pos = list(best_route.keys())[0]

            return wall_pos
        
        elif self.agent_state == 'attack':
            # fitler 1
            walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
            min_weight = min(walls_weights)
            
            walls_to_remove = []
            for i in range(len(walls)):
                weight = walls_weights[i]
                diff = abs(weight - min_weight)

                accepted_range = range(0, 51)
                if diff not in accepted_range:
                    walls_to_remove.append(walls[i])

            for wall_pos in walls_to_remove:
                walls.remove(wall_pos)


            qualified_targets = []
            walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
            min_weight = min(walls_weights)
            index1 = walls_weights.index(min_weight)

            qualified_targets.append(walls[index1])
            walls.pop(index1)

            
            walls_agent_d = [self.walls[self.get_wall_type(wall_pos)][wall_pos]['agent_d'] for wall_pos in walls]
            min_distance = min(walls_agent_d)
            index2 = walls_agent_d.index(min_distance)

            average_distance = sum(walls_agent_d) // len(walls_agent_d)
            diffs = [abs(distance - average_distance) for distance in walls_agent_d]
            min_diff = min(diffs)
            index3 = diffs.index(min_diff)

            qualified_targets.append(walls[index2])
            qualified_targets.append(walls[index3])

            targets_route = {}
            for target in qualified_targets:
                agent_pos = (self.agent.position.y, self.agent.position.x)
                
                route = self.find_best_route(agent_pos, target)
                targets_route[target] = route

            best_route = self.give_best_route(targets_route)
            wall_pos = list(best_route.keys())[0]

            return wall_pos

            # # filter 2
            # distances = []
            # for wall_pos in filter1_qualifieds:
            #     distance_y, distance_x = abs(wall_pos[0] - agent_pos[0]), abs(wall_pos[1] - agent_pos[1])
            #     distance = sqrt(distance_y**2 + distance_x**2)
            #     distances.append(distance)
            
            # min_distance = min(distances)
            # filter2_qualifieds = []
            # min_diff, index = 10000, 0
            # for i in range(len(filter1_qualifieds)):
            #     distance = distances[i]
            #     diff = abs(distance - min_distance)

            #     if 0 <= diff and diff <= 60:
            #         wall_pos = walls[i]
            #         filter2_qualifieds.append(wall_pos)


            # # filter 3
            # distances = []
            # for wall_pos in filter2_qualifieds:
            #     distance_y, distance_x = abs(wall_pos[0] - opponent_pos[0]), abs(wall_pos[1] - opponent_pos[1])
            #     distance = sqrt(distance_y**2 + distance_x**2)
            #     distances.append(distance)
            
            # max_distance = max(distances)
            # filter3_qualifieds = []
            # min_diff, index = 10000, 0
            # for i in range(len(filter2_qualifieds)):
            #     distance = distances[i]
            #     diff = abs(distance - max_distance)

            #     if 0 <= diff and diff <= 30:
            #         wall_pos = filter2_qualifieds[i]
            #         filter3_qualifieds.append(wall_pos)

            # if len(filter3_qualifieds) == 1:
            #     index = 0
            # else:
            #     distances = []
            #     for wall_pos in filter3_qualifieds:
            #         distance_y, distance_x = abs(wall_pos[0] - opponent_pos[0]), abs(wall_pos[1] - opponent_pos[1])
            #         distance = sqrt(distance_y**2 + distance_x**2)
            #         distances.append(distance)
                
            #     max_distance = max(distances)
            #     index = distances.index(max_distance)

            # return filter1_qualifieds[index]

    def find_target(self):
        if self.agent_state == 'normal':
            agent_y, agent_x = self.agent.position.y, self.agent.position.x
            curr_wall_neighbors = self.walls_neighbors[(agent_y, agent_x)]

            wall_pos = self.find_best_wall(curr_wall_neighbors)

        elif self.agent_state == 'attack':
            opponent_walls = list(self.walls['opponent'].keys()).copy()

            agent_pos = (self.agent.position.y, self.agent.position.x)
            if agent_pos in opponent_walls:
                print('yeah, agent is here')
                opponent_walls.remove(agent_pos)
            
            opponent_pos = (self.opponent.position.y, self.opponent.position.x)
            if opponent_pos in opponent_walls:
                print('yeah, opponent is here')
                opponent_walls.remove(opponent_pos)

            wall_pos = self.find_best_wall(opponent_walls)

        elif self.agent_state == 'defence':
            opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

            range_y1 = opponent_y-3
            range_y2 = opponent_y+3
            if range_y1 <= 1:
                range_y1 = 1
            elif range_y2 >= len(self.board)-2:
                range_y2 = len(self.board)
                
            range_y = range(range_y1, range_y2+1)
            
            range_x1 = opponent_x-4
            range_x2 = opponent_x+4
            if range_x1 <= 1:
                range_x1 = 1
            elif range_x2 >= len(self.board[0])-2:
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

        elif self.agent_state == 'brutal':
            opponent_pos = (self.opponent.position.y, self.opponent.position.x)
            wall_pos = opponent_pos


        print('targes changed')
        self.target_passed_cycles = 10
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
                    heuristics[(i, j)] = distance*10

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
                    for wall_type in list(self.walls.keys())[:-2]:
                        positions = list(self.walls[wall_type].keys())
                        position = (i, j)
                        if position in positions:
                            costs[(i, j)] = self.get_wall_weight(position)


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
                        wall_cost += (wall_cost * 30/100)
                        costs[wall_pos] = int(wall_cost)

                if self.board[y][x] == m_wall:
                    wall_cost += (wall_cost * 60/100)
                    costs[wall_pos] = int(wall_cost)

                if self.agent_state == 'attack' or self.agent_state == 'brutal':
                    if self.board[y][x] == o_wall:
                        if self.agent.wall_breaker_rem_time > 2:
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

                    return path

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

    def find_next_route(self):
        agent_pos = (self.agent.position.y, self.agent.position.x)
        route = self.find_best_route(agent_pos, self.target_pos)

        self.reaching_path = route

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
            if pos_y == 0 or pos_y == len(self.board)-1 or pos_x == 0 or pos_x == len(self.board[0])-1:
                return 'side_area'
            else:
                return 'mid_area'

    def is_target_cycles_exceeded(self):
        self.target_passed_cycles -= 1
        if self.target_passed_cycles <= 0:
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
                    