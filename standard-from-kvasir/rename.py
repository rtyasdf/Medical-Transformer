import os
from pathlib import Path
import shutil
import matplotlib.pyplot as plt

if __name__ == "__main__":
    im_or = "./images_original"
    im_ch = "./images_changed"
    p_io = Path(im_or)
    p_ic = Path(im_ch)
    
    m_or = "./masks_original"
    m_ch = "./masks_changed"
    p_mo = Path(m_or)
    p_mc = Path(m_ch)
    
    for i,x in enumerate(p_io.iterdir()):
        im_name = str(x).split('/')[-1]
        
        old_im = im_or + '/' + im_name
        old_mask = m_or + '/' + im_name
        
        im = plt.imread(old_im)
        mask = plt.imread(old_mask)

        new_im = im_ch + '/' + "{:04d}".format(i + 1) + ".png"        
        new_mask = m_ch + '/' + "{:04d}".format(i + 1) + ".png"
        
        plt.imsave(new_im, im)
        plt.imsave(new_mask, mask)
        
        #shutil.copy(old_im, new_im)
        #shutil.copy(old_mask, new_mask)
