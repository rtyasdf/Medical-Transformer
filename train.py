# Code for MedT

import lib
import argparse
import torch
import torchvision
from torch import nn
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.utils import save_image
import torch.nn.functional as F
import os
import matplotlib.pyplot as plt
import torch.utils.data as data
from PIL import Image
import numpy as np
from torchvision.utils import save_image
import torch.nn.init as init
from utils import JointTransform2D, ImageToImage2D, Image2D
from metrics import jaccard_index, f1_score, LogNLLLoss, classwise_f1
from utils import chk_mkdir, Logger, MetricList
import cv2
from functools import partial
from random import randint
import timeit

parser = argparse.ArgumentParser(description='MedT')
parser.add_argument('-j', '--workers', default=16, type=int, metavar='N',
                    help='number of data loading workers (default: 8)')
parser.add_argument('--epochs', default=400, type=int, metavar='N',
                    help='number of total epochs to run(default: 400)')
parser.add_argument('--start-epoch', default=0, type=int, metavar='N',
                    help='manual epoch number (useful on restarts)')
parser.add_argument('-b', '--batch_size', default=1, type=int,
                    metavar='N', help='batch size (default: 1)')
parser.add_argument('--learning_rate', default=1e-3, type=float,
                    metavar='LR', help='initial learning rate (default: 0.001)')
parser.add_argument('--momentum', default=0.9, type=float, metavar='M',
                    help='momentum')
parser.add_argument('--weight-decay', '--wd', default=1e-5, type=float,
                    metavar='W', help='weight decay (default: 1e-5)')
parser.add_argument('--train_dataset', required=True, type=str)
parser.add_argument('--val_dataset', type=str)
parser.add_argument('--save_freq', type=int, default = 10)
parser.add_argument('--cuda', default="on", type=str, 
                    help='switch on/off cuda option (default: off)')
parser.add_argument('--aug', default='off', type=str,
                    help='turn on img augmentation (default: False)')
parser.add_argument('--load', default='default', type=str,
                    help='load a pretrained model')
parser.add_argument('--save', default='default', type=str,
                    help='save the model')
parser.add_argument('--direc', default='./medt', type=str,
                    help='directory to save')
parser.add_argument('--crop', default=None, type=int)
parser.add_argument('--imgsize', default=None, type=int)
parser.add_argument('--device', default='cuda', type=str)
parser.add_argument('--gray', default='no', type=str)

args = parser.parse_args()
gray_ = args.gray
aug = args.aug
direc = args.direc
modelname = args.modelname
imgsize = args.imgsize

if gray_ == "yes":
    from utils_gray import JointTransform2D, ImageToImage2D, Image2D
    imgchant = 1
else:
    from utils import JointTransform2D, ImageToImage2D, Image2D
    imgchant = 3

if args.crop is not None:
    crop = (args.crop, args.crop)
else:
    crop = None

tf_train = JointTransform2D(crop=crop, p_flip=0.5, color_jitter_params=None, long_mask=True)
tf_val = JointTransform2D(crop=crop, p_flip=0, color_jitter_params=None, long_mask=True)

train_dataset = ImageToImage2D(args.train_dataset, tf_val)
val_dataset = ImageToImage2D(args.val_dataset, tf_val)

predict_dataset = Image2D(args.val_dataset)

dataloader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=2)
valloader = DataLoader(val_dataset, 1, shuffle=True)


model = lib.models.axialnet.MedT(img_size=imgsize, imgchan=imgchant, groups=4)
device = torch.device("cuda")

if torch.cuda.device_count() > 1:
  print("Let's use", torch.cuda.device_count(), "GPUs!")
  # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
  model = nn.DataParallel(model, device_ids=[0, 1]).cuda()
model.to(device)
print(f"After only defining the model {torch.cuda.memory_allocated()} of GPU is occupied")
criterion = lib.criterions.iou_approximation # LogNLLLoss()
optimizer = torch.optim.Adam(list(model.parameters()), lr=args.learning_rate,
                             weight_decay=1e-5)
softmax = nn.Softmax(dim=1)

pytorch_total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print("Total_params: {}".format(pytorch_total_params))

seed = 3000
np.random.seed(seed)
torch.manual_seed(seed)

torch.cuda.manual_seed(seed)

# torch.set_deterministic(True)
# random.seed(seed)

train_loss = []
validate_loss = []
for epoch in range(args.epochs):

    epoch_running_loss = 0
    
    for batch_idx, (X_batch, y_batch, rest) in enumerate(dataloader):
        
        X_batch = Variable(X_batch.to(device='cuda')) # cuda
        y_batch = Variable(y_batch.to(device='cuda')) # cuda

        # ===================forward=====================
        output = model(X_batch)
        if criterion is not LogNLLLoss:
            output = softmax(output)[:, 1, :, :]

        # ===================backward====================
        loss = criterion(output, y_batch)
        loss.backward()

        if (batch_idx + 1) % 5 == 0:
            optimizer.step()
            optimizer.zero_grad()
            print(f"Batch #{batch_idx + 1}")
            
        epoch_running_loss += loss.item()
        
        if (batch_idx + 1) % 20 == 0:
            print("Train Loss = {:.4f}".format(epoch_running_loss/(batch_idx + 1)))
            with open(direc + "train_loss.txt", 'a') as tl:
                tl.write(str(epoch_running_loss/(batch_idx + 1)))
                tl.write("\n")
            fulldir = direc + "{}/".format(epoch)
            if not os.path.isdir(fulldir):
                os.makedirs(fulldir)
            
            fulldir = direc + "{}/{}/".format(epoch, batch_idx + 1)
            if not os.path.isdir(fulldir):
                os.makedirs(fulldir)
            
            torch.save(model.state_dict(), fulldir + args.modelname + ".pth")
        
    # ===================log========================
    print('epoch [{}/{}], loss:{:.4f}'
          .format(epoch, args.epochs, epoch_running_loss/(batch_idx+1)))
    train_loss.append(epoch_running_loss/(batch_idx+1))
    del X_batch, y_batch, output
    
    for param in model.parameters():
        param.requires_grad = True

    if (epoch % args.save_freq) == 0:

        validate_loss.append(0)
        for batch_idx, (X_batch, y_batch, rest) in enumerate(valloader):
            if isinstance(rest[0], str):
                        image_filename = rest[0]
            else:
                        image_filename = '%s.png' % str(batch_idx + 1).zfill(3)

            X_batch = Variable(X_batch.to(device='cuda')) # cuda
            y_batch = Variable(y_batch.to(device='cuda')) # cuda
            with torch.no_grad():
                y_out = model(X_batch)
                if criterion is not LogNLLLoss:
                    y_out = softmax(y_out)
                    loss = criterion(y_out[:, 1, :, :], y_batch)
                else:
                    loss = criterion(y_out, y_batch)
                validate_loss[-1] += loss.item()
                if criterion is LogNLLLoss:
                    y_out = softmax(y_out)

            tmp2 = y_batch.detach().cpu().numpy()
            tmp = y_out.detach().cpu().numpy()

            tmp[tmp >= 0.5] = 1
            tmp[tmp < 0.5] = 0
            tmp2[tmp2 > 0] = 1
            tmp2[tmp2 <= 0] = 0

            tmp2 = tmp2.astype(int)
            tmp = tmp.astype(int)

            yHaT = tmp
            yval = tmp2

            epsilon = 1e-20
            
            
            del X_batch, y_batch, tmp, tmp2, y_out

            yHaT[yHaT == 1] = 255
            yval[yval == 1] = 255
            fulldir = direc + "{}/".format(epoch)
            if not os.path.isdir(fulldir):
                os.makedirs(fulldir)
            
            cv2.imwrite(fulldir + image_filename, yHaT[0, 1, :, :])

        fulldir = direc + "/{}/".format(epoch)
        torch.save(model.state_dict(), fulldir + args.modelname + ".pth")
        torch.save(model.state_dict(), direc + "final_model.pth")
        validate_loss[-1] /= batch_idx
        print("Validation loss = {:.4f}".format(validate_loss[-1]))
        with open(direc + "validate_loss.txt", 'a') as vl:
            vl.write(str(validate_loss[-1]))
            vl.write("\n")
