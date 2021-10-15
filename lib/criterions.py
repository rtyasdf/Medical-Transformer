import torch

def iou_approximation(output: torch.Tensor, ground_true: torch.Tensor):
    I = torch.sum(output * ground_true)
    U = torch.sum(output) + torch.sum(ground_true) - I
    return 1 - I / U

def dice(output: torch.Tensor, ground_true: torch.Tensor):
    s1 = torch.sum(output)
    s2 = torch.sum(ground_true)
    product = torch.sum(output * ground_true)
    return - 2 * product / (s1 + s2)
