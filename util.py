import tensorflow as tf
import pandas as pd
import numpy as np
import scipy.sparse as sp
import csv

from dataReformatter import reformat


#Helper functions from example (see file for credit)

def init_variable(size, dim, name=None):
    std = np.sqrt(2 / dim)
    return tf.Variable(tf.random_uniform([size, dim], -std, std), name=name)


def embed(inputs, size, dim, name=None):
    emb = init_variable(size, dim, name)
    return tf.nn.embedding_lookup(emb, inputs)


def get_variable(graph, session, name):
    v = graph.get_operation_by_name(name)
    v = v.values()[0]
    v = v.eval(session=session)
    return v

# Our functions

def loadModal(path):
    session = tf.Session()
    saver = tf.train.import_meta_graph(path)
    saver.restore(session, tf.train.latest_checkpoint('./'))
    return tf.get_default_graph(), session

def loadTestData():
    try:
        data = pd.read_csv('dataset/testData.csv', sep=',')

        with open('dataset/item_lookup.csv') as itemFile:
            reader = csv.reader(itemFile)
            table = [[cell for cell in row] for row in reader ]
            item_lookup = [[int(cell) for cell in row] for row in table[1:]]
        with open('dataset/user_lookup.csv') as userFile:
            reader = csv.reader(userFile)
            table = [[cell for cell in row] for row in reader ]
            user_lookup = [[int(cell) for cell in row] for row in table[1:]]
    except:
        raise FileExistsError("The test data doesn't exist.  Did you run training first?")
    return data,user_lookup[1:],item_lookup[1:]

def preprocessTestData(loaded):
    df, user_lookup, item_lookup = loaded

    lookUpUserDict = {row[1]: row[0] for row in user_lookup}

    lookUpItemDict = {row[1]: row[0] for row in item_lookup}

    df['user_id']= df['visitorid'].apply(lambda x: lookUpUserDict[x])
    df['item_id']= df['itemid'].apply(lambda x: lookUpItemDict[x])

    users = list(sorted(set(df.user_id)))
    items = list(sorted(set(df.item_id)))
    numEvents = list(df.eventsCount)

    return df, users, items, numEvents, lookUpUserDict, lookUpItemDict

def loadTrainingData():
    while True:
        try:
            res = pd.read_csv('dataset/trainData.csv', sep=',')
            break
        except:
            print("reformatting data")
            reformat()
    return res

# Remaining code borrows heavily from example as well

def preprocessTrainingData(df):


    df = df.dropna()

    df['user_id'] = df['visitorid'].astype("category").cat.codes
    df['item_id'] = df['itemid'].astype("category").cat.codes

    # Create a lookup frame so we can get the items original id back
    user_lookup = df[['user_id', 'visitorid']].drop_duplicates()
    user_lookup['user_id'] = user_lookup.user_id.astype(str)
    user_lookup.to_csv('dataset/user_lookup.csv',index = None, header=True)

    #create the same thing for the items
    item_lookup = df[['item_id', 'itemid']].drop_duplicates()
    item_lookup['item_id'] = item_lookup.item_id.astype(str)
    item_lookup.to_csv('dataset/item_lookup.csv',index = None, header=True)

    #df = df.loc[df.eventsCount != 0]
    #print(df)

    users = list(sorted(set(df.user_id)))
    items = list(sorted(set(df.item_id)))
    numEvents = list(df.eventsCount)

    return df, users, items, numEvents

def makeMatrix(tup):
    df, users, items, numEvents = tup

    rows = df.user_id.astype(float)
    cols = df.item_id.astype(float)

    data_sparse = sp.csr_matrix((numEvents, (rows, cols)), shape=(len(users), len(items)))

    uids, iids = data_sparse.nonzero()

    return df, users, items, numEvents, rows, cols, data_sparse, uids, iids
