from ks.models import ECell
from math import sqrt

def is_attack_target_increased(self):
    prev_distance = self.attack_target_init_dist
    curr_distance = self.walls[self.get_wall_type(self.target_pos)][self.target_pos]['agent_d']

    if prev_distance < curr_distance:
        self.attack_target_init_dist = curr_distance
        return True
    else:
        return False

def is_target_wall_type_changed(self):
    prev_wall_type = self.target_wall_type
    curr_wall_type = self.get_wall_type(self.target_pos)

    if prev_wall_type != curr_wall_type:
        return True
    else:
        return False

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

def is_enough_opp_wall_around_us(self):
    agent_pos = (self.agent.position.y, self.agent.position.x)

    range_y = [agent_pos[0]-10, agent_pos[0]+10]
    range_y[0] = 1 if range_y[0] < 1 else range_y[0]
    range_y[1] = len(self.board)-2 if range_y[1] > len(self.board)-2 else range_y[1]
    y_range = range(range_y[0], range_y[1]+1)

    range_x = [agent_pos[1]-6, agent_pos[1]+6]
    range_x[0] = 1 if range_x[0] < 1 else range_x[0]
    range_x[1] = len(self.board[0])-2 if range_x[1] > len(self.board[0])-2 else range_x[1]
    x_range = range(range_x[0], range_x[1]+1)

    walls_number = 0
    opponnet_walls_around = []
    for i in y_range:
        for j in x_range:
            wall_type = self.get_wall_type((i, j))
            if wall_type == 'opponent':
                walls_number += 1
                opponnet_walls_around.append((i, j))

    if walls_number >= 4:
        self.attack_possible_targets = opponnet_walls_around
        return True
    else:
        return False

def is_agent_around_dense(self):
    agent_pos = (self.agent.position.y, self.agent.position.x)

    range_y = [agent_pos[0]-7, agent_pos[0]+7]
    range_x = [agent_pos[1]-7, agent_pos[1]+7]

    range_y[0] = 1 if range_y[0] < 1 else range_y[0]
    range_y[1] = len(self.board)-2 if range_y[1] > len(self.board)-2 else range_y[1]
    range_x[0] = 1 if range_x[0] < 1 else range_x[0]
    range_x[1] = len(self.board[0])-2 if range_x[1] > len(self.board[0])-2 else range_x[1]
    
    range_y = range(range_y[0], range_y[1]+1)
    range_x = range(range_x[0], range_x[1]+1)
    
    empty_walls = opponent_walls = my_walls = area_walls = 0
    for i in range_y:
        for j in range_x:
            wall_type = self.get_wall_type((i, j))
            if wall_type == 'my':
                my_walls += 1
            elif wall_type == 'opponent':
                opponent_walls += 1
            elif wall_type == 'empty':
                empty_walls += 1
            elif wall_type == 'mid_area':
                area_walls += 1

    density = opponent_walls + my_walls - empty_walls
    self.log_string += f'density: {density}\n'
    if density > 20:
        return True
    else:
        return False

def get_distance(self, start_pos: tuple, end_pos: tuple) -> float:
    distance_y = abs(start_pos[0] - end_pos[0])
    distance_x = abs(start_pos[1] - end_pos[1])
    distance = sqrt(distance_y**2 + distance_x**2)

    return distance

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

def init_file(self):
    with open(f'log{self.agent_name}.txt', 'w') as file:
        file.write(f'START FOR TEAM {self.agent_name}\n\n\n')

def output_log(self):
    with open(f'log{self.agent_name}.txt', 'a') as file:
        file.writelines(self.log_string)
    self.log_string = ''