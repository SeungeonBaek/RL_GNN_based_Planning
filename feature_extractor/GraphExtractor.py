from typing import List, Dict, Union, Any
from numpy.typing import NDArray

import tensorflow as tf

from tensorflow.keras import Model
from tensorflow.keras import initializers
from tensorflow.keras import regularizers
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM, LSTMCell
from tensorflow.keras.layers import GRU, GRUCell
from tensorflow.keras.layers import LayerNormalization
from tensorflow.keras.layers import BatchNormalization
# from tensorflow.keras.layers import GroupNormalization


class GCNExtractor(Model):
    def __init__(self, extractor_config: Dict, feature_dim: int)-> None:
        super(GCNExtractor,self).__init__()

        self.config = extractor_config

        # Initializer
        if self.config.get('initializer', None) == 'glorot_normal':
            self.initializer = initializers.glorot_normal()
        elif self.config.get('initializer', None) == 'he_normal':
            self.initializer = initializers.he_normal()
        elif self.config.get('initializer', None) == 'orthogonal':
            self.initializer = initializers.orthogonal()
        else:
            self.initializer = initializers.random_normal()

        # Regularizer
        if self.config.get('regularizer', None) == 'l1':
            self.regularizer = regularizers.l1(l=self.config['regularizer']['l1']) # 0.0005
        elif self.config.get('regularizer', None) == 'l2':
            self.regularizer = regularizers.l2(l=self.config['regularizer']['l2']) # 0.0005
        elif self.config.get('regularizer', None) == 'l1_l2':
            self.regularizer = regularizers.l1_l2(l1=self.config['regularizer']['l1'], l2=self.config['regularizer']['l2']) # 0.0005, 0.0005
        else:
            self.regularizer = None

        # Loading the network architecture


        # Define the network architecture


        self.feature = Dense(feature_dim, activation = self.config.get('act_fn', 'relu'))

    def call(self, state: Union[NDArray, tf.Tensor])-> tf.Tensor:

        feature = self.feature(state)

        return feature


class GATExtractor(Model):
    def __init__(self, extractor_config: Dict, feature_dim: int)-> None:
        super(GATExtractor,self).__init__()

        self.config = extractor_config

        # Initializer
        if self.config.get('initializer', None) == 'glorot_normal':
            self.initializer = initializers.glorot_normal()
        elif self.config.get('initializer', None) == 'he_normal':
            self.initializer = initializers.he_normal()
        elif self.config.get('initializer', None) == 'orthogonal':
            self.initializer = initializers.orthogonal()
        else:
            self.initializer = initializers.random_normal()

        # Regularizer
        if self.config.get('regularizer', None) == 'l1':
            self.regularizer = regularizers.l1(l=self.config['regularizer']['l1']) # 0.0005
        elif self.config.get('regularizer', None) == 'l2':
            self.regularizer = regularizers.l2(l=self.config['regularizer']['l2']) # 0.0005
        elif self.config.get('regularizer', None) == 'l1_l2':
            self.regularizer = regularizers.l1_l2(l1=self.config['regularizer']['l1'], l2=self.config['regularizer']['l2']) # 0.0005, 0.0005
        else:
            self.regularizer = None

        # Loading the network architecture


        # Define the network architecture


        self.feature = Dense(feature_dim, activation = self.config.get('act_fn', 'relu'))

    def call(self, state: Union[NDArray, tf.Tensor])-> tf.Tensor:

        feature = self.feature(state)

        return feature


def load_GraphExtractor(extractor_config:Dict, feature_dim):
    if extractor_config.get('name', None) == 'GCN':
        return GCNExtractor(extractor_config, feature_dim)

    elif extractor_config.get('name', None) == 'GAT':
        return GATExtractor(extractor_config, feature_dim)

    else:
        raise ValueError("please use the MLPExtractor in ['GCN', 'GAT']")


if __name__ == "__main__":
    # Devlopment required
    pass