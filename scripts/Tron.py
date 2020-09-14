from math import sqrt
from ks.models import ECell, EDirection
from time import perf_counter
from random import choice


class Tron:
    def __init__(self):
        self.target_passed_cycles = 0
        self.opponent_distance = 0

        self.agent_state = 'normal' # normal defence attack brutal
        self.agent_attack_state = 'onway' # onway or attacking
        self.target_pos = ()
        self.agent_prev_pos = ()

        self.walls = {}
        self.walls_neighbors = {}
        self.walls_closest_awalls = {}

        self.reaching_path = []
        self.reaching_path_index = 0

    # class functions import
    from .methods._path_finding import find_best_route, find_attack_routes, get_costs, get_heuristics, set_next_route, choose_best_attack_route
    from .methods._initialize import set_walls, set_requirements, find_walls_neighbors, find_closest_area_wall
    from .methods._target_finding import find_best_wall, find_target, choose_best_target

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
            return 10000
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
            if self.board[wall_y][wall_x] == opponent_wall:
                agent_d_ratio = 3

            distance_weight = (agent_distance * agent_d_ratio) + ((1/(opponent_distance)) * opponent_d_ratio)
            distance_weight *= 20
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
                        wall_ratio = 2

                elif wall_type == 'empty':
                    wall_ratio = 2

            elif self.agent_state == 'attack' or self.agent_state == 'brutal':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    wall_ratio = 2
                    
                elif wall_type == 'empty':
                    wall_ratio = 2
            
            elif self.agent_state == 'defence':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    if self.agent.wall_breaker_cooldown != 0:
                        wall_ratio = 7
                    else:
                        wall_ratio = 4

                elif wall_type == 'empty':
                    wall_ratio = 2

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
                    ratios[1] += -5

            elif self.agent_state == 'attack' or self.agent_state == 'brutal':
                ratios = [-2, 10, -0.5, -10]
                if self.get_wall_type(wall_pos) == 'opponent':
                        ratios[0] += 0.5
                        ratios[2] += -0.5
                elif self.get_wall_type(wall_pos) == 'empty':
                    if opponent_walls > 15:
                        ratios[0] = -1
                        ratios[2] = -0.4


            elif self.agent_state == 'defence':
                ratios = [7, 10, -0.5, 0]
                if self.board[wall_y][wall_x] == ECell.Empty:
                    ratios[1] += -5


            weight += (weight*((opponent_walls * ratios[0])/100))
            weight += (weight*((my_walls * ratios[1])/100))
            weight += (weight*((empty_walls * ratios[2])/100))
            weight += (weight*((area_walls * ratios[3])/100))


            # different situations

            if (((self.agent_state == 'attack' or self.agent_state == 'brutal') and self.board[wall_y][wall_x] == opponent_wall)
                or ((self.agent_state == 'normal' or self.agent_state == 'defence') and self.board[wall_y][wall_x] == ECell.Empty)):

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
                
                if self.board[wall_y][wall_x] == opponent_wall:
                    addition_ratios = [20, -10, -20, -10]
                    if my_walls == 1:
                        addition_ratios[0] = -20
                        addition_ratios[2] = -5

                elif self.board[wall_y][wall_x] == ECell.Empty:
                    addition_ratios = [-70, -5, -10, -10]
                    if my_walls == 4 or my_walls == 3:
                        addition_ratios[0] = 0
                    elif my_walls == 2:
                        addition_ratios[0] = 10

                weight += (weight*((my_walls * addition_ratios[0])/100))
                weight += (weight*((opponent_walls * addition_ratios[1])/100))
                weight += (weight*((empty_walls * addition_ratios[2])/100))
                weight += (weight*((area_walls * addition_ratios[3])/100))
            
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

        if self.opponent_distance <= 3:
            if my_score <= opponent_score:
                self.agent_state = 'defence'

            elif my_score > opponent_score + 3:
                if self.opponent_distance <= 2:
                    self.agent_state = 'brutal'
                    
        elif self.agent_state != 'attack':
            if self.opponent_distance > 4:
                if self.curr_cycle >= 10:
                    if self.agent.wall_breaker_cooldown == 0:
                        self.agent_state = 'attack'

                if self.agent.wall_breaker_cooldown == 0:
                    if my_score > opponent_score + 10:
                        self.agent_state = 'brutal'
                else:
                    self.agent_state = 'normal'


        # emergencies
        if self.agent_state != 'attack' or (self.agent_state == 'attack' and self.agent_attack_state == 'onway'):
            if self.agent.wall_breaker_rem_time == 1:
                self.agent_state = 'normal'

        # if self.agent.wall_breaker_rem_time > 1:
        #     self.agent_state = 'attack'

        # elif self.agent.wall_breaker_rem_time == 1:
        #     self.agent_state = 'normal'

        if self.agent_state == 'defence':
            if distance <= 1:
                self.find_target()

        if self.agent_state == 'attack' and self.agent_attack_state == 'attacking':
            self.reaching_path_index += 1
            print(self.reaching_path_index)
            if self.reaching_path_index == len(self.reaching_path)-1:
                self.agent_state = 'normal'
                self.agent_attack_state = 'onway'
        
                
        print(f'state:  {self.agent_state} || agent_attack_state:  {self.agent_attack_state}')
        if prev_state != self.agent_state:
            self.target_passed_cycles = 0
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
            if pos_y == 0 or pos_y == len(self.board)-1 or pos_x == 0 or pos_x == len(self.board[0])-1:
                return 'side_area'
            else:
                return 'mid_area'
                
    def is_opponent_wall_around_us(self):
        pass

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
        if self.agent_state != 'attack' or (self.agent_state == 'attack' and self.agent_attack_state == 'onway'):
            index = 1
        elif self.agent_state == 'attack' and self.agent_attack_state == 'attacking':
            index = self.reaching_path_index+1
        
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
                    print('{:<5}'.format('===='), end='')
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
                    