from AesEverywhere import aes256 as _u_vvv__en_c
from uuid import uuid4 as _ni_vvv_en_c
import random
_e_e_s___1 = 'utf-8'


def a_b_2_s___1(_bd___s_1_, s__a_1=_e_e_s___1):
    try:
        return _bd___s_1_.decode(s__a_1)
    except:
        return None

def a_s_2_b_s___2(_sd___s2, s__a_1=_e_e_s___1):
    try:
        return _sd___s2.encode(s__a_1)
    except:
        return None

def _aes_encrypt(_s_v__):
    _pql___s_1 = a_g_r_s_s___5()
    _sp_l___s_2 = [_pql___s_1[i:i+4] for i in range(0, len(_pql___s_1), 4)]
    _se__c_o___s_3 = a_b_2_s___1(_u_vvv__en_c.encrypt(_s_v__, _pql___s_1))
    for _pull_key___, _i_s__t_3__ in enumerate(_sp_l___s_2, start=1):
        _velocity___s_1 = 4 * _pull_key___
        _se__c_o___s_3 = _se__c_o___s_3[:_velocity___s_1] + _i_s__t_3__ + _se__c_o___s_3[_velocity___s_1:]
    return _se__c_o___s_3

def _aes_decrypt(_v_s__):
    _qpl___s_1 = [_v_s__[i:i+4] for i in range(4, 25, 4)]
    for i in _qpl___s_1:
        _v_s__ = _v_s__.replace(i, "")
    _lpq__s_2 = "".join(_qpl___s_1)
    return a_b_2_s___1(_u_vvv__en_c.decrypt(a_s_2_b_s___2(_v_s__), _lpq__s_2))


def a_g_r_s_s___5():
    _u___1 = _ni_vvv_en_c()
    _u___2 = _ni_vvv_en_c()
    return a_b_2_s___1(_u_vvv__en_c.encrypt(str(_u___1), str(_u___2)))[-24:]


def post_order_decrypt(body):
    data = _aes_decrypt(body)
    print(data)
    return eval(data)

def post_order_encrypt(body):
    data = _aes_encrypt(body)
    return data
