import os
from p_tqdm import p_map

import tensorflow as tf
import multiprocessing
import argparse

from utils import (get_wav, to_mfcc, 
                    normalize_mfcc, make_segments, 
                    segment_one, load_data, get_input_shape)
                            
from model import Model

import logging
logging.basicConfig(format='%(asctime)s', level=logging.INFO)

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

def parser():
    parser = argparse.ArgumentParser(description='Configs for training')
    parser.add_argument("--DEBUG", default = True, type = bool, help = 'Debug mode')
    parser.add_argument("--SILENCE_THRESHOLD", default = .01, type = float, help = 'Debug mode')
    parser.add_argument('--COL_SIZE', default = 30, type = int, help = 'Range of a single segment')
    parser.add_argument('--SAVE_CHECKPOINT_FREQUENCY', default = 5, type = int, help = 'Save checkpoint per number of epochs')
    parser.add_argument('--NUM_EPOCH', default = 100,type = int, help = 'Number of epochs')
    parser.add_argument('--DATA_DIR', type = str, help = 'Dir of data')
    parser.add_argument('--CHECKPOINT_DIR', default = 'checkpoint', type = str, help ='Dir of checkpoint')
    parser.add_argument('--LOG', default='logs', type = str, help = 'Dir of logs')
    parser.add_argument('--BATCH_SIZE', default=32, type = int)
    parser.add_argument('--STEPS_PER_EPOCH', default=128, type = int)
    parser.add_argument('--LOAD_CHECKPOINT_DIR', default=None, type = str)
    parser.add_argument('--LR', default=0.01, type = float)
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    
    # init arparser
    args = parser()

    #labels
    categories = {'female_central' : 0,
                  'male_central' : 1,
                  'female_north' : 2,
                  'male_north' : 3,
                  'female_south' : 4,
                  'male_south' : 5}

    #load data
    X, y = load_data(args.DATA_DIR, categories = categories)


    # Get resampled wav files using multiprocessing
    logging.info('Loading wav files....')
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

    #load DATA
    X = p_map(get_wav, X)

    # # Convert to MFCC
    logging.info('Converting to MFCC....')
    X = p_map(to_mfcc, X)
    
    # # Data normalization
    logging.info('Nomalizing data....')
    X = p_map(normalize_mfcc,X)

    # # get the input shape 
    input_shape = get_input_shape(X, args.COL_SIZE)
    
    # # initiate model
    model = Model(input_shape = input_shape, num_classes = len(categories), lr = args.LR)

    #load the weights                
    if (args.LOAD_CHECKPOINT_DIR != None): 
        model.load_weights(args.LOAD_CHECKPOINT_DIR)

    #Evaluates
    acc = 0.0

    for X_,y_ in zip(X, y):
        X_, y_ = segment_one(X_ ,y_, COL_SIZE = args.COL_SIZE)
        score = model.evaluate(X_, y_)
        
        acc += (score[1] >= 0.17)

    print('Accuracy : ',acc / len(y))
    