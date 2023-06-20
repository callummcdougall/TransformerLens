"""
Main set of utils to import at the start of all scripts and notebooks
"""

import warnings

import torch as t
import torch
warnings.warn("Setting grad enabled false...")
t.set_grad_enabled(False)

import numpy as np
from jaxtyping import Float, Int, Bool, jaxtyped
from typing import Union, List, Dict, Tuple, Callable, Optional, Any, Sequence, Iterable, Mapping, TypeVar, Generic, NamedTuple, Literal
from torch import Tensor
import itertools
import torch.nn.functional as F
from tqdm.auto import tqdm
from rich import print as rprint
from transformer_lens import utils, HookedTransformer, ActivationCache
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from functools import partial
import re
from pathlib import Path
import einops
from IPython.display import display, clear_output, HTML
import circuitsvis as cv

import transformer_lens
from transformer_lens import *
from transformer_lens.utils import *
from transformer_lens.hook_points import HookPoint

def to_tensor(
    tensor,
):
    return t.from_numpy(to_numpy(tensor))

def old_imshow(
    tensor, 
    **kwargs,
):
    tensor = to_tensor(tensor)
    zmax = tensor.abs().max().item()

    if "zmin" not in kwargs:
        kwargs["zmin"] = -zmax
    if "zmax" not in kwargs:
        kwargs["zmax"] = zmax
    if "color_continuous_scale" not in kwargs:
        kwargs["color_continuous_scale"] = "RdBu"

    fig = px.imshow(
        to_numpy(tensor),
        **kwargs,
    )
    fig.show()


device = t.device("cuda" if t.cuda.is_available() else "cpu")

from transformer_lens.cautils.path_patching import Node, IterNode, act_patch, path_patch
from transformer_lens.cautils.plotly_utils import imshow, hist, line
from transformer_lens.cautils.ioi_dataset import NAMES, IOIDataset, generate_data_and_caches

def get_webtext(seed: int = 420) -> List[str]:
    """Get 10,000 sentences from the OpenWebText dataset"""

    # Let's see some WEBTEXT
    raw_dataset = load_dataset("stas/openwebtext-10k")
    train_dataset = raw_dataset["train"]
    dataset = [train_dataset[i]["text"] for i in range(len(train_dataset))]

    # Shuffle the dataset (I don't want the Hitler thing being first so use a seeded shuffle)
    np.random.seed(seed)
    np.random.shuffle(dataset)

    return dataset

def lock_attn(
    attn_patterns: Float[t.Tensor, "batch head_idx dest_pos src_pos"],
    hook: HookPoint,
    ablate: bool = False,
) -> Float[t.Tensor, "batch head_idx dest_pos src_pos"]:
    """Hook to lock the attention patterns to the identity matrix"""

    assert isinstance(attn_patterns, Float[t.Tensor, "batch head_idx dest_pos src_pos"])
    assert hook.layer() == 0

    batch, n_heads, seq_len = attn_patterns.shape[:3]
    attn_new = einops.repeat(t.eye(seq_len), "dest src -> batch head_idx dest src", batch=batch, head_idx=n_heads).clone().to(attn_patterns.device)
    if ablate:
        attn_new = attn_new * 0
    return attn_new
