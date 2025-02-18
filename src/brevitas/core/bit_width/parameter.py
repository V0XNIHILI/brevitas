# Copyright (C) 2023, Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause


from typing import Optional

import torch
from torch import Tensor
from torch.nn import Parameter, Module

import brevitas
import brevitas.config as config
from brevitas.function import abs_binary_sign_grad
from brevitas.core.function_wrapper import RoundSte
from brevitas.core.restrict_val import IntRestrictValue


MIN_INT_BIT_WIDTH = 2
NON_ZERO_EPSILON = 1e-6
REMOVE_ZERO_BIT_WIDTH = 0.1


class BitWidthParameter(brevitas.jit.ScriptModule):
    """
    ScriptModule that returns a learnable bit-width wrapped in a float torch.Tensor.

    Args:
        bit_width (int): value to initialize the output learned bit-width.
        min_bit_width (int): lower bound for the output learned bit-width. Default: 2.
        restrict_bit_width_impl: restrict the learned bit-width to a subset of values. Default: IntRestrictValue(RoundSte()).
        override_pretrained_bit_width (bool): ignore pretrained bit-width loaded from a state dict. Default: False.

    Returns:
        Tensor: bit-width wrapped in a float torch.tensor and backend by a learnable torch.nn.Parameter.

    Raises:
        RuntimeError: if bit_width < min_bit_width.

    Examples:
        >>> bit_width_parameter = BitWidthParameter(8)
        >>> bit_width_parameter()
        tensor(8., grad_fn=<RoundSteFnBackward>)

    Note:
        Set env variable BREVITAS_IGNORE_MISSING_KEYS=1 to avoid errors when retraining
        from a floating point state dict.

    Note:
        Maps to bit_width_impl_type == BitWidthImplType.PARAMETER == 'PARAMETER' == 'parameter' in higher-level APIs.
    """
    __constants__ = ['bit_width_base', 'override_pretrained']

    def __init__(
            self,
            bit_width: int,
            min_bit_width: int = MIN_INT_BIT_WIDTH,
            restrict_bit_width_impl: Module = IntRestrictValue(RoundSte()),
            override_pretrained_bit_width: bool = False) -> None:
        super(BitWidthParameter, self).__init__()

        if bit_width < MIN_INT_BIT_WIDTH:
            raise RuntimeError("Int bit width has to be at least {}, instead is {}."
                            .format(MIN_INT_BIT_WIDTH, bit_width))

        if min_bit_width < MIN_INT_BIT_WIDTH:
            raise RuntimeError("Min int bit width has to be at least {}, instead is {}."
                            .format(MIN_INT_BIT_WIDTH, min_bit_width))

        if bit_width < min_bit_width:
            raise RuntimeError("Int bit width has to be at least {}, instead is {}."
                            .format(min_bit_width, bit_width))

        bit_width = float(int(bit_width))
        min_bit_width = float(int(min_bit_width))
        bit_width_base = restrict_bit_width_impl.restrict_init_float(min_bit_width)
        bit_width = restrict_bit_width_impl.restrict_init_float(bit_width)
        bit_width_offset_init = bit_width - bit_width_base
        self.bit_width_offset = Parameter(torch.tensor(bit_width_offset_init))
        self.bit_width_base = bit_width_base
        self.restrict_bit_width_impl = restrict_bit_width_impl
        self.override_pretrained = override_pretrained_bit_width

    @brevitas.jit.script_method
    def forward(self) -> Tensor:
        bit_width = abs_binary_sign_grad(self.bit_width_offset) + self.bit_width_base
        bit_width = self.restrict_bit_width_impl(bit_width)
        return bit_width

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict,
                              missing_keys, unexpected_keys, error_msgs):
        bit_width_offset_key = prefix + 'bit_width_offset'
        if self.override_pretrained and bit_width_offset_key in state_dict:
            del state_dict[bit_width_offset_key]
        super(BitWidthParameter, self)._load_from_state_dict(
            state_dict, prefix, local_metadata,strict,missing_keys, unexpected_keys, error_msgs)
        if config.IGNORE_MISSING_KEYS and bit_width_offset_key in missing_keys:
            missing_keys.remove(bit_width_offset_key)


class RemoveBitwidthParameter(brevitas.jit.ScriptModule):
    __constants__ = ['non_zero_epsilon', 'override_pretrained']

    def __init__(
            self,
            bit_width_to_remove: int,
            override_pretrained_bit_width: bool = False,
            non_zero_epsilon: float = NON_ZERO_EPSILON,
            remove_zero_bit_width = REMOVE_ZERO_BIT_WIDTH):
        super(RemoveBitwidthParameter, self).__init__()

        if bit_width_to_remove < 0:
            raise RuntimeError("Bit width to clamp has to be >= 0.".format(bit_width_to_remove))
        elif bit_width_to_remove == 0:
            bit_width_coeff_init = 1 / remove_zero_bit_width
        else:
            bit_width_coeff_init = 1 / bit_width_to_remove
        self.bit_width_coeff = Parameter(torch.tensor(bit_width_coeff_init))
        self.non_zero_epsilon = non_zero_epsilon
        self.override_pretrained = override_pretrained_bit_width

    @brevitas.jit.script_method
    def forward(self) -> Tensor:
        bit_width_to_remove = 1.0 / (self.non_zero_epsilon + torch.abs(self.bit_width_coeff))
        return bit_width_to_remove

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict,
                              missing_keys, unexpected_keys, error_msgs):
        bit_width_coeff_key = prefix + 'bit_width_coeff'
        if self.override_pretrained and bit_width_coeff_key in state_dict:
            del state_dict[bit_width_coeff_key]
        super(RemoveBitwidthParameter, self)._load_from_state_dict(
            state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)
        if config.IGNORE_MISSING_KEYS and bit_width_coeff_key in missing_keys:
            missing_keys.remove(bit_width_coeff_key)





