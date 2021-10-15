import matplotlib.pyplot as plt
import shutil
import numpy as np
import cv2 as cv

def clip_row(im):
 
    a, b = 0, im.shape[0] - 1
    while (b - a + 1) > 512 and im[a,:,0] @ np.ones(im.shape[1]) < 10:
        a += 1
    
    while (b - a + 1) > 512 and im[b,:,0] @ np.ones(im.shape[1]) < 10:
        b -= 1
        
    while (b - a + 1) > 512:
        a += 1
        if (b - a + 1) > 512:
            b -= 1
            
    return a, b
 
 
def clip_col(im):
 
    a, b = 0, im.shape[1] - 1
    while (b - a + 1) > 512 and im[:,a,0] @ np.ones(im.shape[0]) < 10:
        a += 1
    
    while (b - a + 1) > 512 and im[:,b,0] @ np.ones(im.shape[0]) < 10:
        b -= 1
        
    while (b - a + 1) > 512:
        a += 1
        if (b - a + 1) > 512:
            b -= 1
            
    return a, b
 
 

def process_all(im, mask):
    
    if mask.shape[0] > 1000:
        im = cv.pyrDown(im)
        mask = cv.pyrDown(mask)
        
    dx = 512 - mask.shape[0]
    if dx < 0:
        a, b = clip_row(mask)
        im = im[a:b+1]
        mask = mask[a:b+1]
    else:
        im = np.append(im, np.flip(im[-dx:], axis=0), axis=0)
        mask = np.append(mask, np.flip(mask[-dx:], axis=0), axis=0)
        
    dy = 512 - mask.shape[1]
    if dy < 0:
        c, d = clip_col(mask)
        im = im[:, c:d+1]
        mask = mask[:, c:d+1]
    else:
        im = np.append(im, np.flip(im[:, -dy:], axis=1), axis=1)
        mask = np.append(mask, np.flip(mask[:, -dy:], axis=1), axis=1)
        
    return im, mask    
    
if __name__ == "__main__":
    
    old_im = "./images_changed"
    old_mask = "./masks_changed"
    
    new_im = "./images_512"
    new_mask = "./masks_512"
    
    for i in range(1000):
        suffix = '/{:04d}.png'.format(i+1)
        M = plt.imread(old_mask + suffix)
        I = plt.imread(old_im + suffix)
        
        I, M = process_all(I, M)
        plt.imsave(new_mask + suffix, M)
        plt.imsave(new_im + suffix, I)
