from typing import Dict, Union, Any
from numpy.typing import NDArray

import tensorflow as tf
import numpy as np
import tensorflow_probability as tfp

from tensorflow.keras.optimizers import Adam
from tensorflow.keras import Model
from tensorflow.keras import initializers
from tensorflow.keras import regularizers
from tensorflow.keras.layers import Dense

from utils.replay_buffer import ExperienceMemory
from utils.prioritized_memory import PrioritizedMemory

from agents.ICM_model import ICM_model
from agents.RND_model import RND_target, RND_predict


class DistCritic(Model): # Distributional Q network
    def __init__(self,
                 quantile_num: int,
                 obs_space: int,
                 action_space: int)-> None:
        super(DistCritic,self).__init__()
        self.quantile_num = quantile_num

        self.obs_space = obs_space
        self.action_space = action_space

        self.initializer = initializers.he_normal()
        self.regularizer = regularizers.l2(l=0.001)
        
        self.l1 = Dense(256, activation = 'relu' , kernel_initializer=self.initializer, kernel_regularizer=self.regularizer)
        self.l2 = Dense(256, activation = 'relu' , kernel_initializer=self.initializer, kernel_regularizer=self.regularizer)
        self.l3 = Dense(128, activation = 'relu' , kernel_initializer=self.initializer, kernel_regularizer=self.regularizer)
        self.l4 = Dense(128, activation = 'relu' , kernel_initializer=self.initializer, kernel_regularizer=self.regularizer)
        self.value_dist = Dense(self.action_space * self.quantile_num, activation = None)

    def call(self, state: Union[NDArray, tf.Tensor])-> tf.Tensor:
        l1 = self.l1(state) # 확인
        l2 = self.l2(l1)
        l3 = self.l3(l2)
        l4 = self.l4(l3)
        value_dist = self.value_dist(l4)
        value_dist = tf.reshape(value_dist, shape=(state.shape[0], self.action_space, self.quantile_num)) # check 필요

        return value_dist


class Agent:
    """
    Argument:
        agent_config: agent configuration which is realted with RL algorithm => QR-DQN
            agent_config:
                {
                    name, gamma, tau, update_freq, batch_size, warm_up, lr_actor, lr_critic,
                    buffer_size, use_PER, use_ERE, reward_normalize
                    extension = {
                        'name', 'use_DDQN'
                    }
                }
        obs_space: shpae of observation
        act_space: shape of action

    Properties: Todo
        agent_config: asdf
        name: asdf
        obs_space: asdf
        act_space: asdf
        gamma: asdf

        epsilon: asdf
        epsilon_decaying_rate: asdf
        min_epsilon: asdf

        update_step: asdf
        update_freq: asdf
        target_update_freq: asdf

        replay_buffer: asdf
        batch_size: asdf
        warm_up: asdf

        critic_lr_main: asdf
        critic_target: asdf
        critic_opt_main: asdf

        # extension properties
        extension_config: asdf
        extension_name: asdf
            
            # icm
            icm_update_freq: asdf
            icm_lr: asdf
            icm_feqture_dim: asdf

            icm: asdf
            icm_opt: asdf

            # rnd
            rnd_update_freq: asdf
            rnd_lr: asdf
            
            rnd_target: asdf
            rnd_predict: asdf
            rnd_opt: asdf

            # ngu
            None (Todo)

    Methods:
        action: return the action which is mapped with obs in policy
        get_intrinsic_reward: return the intrinsic reward
        update_target: update target critic network at user-specified frequency
        update: update main distributional critic network
        save_xp: save transition(s, a, r, s', d) in experience memory
        load_models: load weights
        save_models: save weights

    """
    def __init__(self,
                 agent_config: Dict,
                 obs_space: int,
                 act_space: int)-> None:
        self.agent_config = agent_config
        self.name = self.agent_config['agent_name']

        self.obs_space = obs_space
        self.act_space = act_space
        print(f'obs_space: {self.obs_space}, act_space: {self.act_space}')

        self.critic_lr_main = self.agent_config['lr_critic']

        self.gamma = self.agent_config['gamma']
        self.tau = self.agent_config['tau']
        self.quantile_num = self.agent_config['quantile_num']

        self.update_step = 0
        self.update_freq = self.agent_config['update_freq']
        self.target_update_freq = agent_config['target_update_freq']

        if self.agent_config['use_PER']:
            self.replay_buffer = PrioritizedMemory(self.agent_config['buffer_size'])
        else:
            self.replay_buffer = ExperienceMemory(self.agent_config['buffer_size'])
        self.batch_size = self.agent_config['batch_size']
        self.warm_up = self.agent_config['warm_up']

        self.epsilon = self.agent_config['epsilon']
        self.epsilon_decaying_rate = self.agent_config['epsilon_decaying_rate']

        # network config
        self.critic_lr_main = self.agent_config['lr_critic']

        self.critic_main = DistCritic(self.quantile_num, self.obs_space, self.act_space)
        self.critic_target = DistCritic(self.quantile_num, self.obs_space, self.act_space)
        self.critic_target.set_weights(self.critic_main.get_weights())
        self.critic_opt_main = Adam(self.critic_lr_main)
        self.critic_main.compile(optimizer=self.critic_opt_main)

        # extension config
        self.extension_config = self.agent_config['extension']
        self.extension_name = self.extension_config['name']

        if self.extension_name == 'ICM':
            self.icm_update_freq = self.extension_config['icm_update_freq']

            self.icm_lr = self.extension_config['icm_lr']
            self.icm_feature_dim = self.extension_config['icm_feature_dim']
            self.icm = ICM_model(self.obs_space, self.act_space, self.icm_feature_dim)
            self.icm_opt = Adam(self.icm_lr)

        elif self.extension_name == 'RND':
            self.rnd_update_freq = self.extension_config['rnd_update_freq']

            self.rnd_lr = self.extension_config['rnd_lr']
            self.rnd_target = RND_target(self.obs_space, self.act_space)
            self.rnd_predict = RND_predict(self.obs_space, self.act_space)
            self.rnd_opt = Adam(self.rnd_lr)

        elif self.extension_name == 'NGU':
            self.icm_lr = self.extension_config['ngu_lr']

    def action(self, obs: NDArray)-> NDArray: # Todo
        obs = tf.convert_to_tensor([obs], dtype=tf.float32)
        # print(f'in action, obs: {np.shape(np.array(obs))}')
        value_dist = self.critic_main(obs)
        # print(f'in action, value_dist: {np.shape(np.array(value_dist))}')

        random_val = np.random.rand()
        if self.update_step > self.warm_up:
            if random_val > self.epsilon:
                mean_value = np.mean(value_dist.numpy(), axis=1) # Todo: CVaR
                action = np.argmax(mean_value)
            else:
                action = np.random.randint(self.act_space)
        else:
            action = np.random.randint(self.act_space)
        # print(f'in action, action: {np.shape(np.array(action))}')

        self.epsilon *= self.epsilon_decaying_rate
        if self.epsilon < self.min_epsilon:
            self.epsilon = self.min_epsilon

        return action

    def get_intrinsic_reward(self, state: NDArray, next_state: NDArray, action: NDArray)-> float:
        reward_int = 0
        if self.extension_name == 'ICM':
            state = tf.convert_to_tensor([state], dtype=tf.float32)
            next_state = tf.convert_to_tensor([next_state], dtype=tf.float32)
            action = tf.convert_to_tensor([action], dtype=tf.float32)
            
            feature_next_s, pred_feature_next_s, _ = self.icm((state, next_state, action))

            reward_int = tf.clip_by_value(tf.reduce_mean(tf.math.square(tf.subtract(feature_next_s, pred_feature_next_s))), 0, 5)
            reward_int = reward_int.numpy()
        
        elif self.extension_name == 'RND':
            next_state = tf.convert_to_tensor([next_state], dtype=tf.float32)
            
            target_value = self.rnd_target(next_state)
            predict_value = self.rnd_predict(next_state)

            reward_int = tf.clip_by_value(tf.reduce_mean(tf.math.square(tf.subtract(predict_value, target_value))), 0, 5)
            reward_int = reward_int.numpy()

        elif self.extension_name == 'NGU':
            pass

        return reward_int

    def update_target(self)-> None:
        critic_main_weight = self.critic_main.get_weights()
        self.critic_target.set_weights(critic_main_weight)

    def update(self)-> None:
        if self.replay_buffer._len() < self.batch_size:
            if self.extension_name == 'ICM':
                return False, 0.0, 0.0, 0.0, 0.0, 0.0
            elif self.extension_name == 'RND':
                return False, 0.0, 0.0, 0.0, 0.0
            elif self.extension_name == 'NGU':
                return False, 0.0, 0.0, 0.0
            else:
                return False, 0.0, 0.0, 0.0

        updated = True
        self.update_step += 1
        
        if self.agent_config['use_PER']:
            states, next_states, rewards, actions, dones, idxs, is_weight = self.replay_buffer.sample(self.batch_size)

            if self.agent_config['reward_normalize']:
                rewards = np.asarray(rewards)
                rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)

            states = tf.convert_to_tensor(states, dtype = tf.float32)
            next_states = tf.convert_to_tensor(next_states, dtype = tf.float32)
            rewards = tf.convert_to_tensor(rewards, dtype = tf.float32)
            actions = tf.squeeze(tf.convert_to_tensor(actions, dtype = tf.float32))
            dones = tf.convert_to_tensor(dones, dtype = tf.bool)
            is_weight = tf.convert_to_tensor(is_weight, dtype=tf.float32)
        
        else:
            states, next_states, rewards, actions, dones = self.replay_buffer.sample(self.batch_size)

            if self.agent_config['reward_normalize']:
                rewards = np.asarray(rewards)
                rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)

            states = tf.convert_to_tensor(states, dtype = tf.float32)
            next_states = tf.convert_to_tensor(next_states, dtype = tf.float32)
            rewards = tf.convert_to_tensor(rewards, dtype = tf.float32)
            actions = tf.squeeze(tf.convert_to_tensor(actions, dtype = tf.float32))
            dones = tf.convert_to_tensor(dones, dtype = tf.bool)
        
        critic_variable = self.critic_main.trainable_variables
        with tf.GradientTape() as tape_critic:  # Todo
            tape_critic.watch(critic_variable)
            # print(f'in update, states: {states.shape}')
            # print(f'in update, next_states: {next_states.shape}')
            # print(f'in update, actions: {actions.shape}')
            # print(f'in update, rewards: {rewards.shape}')
            
            target_q_next = tf.reduce_max(self.critic_target(next_states), axis=1)
            # print(f'in update, target_q_next: {target_q_next.shape}')

            target_q = rewards + self.gamma * target_q_next * (1.0 - tf.cast(dones, dtype=tf.float32))
            # print(f'in update, target_q_next: {target_q_next.shape}')

            current_q = self.critic_main(states)
            # print(f'in update, current_q: {current_q.shape}')
            action_one_hot = tf.one_hot(tf.cast(actions, tf.int32), self.act_space)
            # print(f'in update, action_one_hot: {action_one_hot.shape}')
            current_q = tf.reduce_sum(tf.multiply(current_q, action_one_hot), axis=1)
            # print(f'in update, current_q: {current_q.shape}')
        
            critic_loss = tf.keras.losses.MSE(target_q, current_q)
            # print(f'in update, critic_loss: {critic_loss.shape}')

        grads_critic, _ = tf.clip_by_global_norm(tape_critic.gradient(critic_loss, critic_variable), 0.5)

        self.critic_opt_main.apply_gradients(zip(grads_critic, critic_variable))

        target_q_val = target_q.numpy()
        current_q_val = current_q.numpy()
        critic_loss_val = critic_loss.numpy()

        if self.update_step % self.target_update_freq == 0:
            self.update_target()

        return updated, np.mean(critic_loss_val), np.mean(target_q_val), np.mean(current_q_val)

    def save_xp(self, state: NDArray, next_state: NDArray, reward: float, action: int, done: bool)-> None:
        # Store transition in the replay buffer.
        if self.agent_config['use_PER']:
            state_tf = tf.convert_to_tensor([state], dtype = tf.float32)
            action_tf = tf.convert_to_tensor([action], dtype = tf.float32)
            next_state_tf = tf.convert_to_tensor([next_state], dtype = tf.float32)
            target_action_tf = self.critic_target(next_state_tf)
            # print(f'state_tf: {state_tf.shape}, {state_tf}')
            # print(f'action_tf: {action_tf.shape}, {action_tf}')
            # print(f'next_state_tf: {next_state_tf.shape}, {next_state_tf}')
            # print(f'target_action_tf: {target_action_tf.shape}, {target_action_tf}')

            current_q_next = self.critic_main(next_state_tf)
            # print(f'current_q_next: {current_q_next.shape}, {current_q_next}')
            next_action = tf.argmax(current_q_next, axis=1)
            # print(f'next_action: {next_action.shape}, {next_action}')
            indices = tf.stack([[0], next_action], axis=1)
            # print(f'indices: {indices.shape}, {indices}')

            target_q_next = self.critic_target(next_state_tf)
            # print(f'target_q_next: {target_q_next.shape}, {target_q_next}')

            target_q_next = tf.cond(tf.convert_to_tensor(self.extension_config['use_DDQN'], dtype=tf.bool),\
                    lambda: tf.gather_nd(params=self.critic_target(next_state_tf), indices=indices), \
                    lambda: tf.reduce_max(self.critic_target(next_state_tf), axis=1))
            # print(f'target_q_next: {target_q_next.shape}, {target_q_next}')

            target_q = reward + self.gamma * target_q_next * (1.0 - tf.cast(done, dtype=tf.float32))
            # print(f'target_q: {target_q.shape}, {target_q}')
            
            current_q = self.critic_main(state_tf)
            # print(f'current_q: {current_q.shape}, {current_q}')
            action_one_hot = tf.one_hot(tf.cast(action_tf, tf.int32), self.act_space)
            # print(f'action_one_hot: {action_one_hot.shape}, {action_one_hot}')
            current_q = tf.reduce_sum(tf.multiply(current_q, action_one_hot), axis=1)
            # print(f'current_q: {current_q.shape}, {current_q}')
            
            td_error = tf.subtract(target_q ,current_q)
            # print(f'td_error: {td_error.shape}, {td_error}')

            td_error_numpy = np.abs(td_error)
            # print(f'td_error_numpy: {td_error_numpy.shape}, {td_error_numpy}')

            self.replay_buffer.add(td_error_numpy[0], (state, next_state, reward, action, done))
        else:
            self.replay_buffer.add((state, next_state, reward, action, done))

    def load_models(self, path: str)-> None:
        print('Load Model Path : ', path)
        self.critic_main.load_weights(path, "_critic_main")
        self.critic_target.load_weights(path, "_critic_target")

    def save_models(self, path: str, score: float)-> None:
        save_path = path + "score_" + str(score) + "_model"
        print('Save Model Path : ', save_path)
        self.critic_main.save_weights(save_path, "_critic_main")
        self.critic_target.save_weights(save_path, "_critic_target")