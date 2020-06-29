import tensorflow.keras.backend as K


def r2_score(y_true, y_pred):
    ss_res = K.sum(K.square(y_true-y_pred))
    ss_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - ss_res/(ss_tot + K.epsilon()))


def rpd(y_true, y_pred):
    sep = K.sqrt(K.mean(K.square(y_pred - y_true)))
    sd = K.std(y_true)
    return sd/sep
