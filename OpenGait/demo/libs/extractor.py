import os
import os.path as osp
import pickle
import sys
import shutil

root = os.path.dirname(os.path.dirname(os.path.dirname( os.path.abspath(__file__) )))
sys.path.append(root)
from opengait.utils import config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname( os.path.abspath(__file__)))) + "/modeling/")
from loguru import logger
import model.baselineDemo as baselineDemo
import gait_compare as gc

extractor_cfgs = {  
    "gaitmodel":{
        "model_type": "BaselineDemo",
        "cfg_path": "./configs/baseline/baseline_GREW.yaml",
    },
}


def loadModel(model_type, cfg_path):
    Model = getattr(baselineDemo, model_type)
    cfgs = config_loader(cfg_path)
    model = Model(cfgs, training=False)
    return model

def gait_sil(sils, embs_save_path):
    gaitmodel = loadModel(**extractor_cfgs["gaitmodel"])
    gaitmodel.requires_grad_(False)
    gaitmodel.eval()
    feats = {}
    for inputs in sils:
        ipts = gaitmodel.inputs_pretreament(inputs)
        id = inputs[1][0]
        if id not in feats:
            feats[id] = []
        type = inputs[2][0] 
        view = inputs[3][0]
        embs_pkl_path = "{}/{}/{}/{}".format(embs_save_path, id, type, view)
        if not os.path.exists(embs_pkl_path):
            os.makedirs(embs_pkl_path)
        embs_pkl_name = "{}/{}.pkl".format(embs_pkl_path, inputs[3][0])
        retval, embs = gaitmodel.forward(ipts)
        pkl = open(embs_pkl_name, 'wb')
        pickle.dump(embs, pkl)
        feat = {}
        feat[type] = {}
        feat[type][view] = embs
        feats[id].append(feat)        
    return feats    

def gaitfeat_compare(probe_feat:dict, gallery_feat:dict):
    item = list(probe_feat.keys())
    # for item in probe_feat.items():
    probe = item[0]
    pg_dict = {}
    pg_dicts = {}
    for inputs in probe_feat[probe]:
        number = list(inputs.keys())[0]
        probeid = probe + "-" + number
        galleryid, idsdict = gc.comparefeat(inputs[number]['undefined'], gallery_feat, probeid, 100)
        pg_dict[probeid] = galleryid
        pg_dicts[probeid] = idsdict
    print("=================== pg_dicts ===================")
    print(pg_dicts)
    return pg_dict

# def extract_sil(probe_sil, save_embs_path):
def extract_sil(sil, save_path):
    logger.info("begin extracting")
    video_feat = gait_sil(sil, save_path)
    logger.info("extract Done")
    return video_feat