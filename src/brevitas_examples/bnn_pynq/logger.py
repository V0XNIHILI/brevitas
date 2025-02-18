# Copyright (C) 2023, Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause


import logging
import sys
import os


class AverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


class TrainingEpochMeters(object):
    def __init__(self):
        self.batch_time = AverageMeter()
        self.data_time = AverageMeter()
        self.losses = AverageMeter()
        self.top1 = AverageMeter()
        self.top5 = AverageMeter()


class EvalEpochMeters(object):
    def __init__(self):
        self.model_time = AverageMeter()
        self.loss_time = AverageMeter()
        self.losses = AverageMeter()
        self.top1 = AverageMeter()
        self.top5 = AverageMeter()


class Logger(object):

    def __init__(self, output_dir_path, dry_run):
        self.output_dir_path = output_dir_path
        self.log = logging.getLogger('log')
        self.log.setLevel(logging.INFO)

        # Stout logging
        out_hdlr = logging.StreamHandler(sys.stdout)
        out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        out_hdlr.setLevel(logging.INFO)
        self.log.addHandler(out_hdlr)

        # Txt logging
        if not dry_run:
            file_hdlr = logging.FileHandler(os.path.join(self.output_dir_path, 'log.txt'))
            file_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
            file_hdlr.setLevel(logging.INFO)
            self.log.addHandler(file_hdlr)
            self.log.propagate = False

    def info(self, arg):
        self.log.info(arg)

    def eval_batch_cli_log(self, epoch_meters, batch, tot_batches):
        self.info('Test: [{0}/{1}]\t'
                  'Model Time {model_time.val:.3f} ({model_time.avg:.3f})\t'
                  'Loss Time {loss_time.val:.3f} ({loss_time.avg:.3f})\t'
                  'Loss {loss.val:.4f} ({loss.avg:.4f})\t'
                  'Prec@1 {top1.val:.3f} ({top1.avg:.3f})\t'
                  'Prec@5 {top5.val:.3f} ({top5.avg:.3f})\t'
                  .format(batch, tot_batches,
                          model_time=epoch_meters.model_time,
                          loss_time=epoch_meters.loss_time,
                          loss=epoch_meters.losses,
                          top1=epoch_meters.top1,
                          top5=epoch_meters.top5))

    def training_batch_cli_log(self, epoch_meters, epoch, batch, tot_batches):
        self.info('Epoch: [{0}][{1}/{2}]\t'
                         'Time {batch_time.val:.3f} ({batch_time.avg:.3f})\t'
                         'Data {data_time.val:.3f} ({data_time.avg:.3f})\t'
                         'Loss {loss.val:.4f} ({loss.avg:.4f})\t'
                         'Prec@1 {top1.val:.3f} ({top1.avg:.3f})\t'
                         'Prec@5 {top5.val:.3f} ({top5.avg:.3f})\t'
                         .format(epoch, batch, tot_batches,
                                 batch_time=epoch_meters.batch_time,
                                 data_time=epoch_meters.data_time,
                                 loss=epoch_meters.losses,
                                 top1=epoch_meters.top1,
                                 top5=epoch_meters.top5))
