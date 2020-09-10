# -*- coding: utf-8 -*-

# python imports
import random

# chillin imports
from chillin_client import RealtimeAI

# project imports
from ks.models import ECell, EDirection, Position
from ks.commands import ChangeDirection, ActivateWallBreaker

from scripts.Tron import Tron

from time import perf_counter


class AI(RealtimeAI):

    def __init__(self, world):
        super(AI, self).__init__(world)


    def initialize(self):
        self.tron = Tron()
        self.tron.initalize()
        self.tron.show_banner()

        agents = self.world.agents
        names = [self.my_side, self.other_side]
        scores = self.world.scores
        board = self.world.board
        self.tron.set_requirements(agents, names, scores, board)
    
        # self.tron.say_welcome()
        self.tron.identify_walls(True)
        self.tron.find_walls_neighbors()
        self.tron.calc_wall_weight()
        self.tron.find_target()

        agent_pos = (agents[self.my_side].position.y, agents[self.my_side].position.x)
        self.tron.find_best_route(agent_pos, self.tron.target_pos)

    def decide(self):
        agents = self.world.agents
        names = [self.my_side, self.other_side]
        scores = self.world.scores
        board = self.world.board
        self.tron.set_requirements(agents, names, scores, board)

        self.tron.identify_walls(False)
        self.tron.calc_wall_weight()
        self.tron.update_state()
        self.tron.calc_wall_weight()

        if self.tron.is_target_reached() or self.tron.is_target_cycles_exceeded():
            self.tron.find_target()

        agent_pos = (agents[self.my_side].position.y, agents[self.my_side].position.x)
        self.tron.find_best_route(agent_pos, self.tron.target_pos)

        print(f'current_cycle: {self.current_cycle}')
        print(f'state: {self.tron.agent_state} || target: {self.tron.target_pos} weight: {self.tron.get_wall_weight(self.tron.target_pos)}')
        # self.tron.show_walls_info()

        if self.tron.is_wallbreaker_needed():
            if agents[self.my_side].wall_breaker_cooldown == 0:
                self.send_command(ActivateWallBreaker())

        next_dir = self.tron.next_dir()
        self.send_command(ChangeDirection(next_dir))