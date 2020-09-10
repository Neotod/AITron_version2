from ks.models import ECell
from scripts.Tron import Tron

class Normal(Tron):
    def find_awalls_pos(board):
        awalls_pos = []

        for i in range(len(board)):
            for j in range(len(board[i])):
                if i == 0 or i == (len(board)-1):
                    awalls_pos.append((i, j))
                elif j == 0 or (j == len(board)-1):
                    awalls_pos.append((i, j))
                else:
                    if board[i][j] == ECell.AreaWall:
                        y_steps = [0, 1, -1, 0]
                        x_steps = [1, 0, 0, -1]

                        area_wall_sole = False
                        for m in range(4):
                            y = i + y_steps
                            x = j + x_steps
                            if board[y][x] != ECell.AreaWall:
                                area_wall_sole = True
                                break

                        if area_wall_sole:
                            awalls_pos.append((i, j))

    def find_awall_neighbors(board, awalls_pos):
        awall_neighbors_pos = []

        for position in awalls_pos:
            x = y = 0
            pos_y, pos_x = position[0], position[1]

            if pos_y == 0 or pos_y == ((len(board)-1)):
                if pos_y == 0:
                    y = pos_y+1
                elif pos_y == ((len(board)-1)):
                    y = pos_y-1

                x = pos_x

            elif pos_x == 0 or (pos_x == len(board)-1):
                if pos_x == 0:
                    x = pos_x+1
                elif pos_x == (len(board)-1):
                    x = pos_x-1                
                
            else:
                y_steps = [0, 1, -1, 0]
                x_steps = [1, 0, 0, -1]
                for m in range(4):
                    y = pos_y + y_steps
                    x = pos_x + x_steps
                    if board[y][x] != ECell.AreaWall:
                        break
            
            awall_neighbors_pos.append((y, x))
            

    def calc_awall_neighbors_weight(board, awall_neighbors_pos, weight_ratios: list):
            wall_y, wall_x = wall_pos[0], wall_pos[1]

            agent_pos = self.agent.posiiton
            enemy_pos = self.enemy.position
        
            agent_y, agent_x = agent_pos[0], agent_pos[1]
            enemy_y, enemy_x = enemy_pos[0], enemy_pos[1]

            y_side_agent = agent_y - wall_y
            x_side_agent = agent_x - wall_x
            agent_distance = round(sqrt(y_side_agent**2 + x_side_agent **2))

            y_side_enemy = enemy_y - wall_y
            x_side_enemy = enemy_x - wall_x
            enemy_distance = round(sqrt(y_side_enemy**2 + x_side_enemy **2))


            # check walls near the current wall

            if self.agent_name == 'Blue':
                my_wall = ECell.BlueWall
                enemy_wall = ECell.YellowWall
            elif self.agent_name == 'Yellow':
                my_wall = ECell.YellowWall
                enemy_wall = ECell.BlueWall
                
            y_steps = [0, -1, 1, 0]
            x_steps = [-1, 0, 0, 1]
            enemy_walls = my_walls = empty_walls = area_walls = 0
            for i in range(4):
                y = wall_y + y_steps[i]
                x = wall_x + x_steps[i]

                if board[y][x] == enemy_wall:
                    enemy_walls += 1
                elif board[y][x] == my_wall:
                    my_walls += 1
                elif board[y][x] == ECell.Empty:
                    empty_walls += 1
                else:
                    area_walls += 1


            weight = (agent_distance * -2) + (enemy_distance * -3) + (enemy_walls * 10) + (my_walls * -6) + (empty_walls * 5) + (area_walls * -1)


    def find_reaching_target(board):
        pass